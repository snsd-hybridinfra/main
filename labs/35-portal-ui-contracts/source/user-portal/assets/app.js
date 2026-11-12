const catalogEl = document.querySelector('#catalog');
const requestsEl = document.querySelector('#requests');
const resourcesEl = document.querySelector('#resources');
const monitoringEl = document.querySelector('#monitoring');
const blueprintEl = document.querySelector('#product-code');
const form = document.querySelector('#request-form');
const messageEl = document.querySelector('#form-message');
const requestDetailDialog = document.querySelector('#request-detail-dialog');
const staticPreview = window.location.protocol === 'file:';
const localDev = staticPreview || ['localhost', '127.0.0.1'].includes(window.location.hostname);

const previewCatalog = [
  ['DEVELOPER_WORKSPACE','Developer Workspace','격리된 비운영 개발 데스크톱과 개인 작업공간','PRIVATE_DEVELOPER_ACCESS',['DEV','TEST'],['SMALL','STANDARD'],[4,8,24,72]],
  ['SECURE_ADMIN_WORKSPACE','Secure Admin Workspace','관리영역 접근을 제한한 단기 특권 작업공간','PRIVILEGED_MANAGEMENT_ISOLATED',['DEV','TEST'],['STANDARD'],[4,8]],
  ['WEB_APPLICATION_STACK','Web Application Stack','비공개 웹 애플리케이션 개발·검증 실행환경','PRIVATE_WEB_INGRESS',['DEV','TEST','STG'],['SMALL','STANDARD'],[8,24,72,168]],
  ['API_DEVELOPMENT_STACK','Financial SaaS Development PaaS','금융 SaaS의 DEV·TEST·STG 개발을 위한 표준 PaaS','PRIVATE_SAAS_INGRESS',['DEV','TEST','STG'],['SMALL','STANDARD'],[8,24,72,168]],
  ['VM_APPLICATION_STACK','VM Application Stack','OpenStack 기반 비공개 애플리케이션 VM 환경','PRIVATE_APPLICATION',['DEV','TEST','STG'],['SMALL','STANDARD','LARGE'],[4,8,24,72,168]],
  ['AI_AGENT_SANDBOX','Persistent AI Agent Sandbox','승인·예산·격리를 적용한 장기 비동기 개발 작업','AI_AGENT_EGRESS_BROKERED',['DEV','TEST'],['STANDARD','LARGE'],[1,4,8,24]],
  ['DATA_PROCESSING_LAB','Data Processing Lab','합성 데이터 처리와 저장소 연동을 위한 격리 랩','PRIVATE_DATA_ISOLATED',['DEV','TEST'],['STANDARD','LARGE'],[8,24,72]],
  ['SYNTHETIC_MARKET_DATA_LAB','Synthetic Market Data Lab','합성 시세 데이터와 제한된 멀티캐스트 검증 랩','SYNTHETIC_MULTICAST_BOUNDED',['TEST'],['STANDARD'],[4,8]],
].map(([blueprint_id,display_name,summary,network_profile,allowed_environments,allowed_sizes,allowed_duration_hours]) => ({
  blueprint_id, display_name, summary, network_profile,
  allowed_environments, allowed_sizes, allowed_duration_hours,
}));
const previewRequests = [{
  request_id:'DEMO-REQ-001', idempotency_key:'demo-request-001', owner_id:'demo-user',
  product_code:null, blueprint_id:'VM_APPLICATION_STACK', blueprint_environment:'DEV',
  blueprint_size:'SMALL', manifest_digest:'sha256:demo', parameters:{}, duration_hours:24,
  purpose:'비운영 애플리케이션 랩 검증', status:'GRANTED', rejection_reason:null,
  grant_id:'DEMO-GRANT-001', grant_expires_at:'2026-08-28T08:30:00+09:00',
  resource_id:'DEMO-RESOURCE-001', resource_status:'RUNNING', event_version:3,
  retry_count:0, delivery_status:'DELIVERED', last_error:null,
  created_at:'2026-08-27T08:20:00+09:00', updated_at:'2026-08-27T08:31:00+09:00',
}];
const previewResources = [{
  resource_id:'DEMO-RESOURCE-001', request_id:'DEMO-REQ-001', owner_id:'demo-user',
  status:'RUNNING', endpoint:'10.20.12.34', resource_type:'VM_APPLICATION_STACK',
  display_name:'비운영 애플리케이션 랩', details:{environment:'DEV',size:'SMALL',monitoring_status:'ACTIVE',provisioner:'Mock Terraform Runner'},
  event_version:4, updated_at:'2026-08-27T08:34:00+09:00',
}];

let catalog = [];
let requestsById = new Map();

function authHeaders(extra = {}) {
  return {'X-Dev-User':document.querySelector('#dev-user').value.trim(),'X-Dev-Roles':'user',...extra};
}
function escapeHtml(value) {
  return String(value ?? '').replace(/[&<>'"]/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[ch]));
}
function formatDate(value) {
  if (!value) return '-';
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? String(value) : date.toLocaleString('ko-KR');
}
function formatDuration(hours) {
  return Number(hours) % 24 === 0 ? `${Number(hours) / 24}일` : `${hours}시간`;
}
function requestLabel(item) {
  return item.blueprint_id || '레거시 요청';
}
function statusTimeline(item) {
  let steps;
  if (item.status === 'REJECTED') steps = [['PENDING','신청 접수'],['REJECTED','신청 거절']];
  else if (item.status === 'CANCELLED') steps = [['PENDING','신청 접수'],['CANCELLED','사용자 취소']];
  else {
    steps = [['PENDING','신청 접수'],['APPROVED','관리자 승인'],['PROVISIONING','자동화 실행'],['RUNNING','자원 검증'],['GRANTED','Grant 발급']];
    if (['REVOKED','EXPIRED'].includes(item.status)) steps.push([item.status,item.status === 'REVOKED' ? '권한 회수' : '기간 만료']);
  }
  const effectiveStatus = item.status === 'APPROVED' && item.resource_status ? item.resource_status : item.status;
  const currentIndex = Math.max(0, steps.findIndex(([status]) => status === effectiveStatus));
  return `<ol class="request-timeline">${steps.map(([status,label],index) => {
    const state = index < currentIndex ? 'completed' : index === currentIndex ? (['REJECTED','CANCELLED','REVOKED','EXPIRED'].includes(status) ? 'terminal' : 'current') : 'pending';
    return `<li class="${state}"><span>${index + 1}</span><div><strong>${escapeHtml(label)}</strong><small>${escapeHtml(status)}</small></div></li>`;
  }).join('')}</ol>`;
}
function formatKeyValues(values) {
  const entries = Object.entries(values || {});
  return entries.length ? entries.map(([key,value]) => `${escapeHtml(key)}: ${escapeHtml(value)}`).join(' · ') : '-';
}
function openRequestDetail(item) {
  if (!item) return;
  document.querySelector('#request-detail-content').innerHTML = `
    ${statusTimeline(item)}
    <dl class="detail-grid">
      <div><dt>상품</dt><dd>${escapeHtml(requestLabel(item))}</dd></div>
      <div><dt>환경 / 크기</dt><dd>${escapeHtml(item.blueprint_environment || '-')} / ${escapeHtml(item.blueprint_size || '-')}</dd></div>
      <div class="wide"><dt>사용자 입력</dt><dd>${formatKeyValues(item.parameters)}</dd></div>
      <div><dt>사용기간</dt><dd>${formatDuration(item.duration_hours)}</dd></div>
      <div class="wide"><dt>사용 목적</dt><dd>${escapeHtml(item.purpose)}</dd></div>
      <div><dt>접근 권한</dt><dd>${item.grant_id ? '발급됨' : '미발급'}</dd></div>
      <div><dt>Grant 만료</dt><dd>${escapeHtml(formatDate(item.grant_expires_at))}</dd></div>
      <div><dt>Callback 상태</dt><dd><span class="delivery ${escapeHtml(item.delivery_status)}">${escapeHtml(item.delivery_status)}</span></dd></div>
      <div><dt>Event / Retry</dt><dd>v${item.event_version} / ${item.retry_count}회</dd></div>
      ${item.last_error ? `<div class="wide error-box"><dt>최근 동기화 오류</dt><dd>${escapeHtml(item.last_error)}</dd></div>` : ''}
      <div><dt>신청 시각</dt><dd>${escapeHtml(formatDate(item.created_at))}</dd></div>
      <div><dt>최종 갱신</dt><dd>${escapeHtml(formatDate(item.updated_at))}</dd></div>
    </dl>`;
  requestDetailDialog.showModal();
}
async function api(path, options = {}) {
  const response = await fetch(path, {...options, headers:authHeaders(options.headers)});
  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    throw new Error(apiErrorMessage(body, response.status));
  }
  return response.json();
}
function apiErrorMessage(body, status) {
  const detail = body?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) return detail.map(issue => `${issue?.loc?.filter(part => part !== 'body').join('.') || ''}: ${issue?.msg || '입력값을 확인해 주세요.'}`).join(' / ');
  return `요청 처리 실패 (HTTP ${status})`;
}
function selectBlueprint(code) {
  blueprintEl.value = code;
  updateBlueprintFields(code);
  document.querySelector('#request-section').scrollIntoView({behavior:'smooth'});
}
function updateBlueprintFields(code) {
  const item = catalog.find(entry => entry.blueprint_id === code);
  catalogEl.querySelectorAll('[data-blueprint]').forEach(card => {
    const selected = card.dataset.blueprint === code;
    card.classList.toggle('selected', selected);
    card.setAttribute('aria-selected', String(selected));
  });
  const allowedHours = item?.allowed_duration_hours || [4,8,24,72,168];
  form.duration_hours.innerHTML = allowedHours.map(hours => `<option value="${hours}">${formatDuration(hours)}</option>`).join('');
  document.querySelector('#product-parameters').innerHTML = `
    <div class="field"><label for="blueprint-environment">환경</label><select id="blueprint-environment" name="environment" required>${(item?.allowed_environments || []).map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('')}</select></div>
    <div class="field"><label for="blueprint-size">크기</label><select id="blueprint-size" name="size" required>${(item?.allowed_sizes || []).map(value => `<option value="${escapeHtml(value)}">${escapeHtml(value)}</option>`).join('')}</select></div>`;
}
async function loadCatalog() {
  const selected = blueprintEl.value;
  catalog = staticPreview ? previewCatalog : await api('/api/v1/catalog');
  blueprintEl.innerHTML = catalog.map(item => `<option value="${escapeHtml(item.blueprint_id)}">${escapeHtml(item.display_name)}</option>`).join('');
  catalogEl.innerHTML = catalog.map(item => `
    <article class="catalog-card ${item.blueprint_id === 'VM_APPLICATION_STACK' ? 'primary' : ''}" role="option" aria-selected="false" tabindex="0" data-blueprint="${escapeHtml(item.blueprint_id)}">
      <span class="badge">승인된 조합형 상품</span><h3>${escapeHtml(item.display_name)}</h3>
      <p>${escapeHtml(item.summary)}</p>
      <dl class="resource-details"><div><dt>네트워크</dt><dd>${escapeHtml(item.network_profile)}</dd></div><div><dt>환경</dt><dd>${escapeHtml(item.allowed_environments.join(' / '))}</dd></div><div><dt>크기</dt><dd>${escapeHtml(item.allowed_sizes.join(' / '))}</dd></div></dl>
      <small>사용기간 ${item.allowed_duration_hours.map(formatDuration).join(' / ')}</small>
    </article>`).join('');
  catalogEl.querySelectorAll('[data-blueprint]').forEach(card => {
    card.addEventListener('click', () => selectBlueprint(card.dataset.blueprint));
    card.addEventListener('keydown', event => { if (event.key === 'Enter') selectBlueprint(card.dataset.blueprint); });
  });
  const next = catalog.some(item => item.blueprint_id === selected) ? selected : (catalog.find(item => item.blueprint_id === 'VM_APPLICATION_STACK')?.blueprint_id || catalog[0]?.blueprint_id);
  if (next) selectBlueprint(next);
}
async function loadRequests() {
  const items = staticPreview ? previewRequests : await api('/api/v1/requests');
  requestsById = new Map(items.map(item => [item.request_id,item]));
  document.querySelector('#request-total').textContent = items.length;
  document.querySelector('#request-pending').textContent = items.filter(item => ['PENDING','APPROVED'].includes(item.status)).length;
  document.querySelector('#request-granted').textContent = items.filter(item => ['GRANTED','RUNNING'].includes(item.status)).length;
  document.querySelector('#request-closed').textContent = items.filter(item => ['REJECTED','CANCELLED','REVOKED','EXPIRED','TERMINATED'].includes(item.status)).length;
  if (!items.length) { requestsEl.innerHTML = '<p class="empty">아직 신청이 없습니다.</p>'; return; }
  requestsEl.innerHTML = `<table><thead><tr><th>상품</th><th>환경 / 크기</th><th>기간</th><th>상태</th><th>접근 권한</th><th>작업</th></tr></thead><tbody>${items.map(item => `
    <tr><td>${escapeHtml(requestLabel(item))}</td><td>${escapeHtml(item.blueprint_environment || '-')} / ${escapeHtml(item.blueprint_size || '-')}</td>
    <td>${formatDuration(item.duration_hours)}</td><td><span class="status ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></td>
    <td>${item.grant_id ? `발급됨<br>${escapeHtml(formatDate(item.grant_expires_at))}` : '미발급'}</td>
    <td><button class="ghost" data-detail="${escapeHtml(item.request_id)}">상세</button>${item.status === 'PENDING' ? ` <button class="danger" data-cancel="${escapeHtml(item.request_id)}">취소</button>` : ''}</td></tr>`).join('')}</tbody></table>`;
  requestsEl.querySelectorAll('[data-detail]').forEach(button => button.addEventListener('click', () => openRequestDetail(requestsById.get(button.dataset.detail))));
  requestsEl.querySelectorAll('[data-cancel]').forEach(button => button.addEventListener('click', async () => {
    if (staticPreview) { alert('정적 미리보기의 샘플 신청은 변경되지 않습니다.'); return; }
    try { await api(`/api/v1/requests/${button.dataset.cancel}/cancel`, {method:'POST'}); await loadRequests(); }
    catch (error) { alert(error.message); }
  }));
}
async function loadResources() {
  const items = staticPreview ? previewResources : await api('/api/v1/resources');
  renderMonitoring(items);
  if (!items.length) { resourcesEl.innerHTML = '<p class="empty">등록된 할당 자원이 없습니다.</p>'; return; }
  resourcesEl.innerHTML = `<table><thead><tr><th>자원</th><th>공급 방식</th><th>상태</th><th>Endpoint</th><th>갱신</th></tr></thead><tbody>${items.map(item => `
    <tr><td><strong>${escapeHtml(item.display_name)}</strong><br><small>${escapeHtml(item.resource_type)}</small></td><td>${escapeHtml(item.details?.provisioner || '-')}</td>
    <td><span class="status ${escapeHtml(item.status)}">${escapeHtml(item.status)}</span></td><td>${escapeHtml(item.endpoint || '-')}</td><td>${escapeHtml(formatDate(item.updated_at))}</td></tr>`).join('')}</tbody></table>`;
}
function renderMonitoring(items) {
  const running = items.filter(item => item.status === 'RUNNING');
  monitoringEl.innerHTML = running.length ? `<table><thead><tr><th>상품</th><th>상태</th><th>관측</th><th>갱신</th></tr></thead><tbody>${running.map(item => `<tr><td>${escapeHtml(item.resource_type)}</td><td>${escapeHtml(item.details?.monitoring_status || 'PENDING')}</td><td>CPU·Memory·Disk·Network·Alert</td><td>${escapeHtml(formatDate(item.updated_at))}</td></tr>`).join('')}</tbody></table>` : '<p class="empty">사용 중인 인프라가 생성되면 모니터링 상태가 표시됩니다.</p>';
}
async function refreshAll({refreshCatalog = false} = {}) {
  const loaders = [loadRequests(),loadResources()];
  if (refreshCatalog || catalog.length === 0) loaders.unshift(loadCatalog());
  try { await Promise.all(loaders); document.querySelector('#last-refreshed').textContent = `마지막 동기화 ${new Date().toLocaleTimeString('ko-KR')}`; }
  catch (error) { requestsEl.innerHTML = `<p class="error">${escapeHtml(error.message)}</p>`; }
}
blueprintEl.addEventListener('change', () => updateBlueprintFields(blueprintEl.value));
form.addEventListener('submit', async event => {
  event.preventDefault(); messageEl.textContent = '신청 중…';
  if (staticPreview) { messageEl.textContent = '정적 미리보기에서는 신청할 수 없습니다.'; return; }
  const payload = {
    blueprint_id:blueprintEl.value,
    environment:form.environment.value,
    size:form.size.value,
    duration_hours:Number(form.duration_hours.value),
    purpose:form.purpose.value.trim(),
  };
  try {
    await api('/api/v1/blueprint-requests', {method:'POST',headers:{'Content-Type':'application/json','Idempotency-Key':crypto.randomUUID()},body:JSON.stringify(payload)});
    messageEl.textContent = '신청이 접수됐습니다.'; await loadRequests();
  } catch (error) { messageEl.textContent = error.message; }
});
document.querySelector('#refresh').addEventListener('click', refreshAll);
document.querySelector('#dev-user').addEventListener('change', refreshAll);
document.querySelector('#request-detail-close').addEventListener('click', () => requestDetailDialog.close());
requestDetailDialog.addEventListener('click', event => { if (event.target === requestDetailDialog) requestDetailDialog.close(); });
function openPortal() {
  document.querySelector('#login-view').hidden = true;
  document.querySelector('#portal-shell').hidden = false;
  document.querySelector('#preview-banner').hidden = !staticPreview;
  refreshAll({refreshCatalog: true});
}
document.querySelector('#login-button').addEventListener('click', () => {
  if (localDev) { openPortal(); return; }
  const returnTo = new URL(window.location.href); returnTo.searchParams.set('auth_return','1');
  window.location.assign(`/auth/user/login?return_to=${encodeURIComponent(returnTo.toString())}`);
});
document.querySelector('#logout-button').addEventListener('click', () => {
  if (localDev) { document.querySelector('#portal-shell').hidden = true; document.querySelector('#login-view').hidden = false; return; }
  window.location.assign(`/auth/logout?redirect_uri=${encodeURIComponent(window.location.origin + '/')}`);
});
if (localDev) {
  document.querySelector('#login-button').textContent = '로컬 데모 로그인';
  document.querySelector('#login-note').textContent = '비밀번호를 입력하지 않는 로컬 화면 시연 모드입니다.';
} else if (new URLSearchParams(window.location.search).get('auth_return') === '1') openPortal();
window.setInterval(() => {
  if (!staticPreview && !document.querySelector('#portal-shell').hidden && document.visibilityState === 'visible') refreshAll();
}, 5000);
