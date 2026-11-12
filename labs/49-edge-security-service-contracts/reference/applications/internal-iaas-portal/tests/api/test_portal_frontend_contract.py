from contextlib import ExitStack
from dataclasses import replace
from pathlib import Path
from urllib.parse import urlsplit

import httpx
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from approval_api.config import Settings as ApprovalSettings
from approval_api.main import create_app as approval_app
from grant_api.config import Settings as GrantSettings
from grant_api.main import create_app as grant_app
from request_api.config import Settings
from request_api.main import create_app
from request_api.models import AccessRequest, ResourceProjection
from request_api.portal import PortalUsage
from terraform_runner.config import Settings as RunnerSettings
from terraform_runner.executor import Executor


def identity(user="alice", tenant="tenant-a", role="CUSTOMER_USER", scopes="cloud:read cloud:request manufacturing:read"):
    return {"X-Dev-User": user, "X-Dev-Tenant": tenant, "X-Dev-Roles": f"user,{role}", "X-Dev-Scopes": scopes}


ADMIN = identity("operator", "msp", "MSP_ADMIN", "admin:read approval:manage terraform:read audit:read")
SERVICE = {"X-Dev-User": "local-test-service", "X-Dev-Roles": "service"}


def payload(**changes):
    return {"project": "synthetic-app", "blueprint_id": "VM_APPLICATION_STACK", "environment": "DEV",
            "size": "SMALL", "duration_hours": 24, "purpose": "synthetic non-production testing", **changes}


@pytest.fixture
def integrated(tmp_path, monkeypatch):
    request_settings = Settings(database_url=f"sqlite+pysqlite:///{(tmp_path/'request.db').as_posix()}",
        auto_create_schema=True, auth_mode="dev", approval_api_url="http://approval.local",
        grant_api_url="http://grant.local", enable_local_llm_simulator=True,
        monitoring_assistant_provider="local")
    apps = {
        "request.local": create_app(request_settings),
        "approval.local": approval_app(ApprovalSettings(database_url=f"sqlite+pysqlite:///{(tmp_path/'approval.db').as_posix()}",
            auto_create_schema=True, auth_mode="dev", request_api_url="http://request.local",
            grant_api_url="http://grant.local", enable_provisioning_jobs=True)),
        "grant.local": grant_app(GrantSettings(database_url=f"sqlite+pysqlite:///{(tmp_path/'grant.db').as_posix()}",
            auto_create_schema=True, auth_mode="dev", request_api_url="http://request.local",
            approval_api_url="http://approval.local", grant_signing_key="synthetic-test-key-with-at-least-32-bytes",
            grant_signing_algorithm="HS256")),
    }
    with ExitStack() as stack:
        clients = {name: stack.enter_context(TestClient(app)) for name, app in apps.items()}

        def post(url, **kwargs):
            parsed=urlsplit(url)
            assert parsed.hostname in clients, "test attempted external network access"
            return clients[parsed.hostname].post(parsed.path, json=kwargs.get("json"), headers=kwargs.get("headers"))

        monkeypatch.setattr(httpx, "post", post)

        def transport(request):
            assert request.url.host in clients
            response=clients[request.url.host].request(request.method, request.url.path + ("?" + request.url.query.decode() if request.url.query else ""),
                content=request.content, headers=dict(request.headers))
            return httpx.Response(response.status_code, json=response.json())

        apps["request.local"].state.portal_approval_transport=httpx.MockTransport(transport)
        apps["request.local"].state.portal_grant_transport=httpx.MockTransport(transport)
        yield apps, clients, request_settings


def create(client, data=None, user=None, key="request-one", domain="manufacturing"):
    return client.post(f"/api/{domain}/requests", json=data or payload(), headers={**(user or identity()), "Idempotency-Key": key})


def test_catalog_matches_frontend_and_eight_product_authority(integrated):
    _, clients, _=integrated
    client=clients["request.local"]
    result=client.get("/api/manufacturing/workspace", headers=identity())
    assert result.status_code==200, result.text
    data=result.json()
    assert len(data["catalog"])==8
    assert [p["blueprint_id"] for p in data["catalog"] if p["requestable"]]==["VM_APPLICATION_STACK"]
    assert data["requests"]==data["resources"]==[]
    assert data["monitoring"]["alerts"] is None
    assert data["finops"]["actual_krw"] is None
    assert "provider_binding" not in str(data)


@pytest.mark.parametrize("changes", [
    {"environment":"PROD"}, {"size":"Custom"}, {"duration_hours":123},
    {"project":"../../escape"}, {"provider":"AWS"}, {"configuration":{"raw_hcl":"anything"}},
    {"blueprint_id":"API_DEVELOPMENT_STACK"}, {"purpose":" secret\ncontent"},
])
def test_nonproduction_and_template_boundaries(integrated, changes):
    apps, clients, _=integrated
    response=create(clients["request.local"], payload(**changes))
    assert response.status_code in {409,422}, response.text
    with apps["request.local"].state.session_factory() as db:
        assert list(db.scalars(select(AccessRequest)))==[]


def test_persistent_tenant_domain_and_idempotency_isolation(integrated):
    apps, clients, settings=integrated
    client=clients["request.local"]
    first=create(client).json()
    assert first["delivery_status"]=="DELIVERED"
    assert create(client).json()["id"]==first["id"]
    assert create(client, payload(project="different-project")).status_code==409
    assert create(client, payload(purpose="different approved purpose")).status_code==409
    assert client.get("/api/manufacturing/requests", headers=identity(tenant="tenant-b")).json()["items"]==[]
    assert client.get("/api/finance/requests", headers=identity(role="CUSTOMER_MANAGER",scopes="cloud:read cloud:request finance:read")).json()["items"]==[]
    assert client.get(f'/api/v1/requests/{first["id"]}', headers=identity(tenant="tenant-b")).status_code==404
    assert client.get('/api/v1/requests', headers=identity(tenant="tenant-b")).json()==[]
    assert client.post(f'/api/manufacturing/requests/{first["id"]}/cancel', headers=identity(tenant="tenant-b")).status_code==404
    with TestClient(create_app(settings)) as restarted:
        assert restarted.get('/api/manufacturing/requests', headers=identity()).json()["items"][0]["id"]==first["id"]
    # Preserve the catalog per-user quota, then prove keys do not collide across tenants.
    assert client.post(f'/api/manufacturing/requests/{first["id"]}/cancel', headers=identity()).status_code==200
    assert create(client, user=identity(tenant="tenant-b")).json()["id"]!=first["id"]


@pytest.mark.parametrize("headers,path", [
    ({},'/api/manufacturing/workspace'),
    (identity(scopes=''),'/api/manufacturing/workspace'),
    (identity(tenant=''),'/api/manufacturing/workspace'),
    (identity(),'/api/finance/workspace'),
    (identity(),'/api/admin/workspace'),
    (identity(role='MSP_OPERATOR',scopes='audit:read'),'/api/admin/audit'),
    (identity(role='LLM_USER',scopes='llm:usage:read'),'/api/llm/models'),
])
def test_backend_role_scope_enforcement(integrated, headers, path):
    assert integrated[1]['request.local'].get(path,headers=headers).status_code in {401,403}


def run_next(clients):
    approval=clients['approval.local']
    response=approval.post('/internal/v1/provisioning/jobs/claim', headers=SERVICE, json={'runner_id':'local-test-runner'})
    assert response.status_code==200,response.text
    job=response.json()
    assert job
    reports=[]
    def report(data):
        result=approval.post(f'/internal/v1/provisioning/jobs/{job["job_id"]}/result',headers=SERVICE,json=data)
        assert result.status_code==200,result.text
        reports.append(result.json())
    Executor(RunnerSettings(runner_mode='mock',mock_delay_seconds=0)).run(job,report)
    assert reports
    return job,reports[-1]


def test_frontend_request_approval_runner_grant_recovery_roundtrip(integrated):
    apps,clients,_=integrated
    client=clients['request.local']; item=create(client).json(); rid=item['id']
    queue=client.get('/api/admin/workspace',headers=ADMIN).json()
    assert queue['approval_connection']=='CONNECTED'
    assert queue['requests'][0]['approval_status']=='PENDING'
    decision=client.post(f'/api/admin/requests/{rid}/approve',headers=ADMIN,json={'reason':'synthetic lab policy reviewed'})
    assert decision.status_code==200,decision.text
    job,result=run_next(clients)
    assert job['operation']=='APPLY'
    assert result['job']['status']=='SUCCEEDED'
    data=client.get('/api/manufacturing/workspace',headers=identity()).json()
    assert data['requests'][0]['status']=='GRANTED'
    assert data['resources'][0]['status']=='RUNNING'
    assert data['resources'][0]['runtime_evidence']=='NOT_VALIDATED'
    assert client.get('/api/v1/resources',headers=identity(tenant='tenant-b')).json()==[]
    assert client.get('/api/v1/resources/'+data['resources'][0]['id'],headers=identity(tenant='tenant-b')).status_code==404
    recovered=client.post(f'/api/manufacturing/requests/{rid}/destroy',headers=identity(),json={'reason':'synthetic lab cleanup requested'})
    assert recovered.status_code==202,recovered.text
    # Access revocation precedes infrastructure deletion.
    assert client.get('/api/manufacturing/requests',headers=identity()).json()['items'][0]['status']=='REVOKED'
    job,result=run_next(clients)
    assert job['operation']=='DESTROY'
    assert result['job']['status']=='TERMINATED'
    data=client.get('/api/manufacturing/workspace',headers=identity()).json()
    assert data['resources'][0]['status']=='TERMINATED'
    assert data['finops']['estimated_monthly_krw']==0
    assert client.get('/api/admin/audit',headers=ADMIN).json()['items']


def test_cancel_and_rejection_and_self_approval_bypass(integrated):
    _,clients,_=integrated
    client=clients['request.local'];item=create(client).json();rid=item['id']
    self_admin={**ADMIN,'X-Dev-User':'alice'}
    assert client.post(f'/api/admin/requests/{rid}/approve',headers=self_admin,json={'reason':'self approval denied'}).status_code==403
    direct={**self_admin,'X-Dev-Roles':'approver'}
    assert clients['approval.local'].post(f'/admin-api/v1/requests/{rid}/approve',headers=direct,json={'reason':'direct bypass denied'}).status_code==403
    assert client.post(f'/api/manufacturing/requests/{rid}/cancel',headers=identity()).status_code==200
    assert client.post(f'/api/admin/requests/{rid}/approve',headers=ADMIN,json={'reason':'cancelled request denied'}).status_code==409
    other=create(client,key='reject-me').json()['id']
    assert client.post(f'/api/admin/requests/{other}/reject',headers=ADMIN,json={'reason':'rejected after local review'}).status_code==200
    assert client.get('/api/manufacturing/requests',headers=identity()).json()['items'][0]['status']=='REJECTED'


def test_llm_meter_persistence_without_prompts_or_fake_tokens(integrated):
    apps,clients,settings=integrated
    client=clients['request.local'];headers=identity(role='LLM_USER',scopes='llm:invoke llm:usage:read')
    text='synthetic prompt that must never persist'
    response=client.post('/api/llm/chat',headers={**headers,'Idempotency-Key':'chat-once'},json={'model':'local-simulator','prompt':text})
    assert response.status_code==200,response.text
    assert response.json()['provider_connected'] is False
    client.post('/api/llm/chat',headers={**headers,'Idempotency-Key':'chat-once'},json={'model':'local-simulator','prompt':text})
    usage=client.get('/api/llm/usage',headers=headers).json()
    assert usage['requests']==1 and usage['tokens'] is None and usage['amount_krw'] is None
    assert client.get('/api/llm/usage',headers={**headers,'X-Dev-Tenant':'tenant-b'}).json()['requests']==0
    with apps['request.local'].state.session_factory() as db:
        assert len(list(db.scalars(select(PortalUsage))))==1
    db_path=Path(settings.database_url.split('///',1)[1])
    assert text.encode() not in db_path.read_bytes()
    with TestClient(create_app(replace(settings,enable_local_llm_simulator=False))) as disabled:
        assert disabled.post('/api/llm/chat',headers={**headers,'Idempotency-Key':'disabled'},json={'model':'local-simulator','prompt':text}).status_code==503
        assert disabled.get('/api/llm/usage',headers=headers).json()['requests']==1


def test_monitoring_assistant_is_metric_only_advisory_and_scope_bound(integrated):
    apps,clients,settings=integrated
    client=clients['request.local']
    headers=identity(role='LLM_USER',scopes='llm:invoke llm:usage:read monitoring:assist')
    status=client.get('/api/llm/monitoring-assistant',headers=headers)
    assert status.status_code==200 and status.json()['status']=='LOCAL_SIMULATED'
    signal={'analysis_goal':'TRIAGE_SUMMARY','signals':[{
        'signal_id':'synthetic-cpu-001','observed_at':'2026-10-02T00:00:00Z',
        'source':'SYNTHETIC_TEST','metric_name':'service_cpu_utilization',
        'current_value':82,'baseline_value':45,'anomaly_score':0.86,'state':'WARNING'}]}
    response=client.post('/api/llm/monitoring-assistant/analyze',headers={**headers,'Idempotency-Key':'assist-one'},json=signal)
    assert response.status_code==200,response.text
    result=response.json()
    assert result['source']=='LOCAL_DETERMINISTIC_ASSISTANT'
    assert result['authoritative'] is False and result['action_authorized'] is False
    assert result['human_review_required'] is True and result['provider_connected'] is False
    assert client.post('/api/llm/monitoring-assistant/analyze',headers={**headers,'Idempotency-Key':'assist-one'},json=signal).status_code==409
    assert client.post('/api/llm/monitoring-assistant/analyze',headers={**identity(role='LLM_USER',scopes='llm:invoke'),'Idempotency-Key':'denied'},json=signal).status_code==403
    # The strict schema has no raw-log, host, address, identity, or open prompt field.
    assert client.post('/api/llm/monitoring-assistant/analyze',headers={**headers,'Idempotency-Key':'raw'},json={**signal,'raw_log':'token=secret'}).status_code==422
    db_path=Path(settings.database_url.split('///',1)[1])
    assert b'service_cpu_utilization' not in db_path.read_bytes()


def test_monitoring_assistant_fails_closed_when_provider_is_disabled(integrated):
    _,_,settings=integrated
    headers=identity(role='LLM_USER',scopes='llm:invoke monitoring:assist')
    signal={'analysis_goal':'OPERATOR_CHECKLIST','signals':[{
        'signal_id':'synthetic-memory-001','observed_at':'2026-10-02T00:00:00Z',
        'source':'PROMETHEUS','metric_name':'service_memory_utilization',
        'current_value':70,'baseline_value':55,'anomaly_score':0.61,'state':'REVIEW_REQUIRED'}]}
    with TestClient(create_app(replace(settings,monitoring_assistant_provider='disabled'))) as disabled:
        assert disabled.get('/api/llm/monitoring-assistant',headers=headers).json()['status']=='NOT_CONNECTED'
        response=disabled.post('/api/llm/monitoring-assistant/analyze',headers={**headers,'Idempotency-Key':'disabled'},json=signal)
        assert response.status_code==503


def test_oidc_ignores_forged_development_headers(tmp_path):
    app=create_app(Settings(database_url=f'sqlite+pysqlite:///{(tmp_path/"oidc.db").as_posix()}',auto_create_schema=True,auth_mode='oidc',enable_local_llm_simulator=True))
    with TestClient(app) as client:
        assert client.get('/api/portal/runtime').json()['demoAuth'] is False
        assert client.get('/api/manufacturing/workspace',headers=identity()).status_code==401
        assert client.get('/api/portal/me',headers={'Authorization':'Bearer forged-token'}).status_code==503


def test_bound_grant_revoke_does_not_accept_wrong_owner_or_user_role(integrated):
    _,clients,_=integrated
    client=clients['request.local'];rid=create(client).json()['id']
    client.post(f'/api/admin/requests/{rid}/approve',headers=ADMIN,json={'reason':'synthetic request approved'})
    run_next(clients)
    with integrated[0]['request.local'].state.session_factory() as db:
        grant_id=db.get(AccessRequest,rid).grant_id
    path=f'/internal/v1/grants/{grant_id}/revoke'
    body={'request_id':rid,'owner_id':'wrong-owner','reason':'wrong binding must fail'}
    assert clients['grant.local'].post(path,headers=SERVICE,json=body).status_code==404
    assert clients['grant.local'].post(path,headers=identity(),json={**body,'owner_id':'alice'}).status_code==403


@pytest.mark.parametrize('domain', ['developer','manufacturing','finance','public'])
def test_ecl2_domain_contract_and_scope_isolation(integrated,domain):
    client=integrated[1]['request.local']
    headers=identity(scopes=f'cloud:read cloud:request {domain}:read')
    assert client.get(f'/api/{domain}/workspace',headers=headers).status_code==200
    denied=identity(scopes='cloud:read cloud:request')
    assert client.get(f'/api/{domain}/workspace',headers=denied).status_code==403
    item=create(client,user=headers,domain=domain).json()
    assert item['domain']==domain and item['delivery_status']=='DELIVERED'
    assert client.get(f'/api/{domain}/requests/{item["id"]}',headers=headers).json()['id']==item['id']
    assert client.get(f'/api/{domain}/resources',headers=headers).json()['items']==[]
    assert client.get(f'/api/{domain}/monitoring',headers=headers).json()['source']=='NOT_CONNECTED'
    assert client.get(f'/api/{domain}/finops',headers=headers).json()['actual_krw'] is None
    for other in {'developer','manufacturing','finance','public'}-{domain}:
        other_headers=identity(scopes=f'cloud:read cloud:request {other}:read')
        assert client.get(f'/api/{other}/requests/{item["id"]}',headers=other_headers).status_code==404


def test_ecl2_user_grant_and_workspace_contracts(integrated):
    _,clients,_=integrated
    client=clients['request.local']
    admin={**ADMIN,'X-Dev-Scopes':ADMIN['X-Dev-Scopes']+' admin:write llm:invoke llm:usage:read'}
    rid=create(client).json()['id']
    observed=client.get('/api/admin/users',headers=admin).json()
    assert observed['directory_connected'] is False
    assert observed['items']==[{'user_id':'alice','tenant_id':'tenant-a','source':'OBSERVED_REQUESTER'}]
    assert client.get('/api/admin/users',headers=identity()).status_code==403
    assert client.get('/api/portal/team',headers=identity()).status_code==403
    manager=identity(role='CUSTOMER_MANAGER',scopes='cloud:read team:read')
    assert client.get('/api/portal/team',headers=manager).json()['source']=='NOT_CONNECTED'
    client.post(f'/api/admin/requests/{rid}/approve',headers=admin,json={'reason':'synthetic ecl2 integration approved'})
    run_next(clients)
    grants=client.get('/api/admin/grants',headers=admin).json()
    assert grants['items'][0]['request_id']==rid and grants['source']=='GRANT_DATABASE'
    assert 'token' not in str(grants).lower()
    assert client.get('/api/admin/grants',headers=identity()).status_code==403
    assert client.get('/api/llm/models',headers=admin).status_code==200
    assert client.post('/api/llm/workspace-requests',headers=admin,json={'size':'SMALL'}).status_code==409
    assert client.post('/api/llm/workspace-requests',headers=admin,json={'size':'LARGE'}).status_code==422


def test_delivery_disconnect_and_recovery_fail_closed(integrated):
    apps,clients,_=integrated
    from dataclasses import replace
    client=clients['request.local'];rid=create(client).json()['id']
    client.post(f'/api/admin/requests/{rid}/approve',headers=ADMIN,json={'reason':'synthetic local approval verified'})
    run_next(clients)
    # Removing the Grant binding must not enqueue a destroy that leaves access alive.
    apps['request.local'].state.settings=replace(apps['request.local'].state.settings,grant_api_url='')
    response=client.post(f'/api/manufacturing/requests/{rid}/destroy',headers=identity(),json={'reason':'recovery denied until access revocation available'})
    assert response.status_code==503
    jobs=clients['approval.local'].get('/admin-api/v1/provisioning/jobs?status=ALL',headers={'X-Dev-User':'operator','X-Dev-Roles':'approver'}).json()
    assert [j['operation'] for j in jobs]==['APPLY']
