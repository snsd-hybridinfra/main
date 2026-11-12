import json

import httpx

from request_api.monitoring_assistant import MonitoringAssistRequest, openai_advisory


def test_openai_adapter_sends_only_bounded_signal_and_disables_storage(tmp_path):
    token_file=tmp_path/'openai-token'
    token_file.write_text('synthetic-test-token',encoding='utf-8')
    captured={}

    def handler(request):
        captured['url']=str(request.url)
        captured['authorization']=request.headers.get('Authorization')
        captured['body']=json.loads(request.content)
        return httpx.Response(200,json={
            'output_text':'정제 지표를 운영자가 확인해야 합니다.',
            'usage':{'input_tokens':31,'output_tokens':12},
        })

    payload=MonitoringAssistRequest.model_validate({
        'analysis_goal':'TREND_EXPLANATION',
        'signals':[{
            'signal_id':'synthetic-latency-001','observed_at':'2026-10-02T00:00:00Z',
            'source':'OPENTELEMETRY','metric_name':'request_latency_ms',
            'current_value':190.0,'baseline_value':80.0,'anomaly_score':0.91,
            'state':'ANOMALY_DETECTED',
        }],
    })
    result=openai_advisory(payload,model='gpt-5-mini',token_file=str(token_file.resolve()),
        timeout_seconds=1,transport=httpx.MockTransport(handler))
    assert result.provider_connected is True and result.source=='OPENAI_RESPONSES_API'
    assert captured['url']=='https://api.openai.com/v1/responses'
    assert captured['authorization']=='Bearer synthetic-test-token'
    assert captured['body']['store'] is False and captured['body']['max_output_tokens']==500
    serialized=captured['body']['input']
    assert 'request_latency_ms' in serialized
    for forbidden in ('tenant','user','host','ip_address','raw_log','prompt'):
        assert forbidden not in serialized.lower()
