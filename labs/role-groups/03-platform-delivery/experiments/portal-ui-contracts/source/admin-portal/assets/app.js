const requestsEl = document.querySelector('#requests');
const syncEl = document.querySelector('#sync-status');
const grantsEl = document.querySelector('#grants');
const jobsEl = document.querySelector('#provisioning-jobs');
const monitoringEl = document.querySelector('#monitoring-dashboard');
const dialog = document.querySelector('#decision-dialog');
const detailDialog = document.querySelector('#request-detail-dialog');
const resetDemoButton = document.querySelector('#reset-demo');
const resetMessage = document.querySelector('#reset-message');
const seedDemoButton = document.querySelector('#seed-demo');
const seedMessage = document.querySelector('#seed-message');
const demoCenter = document.querySelector('#admin-demo');
const demoNav = document.querySelector('#demo-nav');
const staticPreview = window.location.protocol === 'file:';
const localDev = staticPreview || ['localhost','127.0.0.1'].includes(window.location.hostname);
let requestsById = new Map();
let resetInProgress = false;
let seedInProgress = false;
const previewRequests=[
  {request_id:'DEMO-REQ-20260812-002',idempotency_key:'demo-request-002',requester_id:'demo-user',product_code:'DEV-OS-VM-M',cpu:2,memory_gib:4,storage_gib:50,parameters:{project_name:'integration-lab',workload_purpose:'backend-integration-test'},duration_hours:8,purpose:'OpenStack 통합 테스트 VM 신청',status:'PENDING',event_version:1,retry_count:0,delivery_status:'DELIVERED',last_error:null,created_at:'2026-08-12T09:05:00+09:00',updated_at:'2026-08-12T09:05:00+09:00'},
  {request_id:'DEMO-REQ-20260729-003',idempotency_key:'demo-request-003',requester_id:'demo-user-2',product_code:'DEV-OS-VM-S',cpu:2,memory_gib:2,storage_gib:30,parameters:{project_name:'security-test',workload_purpose:'security-validation'},duration_hours:24,purpose:'보안 검증용 일시 개발 서버',status:'APPROVED',event_version:2,retry_count:1,delivery_status:'FAILED',last_error:'request-api callback 연결 시간 초과 (DEMO)',created_at:'2026-07-29T08:45:00+09:00',updated_at:'2026-07-29T08:51:00+09:00'},
  {request_id:'DEMO-REQ-20260729-001',idempotency_key:'demo-request-001',requester_id:'demo-user',product_code:'DEV-OS-VM-S',cpu:2,memory_gib:2,storage_gib:30,parameters:{project_name:'payment-api-test',workload_purpose:'saas-application-development'},duration_hours:24,purpose:'사내 SaaS 백엔드 개발 환경',status:'GRANTED',event_version:3,retry_count:0,delivery_status:'DELIVERED',last_error:null,created_at:'2026-07-29T08:20:00+09:00',updated_at:'2026-07-29T08:31:00+09:00'},
];
const previewGrants=[
  {grant_id:'DEMO-GRANT-001',request_id:'DEMO-REQ-20260729-001',idempotency_key:'demo-grant-001',subject_id:'demo-user',scopes:['resource:access'],status:'ACTIVE',issued_at:'2026-07-29T08:30:00+09:00',expires_at:'2026-07-30T08:30:00+09:00',revoked_at:null,event_version:3,retry_count:0,callback_status:'DELIVERED',last_error:null,updated_at:'2026-07-29T08:31:00+09:00'},
  {grant_id:'DEMO-GRANT-OLD',request_id:'DEMO-REQ-20260728-004',idempotency_key:'demo-grant-old',subject_id:'demo-user-3',scopes:['openstack:vm:access'],status:'EXPIRED',issued_at:'2026-07-28T09:00:00+09:00',expires_at:'2026-07-28T17:00:00+09:00',revoked_at:null,event_version:4,retry_count:0,callback_status:'DELIVERED',last_error:null,updated_at:'2026-07-28T17:01:00+09:00'},
];
const previewJobs=[
  {operation:'APPLY',product_code:'DEV-OS-VM-S',module_name:'openstack-dev-vm-small',module_version:'1.0.0',artifact_digest:'sha256:97f4…90f0',status:'SUCCEEDED',attempts:1,runner_id:'terraform-runner',last_error:null,created_at:'2026-08-12T08:27:00+09:00',updated_at:'2026-08-12T08:30:00+09:00'},
];
function headers(extra={}) { return {'X-Dev-User':document.querySelector('#dev-user').value.trim(),'X-Dev-Roles':'approver,grant-admin,auditor',...extra}; }
function esc(value) { return String(value ?? '').replace(/[&<>'"]/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch])); }
function formatDate(value){if(!value)return '-';const date=new Date(value);return Number.isNaN(date.getTime())?String(value):date.toLocaleString('ko-KR');}
function formatDuration(hours){return Number(hours)%24===0?`${Number(hours)/24}일`:`${hours}시간`;}
function formatParameters(values){const entries=Object.entries(values||{});return entries.length?entries.map(([key,value])=>`${esc(key)}: ${esc(value)}`).join(' · '):'-';}
function apiErrorMessage(body,status){const detail=body?.detail;if(typeof detail==='string')return detail;if(Array.isArray(detail))return detail.map(issue=>{const field=Array.isArray(issue?.loc)?issue.loc.filter(part=>part!=='body').join('.'):'';return `${field?`${field}: `:''}${issue?.msg||'입력값을 확인해 주세요.'}`;}).join(' / ');if(detail&&typeof detail==='object')return detail.message||JSON.stringify(detail);return `요청 처리 실패 (HTTP ${status})`;}
async function api(path, options={}) { const response=await fetch(path,{...options,headers:headers(options.headers)}); if(!response.ok){const body=await response.json().catch(()=>({}));throw new Error(apiErrorMessage(body,response.status));} return response.json(); }

async function loadRequests(){
  const items=staticPreview?previewRequests:await api('/admin-api/v1/requests?status=ALL');
  requestsById=new Map(items.map(item=>[item.request_id,item]));
  const pending=items.filter(item=>item.status==='PENDING');
  const failed=items.filter(item=>item.delivery_status==='FAILED'&&['APPROVED','REJECTED'].includes(item.status));
  document.querySelector('#pending-count').textContent=pending.length;
  document.querySelector('#sync-failed-count').textContent=failed.length;
  if(!pending.length) requestsEl.innerHTML='<p class="empty">승인 대기 신청이 없습니다.</p>';
  else requestsEl.innerHTML=`<table><thead><tr><th>사용자</th><th>상품/사양</th><th>목적</th><th>기간</th><th>작업</th></tr></thead><tbody>${pending.map(item=>`<tr>
  <td>${esc(item.requester_id)}</td><td>${esc(item.product_code)}<br>${item.cpu?`${item.cpu} vCPU / ${item.memory_gib} GiB / ${item.storage_gib} GiB`:formatParameters(item.parameters)}</td>
  <td>${esc(item.purpose)}</td><td>${formatDuration(item.duration_hours)}</td><td><button class="detail-button" data-detail="${esc(item.request_id)}">상세</button> <button data-action="approve" data-id="${esc(item.request_id)}">승인</button> <button class="reject" data-action="reject" data-id="${esc(item.request_id)}">거절</button></td></tr>`).join('')}</tbody></table>`;
  requestsEl.querySelectorAll('[data-action]').forEach(button=>button.addEventListener('click',()=>openDecision(button.dataset.id,button.dataset.action)));
  requestsEl.querySelectorAll('[data-detail]').forEach(button=>button.addEventListener('click',()=>openRequestDetail(requestsById.get(button.dataset.detail))));

  if(!items.length) syncEl.innerHTML='<p class="empty">동기화 이력이 없습니다.</p>';
  else syncEl.innerHTML=`<table><thead><tr><th>신청</th><th>상태</th><th>Callback</th><th>Event</th><th>Retry</th><th>최종 갱신</th><th>작업</th></tr></thead><tbody>${[...items].sort((a,b)=>String(b.updated_at).localeCompare(String(a.updated_at))).slice(0,50).map(item=>`<tr>
    <td><strong>${esc(item.requester_id)}</strong><br><button class="link-button" data-sync-detail="${esc(item.request_id)}">${esc(item.product_code)} 상세 보기</button></td><td><span class="status ${esc(item.status)}">${esc(item.status)}</span></td>
    <td><span class="delivery ${esc(item.delivery_status)}">${esc(item.delivery_status)}</span>${item.last_error?`<small class="inline-error" title="${esc(item.last_error)}">오류 있음</small>`:''}</td><td>v${item.event_version}</td><td>${item.retry_count}회</td><td>${esc(formatDate(item.updated_at))}</td>
    <td>${item.delivery_status==='FAILED'&&['APPROVED','REJECTED'].includes(item.status)?`<button data-retry="${esc(item.request_id)}">동기화 재시도</button>`:'-'}</td></tr>`).join('')}</tbody></table>`;
  syncEl.querySelectorAll('[data-sync-detail]').forEach(button=>button.addEventListener('click',()=>openRequestDetail(requestsById.get(button.dataset.syncDetail))));
  syncEl.querySelectorAll('[data-retry]').forEach(button=>button.addEventListener('click',()=>retrySync(button.dataset.retry,button)));
}

async function loadGrants(){
  const items=staticPreview?previewGrants:await api('/admin-api/v1/grants?status=ALL');
  document.querySelector('#active-grant-count').textContent=items.filter(item=>item.status==='ACTIVE').length;
  if(!items.length){grantsEl.innerHTML='<p class="empty">Grant 이력이 없습니다.</p>';return;}
  grantsEl.innerHTML=`<table><thead><tr><th>사용자</th><th>Scope</th><th>발급</th><th>만료</th><th>상태</th><th>작업</th></tr></thead><tbody>${items.map(item=>`<tr>
  <td>${esc(item.subject_id)}</td><td>${esc(item.scopes.join(', '))}</td><td>${esc(formatDate(item.issued_at))}</td><td>${esc(formatDate(item.expires_at))}</td><td><span class="status ${esc(item.status)}">${esc(item.status)}</span></td>
  <td>${item.status==='ACTIVE'?`<button class="revoke" data-revoke="${esc(item.grant_id)}">회수</button>${localDev?` <button class="expire-now" data-expire="${esc(item.grant_id)}">즉시 만료</button>`:''}`:'-'}</td></tr>`).join('')}</tbody></table>`;
  grantsEl.querySelectorAll('[data-revoke]').forEach(button=>button.addEventListener('click',async()=>{if(staticPreview){alert('정적 미리보기의 샘플 Grant는 변경되지 않습니다. API 실행 후 실제 회수 흐름을 검증하세요.');return;}if(!confirm('이 Grant를 회수할까요?'))return;try{await api(`/admin-api/v1/grants/${button.dataset.revoke}/revoke`,{method:'POST'});await refreshAll();}catch(error){alert(error.message);}}));
  grantsEl.querySelectorAll('[data-expire]').forEach(button=>button.addEventListener('click',async()=>{if(staticPreview){alert('즉시 만료는 Compose로 실행한 로컬 데모에서 동작합니다.');return;}if(!confirm('이 Grant를 지금 만료시킬까요? 연결된 모의 자원도 자동 종료됩니다.'))return;try{await api(`/admin-api/v1/grants/${button.dataset.expire}/expire-now`,{method:'POST'});await refreshAll();}catch(error){alert(error.message);}}));
}

async function loadProvisioningJobs(){
  const items=staticPreview?previewJobs:await api('/admin-api/v1/provisioning/jobs?status=ALL');
  document.querySelector('#provisioning-active-count').textContent=items.filter(item=>['QUEUED','PLANNING','APPLYING','DESTROYING'].includes(item.status)).length;
  if(!items.length){jobsEl.innerHTML='<p class="empty">Terraform 작업 이력이 없습니다.</p>';return;}
  jobsEl.innerHTML=`<table><thead><tr><th>작업</th><th>상품</th><th>승인 모듈</th><th>상태</th><th>시도</th><th>Runner</th><th>최종 갱신</th><th>작업</th></tr></thead><tbody>${items.map(item=>`<tr>
    <td>${esc(item.operation)}</td><td>${esc(item.product_code)}</td><td>${esc(item.module_name)} v${esc(item.module_version)}<br><small title="${esc(item.artifact_digest||'')}">${esc(item.artifact_digest||'').slice(0,18)}${item.artifact_digest?.length>18?'…':''}</small></td><td><span class="status ${esc(item.status)}">${esc(item.status)}</span>${item.last_error?`<small class="inline-error" title="${esc(item.last_error)}">오류 있음</small>`:''}</td><td>${item.attempts}회</td><td>${esc(item.runner_id||'-')}</td><td>${esc(formatDate(item.updated_at))}</td><td>${['PLANNING','APPLYING','DESTROYING','PLAN_FAILED','POLICY_DENIED','APPLY_FAILED','BOOTSTRAP_FAILED','DESTROY_FAILED','CALLBACK_FAILED','GRANT_FAILED'].includes(item.status)?`<button data-job-retry="${esc(item.job_id)}">재시도</button>`:'-'}</td>
  </tr>`).join('')}</tbody></table>`;
  jobsEl.querySelectorAll('[data-job-retry]').forEach(button=>button.addEventListener('click',async()=>{if(staticPreview){alert('실제 API 실행 환경에서 재시도할 수 있습니다.');return;}if(!confirm('이 Terraform 작업을 같은 승인 입력과 State로 다시 실행할까요?'))return;try{await api(`/admin-api/v1/provisioning/jobs/${button.dataset.jobRetry}/retry`,{method:'POST'});await refreshAll();}catch(error){alert(error.message);}}));
}

async function loadMonitoring(){
  const config=staticPreview?{provider:'grafana',status:'PENDING',dashboard_url:null}:await api('/admin-api/v1/monitoring-dashboard');
  const stateEl=document.querySelector('#monitoring-state');
  const dashboardUrl=String(config.dashboard_url||'');
  const validUrl=(dashboardUrl.startsWith('/')&&!dashboardUrl.startsWith('//'))||/^https?:\/\//i.test(dashboardUrl);
  monitoringEl.replaceChildren();
  if(config.status==='READY'&&validUrl){
    stateEl.textContent='연결됨';stateEl.className='connected';
    const frame=document.createElement('iframe');frame.className='grafana-frame';frame.title='Grafana 운영 모니터링 대시보드';frame.src=dashboardUrl;frame.loading='lazy';frame.referrerPolicy='no-referrer';
    const link=document.createElement('a');link.className='grafana-link';link.href=dashboardUrl;link.target='_blank';link.rel='noopener noreferrer';link.textContent='Grafana에서 크게 보기';
    monitoringEl.append(frame,link);
    return;
  }
  stateEl.textContent=config.status==='INVALID'?'설정 오류':'연동 대기';stateEl.className=config.status==='INVALID'?'invalid':'pending';
  monitoringEl.innerHTML=config.status==='INVALID'
    ?'<p class="error">Grafana 대시보드 주소가 올바르지 않습니다. HTTP(S) 또는 동일 출처 경로를 설정하세요.</p>'
    :'<div class="monitoring-placeholder"><strong>Grafana 연동 대기</strong><p>대시보드가 완성되면 <code>GRAFANA_DASHBOARD_URL</code> 설정만으로 이 영역에 자동 표시됩니다.</p></div>';
}

function openDecision(id,action){document.querySelector('#decision-request-id').value=id;document.querySelector('#decision-action').value=action;document.querySelector('#decision-title').textContent=action==='approve'?'신청 승인':'신청 거절';document.querySelector('#decision-reason').value='';dialog.showModal();}
function openRequestDetail(item){if(!item)return;const spec=item.cpu?`${item.cpu} vCPU / ${item.memory_gib} GiB / ${item.storage_gib} GiB`:'권한 상품';document.querySelector('#request-detail-content').innerHTML=`<dl class="detail-grid">
  <div><dt>사용자</dt><dd>${esc(item.requester_id)}</dd></div><div><dt>상품</dt><dd>${esc(item.product_code)}</dd></div><div><dt>사양</dt><dd>${esc(spec)}</dd></div>
  <div class="wide"><dt>상품 옵션</dt><dd>${formatParameters(item.parameters)}</dd></div>
  <div><dt>사용기간</dt><dd>${formatDuration(item.duration_hours)}</dd></div><div><dt>현재 상태</dt><dd><span class="status ${esc(item.status)}">${esc(item.status)}</span></dd></div><div class="wide"><dt>사용 목적</dt><dd>${esc(item.purpose)}</dd></div>
  <div><dt>Callback</dt><dd><span class="delivery ${esc(item.delivery_status)}">${esc(item.delivery_status)}</span></dd></div><div><dt>Event / Retry</dt><dd>v${item.event_version} / ${item.retry_count}회</dd></div>
  ${item.last_error?`<div class="wide error-box"><dt>최근 동기화 오류</dt><dd>${esc(item.last_error)}</dd></div>`:''}<div><dt>신청 시각</dt><dd>${esc(formatDate(item.created_at))}</dd></div><div><dt>최종 갱신</dt><dd>${esc(formatDate(item.updated_at))}</dd></div></dl>`;detailDialog.showModal();}
async function retrySync(id,button){if(staticPreview){alert('정적 미리보기의 실패 건은 변경되지 않습니다. API 실행 후 실제 재시도를 검증하세요.');return;}const original=button.textContent;button.disabled=true;button.textContent='재시도 중…';try{await api(`/admin-api/v1/requests/${id}/retry-sync`,{method:'POST'});await refreshAll();}catch(error){alert(error.message);button.disabled=false;button.textContent=original;}}
document.querySelector('#decision-form').addEventListener('submit',async event=>{if(event.submitter?.value!=='confirm')return;event.preventDefault();if(staticPreview){dialog.close();alert('정적 미리보기의 샘플 신청은 변경되지 않습니다. API 실행 후 실제 승인·거절 흐름을 검증하세요.');return;}const id=document.querySelector('#decision-request-id').value;const action=document.querySelector('#decision-action').value;try{await api(`/admin-api/v1/requests/${id}/${action}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({reason:document.querySelector('#decision-reason').value||null})});dialog.close();await refreshAll();}catch(error){alert(error.message);}});

async function refreshAll(){try{await Promise.all([loadRequests(),loadProvisioningJobs(),loadGrants(),loadMonitoring()]);document.querySelector('#last-refreshed').textContent=`마지막 동기화 ${new Date().toLocaleTimeString('ko-KR')}`;}catch(error){requestsEl.innerHTML=`<p class="error">${esc(error.message)}</p>`;}}
async function resetDemoData(){
  if(staticPreview){alert('정적 미리보기 데이터는 초기화 대상이 아닙니다. Compose로 실행한 로컬 데모에서 사용하세요.');return;}
  if(!confirm('신청·승인·Terraform 작업·Grant·감사·할당 자원을 모두 삭제합니다. 이 작업은 되돌릴 수 없습니다. 계속할까요?'))return;
  resetInProgress=true;resetDemoButton.disabled=true;resetDemoButton.textContent='초기화 중…';resetMessage.textContent='';
  try{
    const result=await api('/admin-api/v1/demo/reset',{method:'POST'});
    const deleted=Object.values(result.deleted||{}).reduce((sum,count)=>sum+Number(count||0),0);
    await refreshAll();
    resetMessage.textContent=`데모 데이터 ${deleted}건을 초기화했습니다.`;
  }catch(error){resetMessage.textContent=`초기화 실패: ${error.message}`;}
  finally{resetInProgress=false;resetDemoButton.disabled=false;resetDemoButton.textContent='데모 데이터 초기화';}
}
async function seedDemoData(){
  if(staticPreview){alert('기본 시나리오 생성은 Compose로 실행한 로컬 데모에서 동작합니다.');return;}
  seedInProgress=true;seedDemoButton.disabled=true;seedDemoButton.textContent='시나리오 준비 중…';seedMessage.textContent='';
  try{
    const result=await api('/admin-api/v1/demo/seed',{method:'POST'});
    await refreshAll();
    seedMessage.textContent=result.created?'개발 VM 승인 대기 신청 1건을 준비했습니다.':'기본 시나리오가 이미 준비되어 있습니다.';
  }catch(error){seedMessage.textContent=`시나리오 생성 실패: ${error.message}`;}
  finally{seedInProgress=false;seedDemoButton.disabled=false;seedDemoButton.textContent='기본 시나리오 생성';}
}
function openPortal(){document.querySelector('#login-view').hidden=true;document.querySelector('#portal-shell').hidden=false;document.querySelector('#preview-banner').hidden=!staticPreview;refreshAll();}
document.querySelector('#refresh').addEventListener('click',refreshAll);document.querySelector('#dev-user').addEventListener('change',refreshAll);
resetDemoButton.addEventListener('click',resetDemoData);resetDemoButton.hidden=!localDev;
seedDemoButton.addEventListener('click',seedDemoData);demoCenter.hidden=!localDev;demoNav.hidden=!localDev;
document.querySelector('#request-detail-close').addEventListener('click',()=>detailDialog.close());detailDialog.addEventListener('click',event=>{if(event.target===detailDialog)detailDialog.close();});
document.querySelector('#login-button').addEventListener('click',()=>{if(localDev){openPortal();return;}const returnTo=new URL(window.location.href);returnTo.searchParams.set('auth_return','1');window.location.assign(`/auth/admin/login?return_to=${encodeURIComponent(returnTo.toString())}`);});
document.querySelector('#logout-button').addEventListener('click',()=>{if(localDev){document.querySelector('#portal-shell').hidden=true;document.querySelector('#login-view').hidden=false;return;}window.location.assign(`/auth/logout?redirect_uri=${encodeURIComponent(window.location.origin + '/')}`);});
if(localDev){document.querySelector('#login-button').textContent='로컬 관리자 데모 로그인';document.querySelector('#login-note').textContent='비밀번호와 MFA를 입력하지 않는 로컬 화면 시연 모드입니다.';}else if(new URLSearchParams(window.location.search).get('auth_return')==='1'){openPortal();}
window.setInterval(()=>{if(!staticPreview&&!resetInProgress&&!seedInProgress&&!document.querySelector('#portal-shell').hidden&&document.visibilityState==='visible')refreshAll();},5000);
