const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');

async function main() {
  let user = {userId:'alice',tenantId:'tenant-a'};
  let load = async()=>({name:'Alice request'});
  const window = {
    EclipseAuth:{user:()=>user}, EclipseApp:{refresh:()=>{}},
    crypto:{randomUUID:()=> 'synthetic-key'}
  };
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../../services/user-portal/eclipse/js/portal-ui.js'),'utf8'),{window,FormData:class{}});
  const controller=window.EclipsePortalUI.controller(()=>load(),(_,data)=>data.name);
  controller.render('/developer/requests');
  await controller.reload();
  assert.match(controller.render('/developer/requests'),/Alice request/);

  let finishOld;
  load=()=>new Promise(resolve=>{finishOld=resolve;});
  const old=controller.reload();
  user={userId:'bob',tenantId:'tenant-b'};
  assert.doesNotMatch(controller.render('/developer/requests'),/Alice request/);
  load=async()=>({name:'Bob request'});
  await controller.reload();
  finishOld({name:'Delayed Alice response'});
  await old;
  assert.match(controller.render('/developer/requests'),/Bob request/);
  assert.doesNotMatch(controller.render('/developer/requests'),/Alice/);

  // Logging out and back into the same identity must fetch current database state.
  controller.resetCache();
  assert.doesNotMatch(controller.render('/developer/requests'),/Bob request/);
  load=async()=>({name:'New Bob callback state'});
  await controller.reload();
  assert.match(controller.render('/developer/requests'),/New Bob callback state/);
  console.log('PASS: cross-tenant cache, delayed response, and same-user re-login');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
