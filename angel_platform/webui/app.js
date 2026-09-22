const $=s=>document.querySelector(s);
const messages=$('#messages');
let history=[],busy=false,currentPage='chat';
let activeSpeech=null;

const esc=t=>String(t).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const isThinking=t=>!t||/^thinking…?$/i.test(String(t).trim())||/^thinking\.\.\.$/i.test(String(t).trim());

function stopReading(){
  if('speechSynthesis' in window) window.speechSynthesis.cancel();
  if(activeSpeech?.button) activeSpeech.button.disabled=false;
  if(activeSpeech?.stopButton) activeSpeech.stopButton.disabled=true;
  if(activeSpeech?.el) activeSpeech.el.classList.remove('speaking');
  activeSpeech=null;
  const globalStop=$('#stopReading');
  if(globalStop) globalStop.disabled=true;
}

function speak(text,button=null,stopButton=null,el=null){
  const clean=String(text||'').trim();
  if(isThinking(clean)) return;
  if(!('speechSynthesis' in window)){alert('Read aloud is not supported in this browser.');return;}
  stopReading();
  const utterance=new SpeechSynthesisUtterance(clean);
  activeSpeech={button,stopButton,el};
  if(button) button.disabled=true;
  if(stopButton) stopButton.disabled=false;
  const globalStop=$('#stopReading');
  if(globalStop) globalStop.disabled=false;
  if(el) el.classList.add('speaking');
  utterance.onend=stopReading;
  utterance.onerror=stopReading;
  window.speechSynthesis.speak(utterance);
}

function copyText(text){
  const clean=String(text||'').trim();
  if(isThinking(clean)) return Promise.reject(new Error('The response is still being generated.'));
  if(navigator.clipboard?.writeText) return navigator.clipboard.writeText(clean);
  const area=document.createElement('textarea');
  area.value=clean;document.body.appendChild(area);area.select();
  try{document.execCommand('copy');}finally{area.remove();}
  return Promise.resolve();
}

function saveText(text,ext='txt'){
  const clean=String(text||'').trim();
  if(isThinking(clean)) return;
  const a=document.createElement('a');
  a.href=URL.createObjectURL(new Blob([clean],{type:'text/plain'}));
  a.download='angel-response.'+ext;a.click();URL.revokeObjectURL(a.href);
}

function currentMessageText(el){return el?.querySelector('.body')?.textContent?.trim()||'';}

function addMessage(who,text){
  const el=document.createElement('article');
  el.className='message '+(who==='Me'?'user':'');
  el.innerHTML=`<div class="meta"><b>${who==='Me'?'M':'🪽'} &nbsp; ${esc(who)}</b><span>${new Date().toLocaleTimeString([], {hour:'numeric',minute:'2-digit'})}</span></div><div class="body">${esc(text)}</div><div class="actions"><button data-copy>Copy</button><button data-speak>Read aloud</button><button data-stop disabled>Stop reading</button></div>`;
  const copyButton=el.querySelector('[data-copy]');
  const speakButton=el.querySelector('[data-speak]');
  const stopButton=el.querySelector('[data-stop]');
  const refreshButtons=()=>{
    const ready=!isThinking(currentMessageText(el));
    copyButton.disabled=!ready;
    speakButton.disabled=!ready;
  };
  copyButton.onclick=()=>copyText(currentMessageText(el)).catch(e=>alert(e.message));
  speakButton.onclick=()=>speak(currentMessageText(el),speakButton,stopButton,el);
  stopButton.onclick=stopReading;
  messages.appendChild(el);messages.scrollTop=messages.scrollHeight;
  refreshButtons();
  el.refreshButtons=refreshButtons;
  return el;
}

function setBusy(v){busy=v;$('#send').disabled=v;$('#send').style.opacity=v?'.55':'1';}

function readLocalConversations(){
  try{return JSON.parse(localStorage.getItem('angel_conversations')||'[]');}
  catch{return [];}
}
function writeLocalConversations(items){
  localStorage.setItem('angel_conversations',JSON.stringify(items.slice(0,100)));
}
function saveConversation(){
  if(!history.length)return;
  const saved=readLocalConversations();
  const first=history.find(x=>x.role==='user');
  const title=(first?.content||'Untitled Chat').slice(0,48);
  const existing=saved.find(x=>x.id===window.angelConversationId);
  const record={id:window.angelConversationId||Date.now().toString(),title,history:[...history],updated:new Date().toISOString()};
  const next=existing?saved.map(x=>x.id===record.id?record:x):[record,...saved];
  window.angelConversationId=record.id;
  writeLocalConversations(next);
  renderConversationHistory();
}
function renderConversationHistory(){
  const box=$('#conversationHistory');if(!box)return;
  const saved=readLocalConversations().sort((a,b)=>String(b.updated||'').localeCompare(String(a.updated||'')));
  box.innerHTML=saved.map(item=>`<button class="history-item" data-history-id="${esc(item.id)}" title="${esc(item.title)}">${esc(item.title)}</button>`).join('')||'<small class="history-empty">No saved conversations yet.</small>';
  box.querySelectorAll('[data-history-id]').forEach(b=>b.onclick=()=>loadConversation(b.dataset.historyId));
}
function loadConversation(id){
  if(busy)return alert('Please wait for the current response to finish.');
  const item=readLocalConversations().find(x=>x.id===id);if(!item)return;
  window.angelConversationId=id;
  history=item.history||[];messages.innerHTML='';
  history.forEach(x=>addMessage(x.role==='user'?'Me':'Angel AI',x.content));
  messages.scrollTop=messages.scrollHeight;renderConversationHistory();
}
async function loadPersistentServerHistory(){
  try{
    const response=await fetch('/api/history');
    if(!response.ok)return;
    const payload=await response.json();
    const serverHistory=Array.isArray(payload.history)?payload.history:[];
    if(!serverHistory.length)return;
    const normalized=serverHistory.map(x=>({role:x.role==='assistant'?'assistant':'user',content:String(x.content||'')})).filter(x=>x.content);
    if(!normalized.length)return;
    const local=readLocalConversations();
    const serverId='server-history';
    const record={id:serverId,title:'Recovered Angel History',history:normalized,updated:new Date().toISOString()};
    const existing=local.find(x=>x.id===serverId);
    writeLocalConversations(existing?[record,...local.filter(x=>x.id!==serverId)]:[record,...local]);
    // Keep recovered history available in the history list, but leave the
    // currently opened chat blank until the user sends a message.
    renderConversationHistory();
  }catch(error){console.warn('Persistent history could not be loaded:',error);}
}
function startNewChat(){
  if(busy){alert('Please wait for the current response to finish.');return;}
  if(history.length){saveConversation();}
  window.angelConversationId=null;
  history=[];messages.innerHTML='';
  // A new chat is intentionally blank. Angel speaks only after the user sends a message.
  $('#prompt')?.focus();renderConversationHistory();
}

async function getDeviceLocation(){
  if(!navigator.geolocation) return null;
  return new Promise(resolve=>{
    navigator.geolocation.getCurrentPosition(
      pos=>resolve({latitude:pos.coords.latitude,longitude:pos.coords.longitude,label:'device location'}),
      ()=>resolve(null),
      {enableHighAccuracy:false,timeout:5000,maximumAge:300000}
    );
  });
}

async function send(){
  if(busy)return;
  const input=$('#prompt'),text=input.value.trim();if(!text)return;
  input.value='';addMessage('Me',text);history.push({role:'user',content:text});
  const pending=addMessage('Angel AI','Thinking…');setBusy(true);
  try{
    let location=null;
    if(/\\b(weather|forecast|temperature|rain|snow|wind|sunny|cloudy|humidity|conditions)\\b/i.test(text) && !/\\b(in|near|for)\\s+[a-z]/i.test(text)){
      location=await getDeviceLocation();
    }
    const res=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:text,model:$('#model').value,history,location})});
    if(!res.ok)throw Error('HTTP '+res.status);
    const reader=res.body.getReader(),decoder=new TextDecoder();let out='';
    pending.querySelector('.body').textContent='';
    while(true){
      const {value,done}=await reader.read();if(done)break;
      out+=decoder.decode(value,{stream:true});
      pending.querySelector('.body').textContent=out;
      pending.refreshButtons?.();messages.scrollTop=messages.scrollHeight;
    }
    out=out.trim();
    if(!out) out='Angel returned an empty response.';
    pending.querySelector('.body').textContent=out;
    pending.refreshButtons?.();
    history.push({role:'assistant',content:out});saveConversation();
  }catch(e){
    const msg='Connection error: '+e.message;
    pending.querySelector('.body').textContent=msg;
    pending.refreshButtons?.();
  }finally{setBusy(false);}
}

const pageInfo={chat:['🪽 Angel AI','Your AI Assistant · Always Here'],projects:['Projects','Your working projects and workspaces'],modules:['Module Library','Your maintained TCDOVERLORD tools'],tools:['System Tools','Read-only diagnostics and tool discovery'],devops:['DevOps','Builds, tests, Git, and artifacts'],memory:['Memory','Local conversation history and retention'],settings:['Settings','Providers, experience, and execution preferences']};
function renderPage(page){currentPage=page;document.querySelectorAll('[data-page]').forEach(b=>b.classList.toggle('active',b.dataset.page===page));const [title,sub]=pageInfo[page]||pageInfo.chat;$('#workspaceTitle').textContent=title;$('#workspaceSubtitle').textContent=sub;const chat=page==='chat';$('#providerRow').style.display=chat?'flex':'none';$('#messages').classList.toggle('hidden',!chat);$('#composer').classList.toggle('hidden',!chat);$('#pageContent').classList.toggle('hidden',chat);if(!chat){$('#pageContent').innerHTML=markup(page);wirePage();}}
function markup(page){if(page==='modules')return `<div class="page-toolbar"><input id="moduleSearch" placeholder="Search your modules…"><button id="addModule">＋ Add GitHub Module</button><button data-action="module_scan">Refresh Catalog</button></div><div id="moduleAddPanel" class="tool-card hidden"><h3>Add a GitHub module</h3><p>Enter a public repository as owner/name. The repository is added to your catalog first; Prepare downloads it locally.</p><div class="page-grid"><label>Repository<input id="newRepo" placeholder="tcdoverlord/My-Tool"></label><label>Display name<input id="newName" placeholder="My Tool"></label><label>Category<input id="newCategory" placeholder="Utilities"></label></div><div class="actions"><button id="saveModule">Add Module</button><button id="cancelAdd">Cancel</button></div><pre id="addModuleResult">Ready.</pre></div><div id="moduleInspector" class="tool-card hidden"><div class="page-toolbar"><h3 id="inspectorTitle">Module Inspector</h3><button id="closeInspector">Close</button></div><pre id="inspectorResult">Select Inspect Module to view details.</pre><div class="actions"><button id="inspectRepo">Open GitHub Repository</button><button id="openReadme">Open README</button><button id="openWebModule">Open Web Module</button><button id="prepareModule">Prepare / Update Local Copy</button><button id="configureModule">Configure Run</button><button id="runModule">Run Module</button><button id="removeModule">Remove From Catalog</button></div><pre id="moduleRunResult">No run action yet.</pre></div><div id="moduleGrid" class="module-grid"><p>Loading modules…</p></div>`;if(page==='tools')return `<div class="page-grid"><section class="tool-card"><h3>Tool Inventory</h3><p>Check local dependencies without changing your system.</p><button data-action="tool_inventory">Check Availability</button><pre id="toolResult">Ready.</pre></section><section class="tool-card"><h3>System Health</h3><p>Read-only environment information.</p><button data-action="system_health">Run Scan</button><pre id="healthResult">Ready.</pre></section></div>`;if(page==='projects')return `<div class="page-grid"><section class="tool-card"><h3>Active Workspace</h3><p>Create and inspect a temporary project workspace.</p><button data-action="workspace_status">Inspect Workspace</button><pre id="workspaceResult">Ready.</pre></section><section class="tool-card"><h3>Project Workflow</h3><p>Angel can prepare a project, test it, and package a ZIP.</p><button data-page-target="devops">Open DevOps</button></section></div>`;if(page==='devops')return `<div class="page-grid"><section class="tool-card"><h3>Builds & Artifacts</h3><p>Build operations live here instead of the everyday chat.</p><button data-action="build_zip">Prepare ZIP Build</button><button data-action="build_exe">EXE Instructions</button><pre id="devopsResult">Ready.</pre></section><section class="tool-card"><h3>Execution Profile</h3><p>Balanced: routine diagnostics allowed; impactful changes require approval.</p><button data-action="execution_policy">View Policy</button><pre id="policyResult">Ready.</pre></section></div>`;if(page==='memory')return `<div class="page-grid"><section class="tool-card"><h3>Local Memory</h3><p>Conversation history is stored locally for continuity.</p><button data-action="memory_status">Inspect Memory</button><pre id="memoryResult">Ready.</pre></section></div>`;if(page==='settings')return `<div class="page-grid"><section class="tool-card"><h3>AI Providers</h3><p>Ollama is local-first. ChatGPT access requires a supported API/OAuth integration; passwords are never stored.</p><button data-action="chatgpt_info">ChatGPT Connection Details</button><pre id="providerResult">Ready.</pre></section><section class="tool-card"><h3>Security Profile</h3><p>Choose Open, Balanced, or Protected behavior in the future settings adapter.</p><button data-action="execution_policy">Review Current Profile</button><pre id="settingsResult">Balanced</pre></section><section class="tool-card"><h3>Module Library Backup</h3><p>Back up your catalog, removed-module choices, and local GitHub module files. Restore a saved backup when needed.</p><div class="actions"><button id="backupModules">Create Backup</button><button id="refreshBackups">Refresh Backups</button></div><label>Saved backup<select id="moduleBackupSelect"><option value="">Loading backups…</option></select></label><button id="restoreModules">Restore Selected Backup</button><pre id="backupResult">Ready.</pre></section><section class="tool-card"><h3>Secure GitHub Credential Vault</h3><p>Optional authenticated GitHub access. Enter your GitHub login or profile URL. The token is encrypted locally with AES-256-GCM using a master password. The password cannot be recovered by Angel.</p><div class="page-grid"><label>GitHub username or profile URL<input id="vaultUsername" autocomplete="off" placeholder="GitHub login or https://github.com/username"></label><label>GitHub profile URL (generated)<input id="vaultProfileUrl" readonly placeholder="https://github.com/username"></label><label>Personal access token<input id="vaultToken" type="password" autocomplete="off" placeholder="Paste your GitHub token"></label></div><div class="security-divider"><span>Master password for Angel Platform</span></div><p class="security-note">Use a strong master password. Angel cannot recover it. Keep a secure copy in a safe place.</p><div class="page-grid"><label>Master password<input id="vaultPassword" type="password" autocomplete="new-password" placeholder="At least 12 characters"></label><label>Confirm master password<input id="vaultConfirm" type="password" autocomplete="new-password" placeholder="Type it again"></label></div><label class="security-confirm"><input id="vaultConfirmAcknowledgement" type="checkbox"> I understand that I must remember my master password or keep a secure copy in a safe place, and that Angel cannot recover it.</label><div class="actions"><button id="vaultSetup" disabled>Create / Replace Vault</button><button id="vaultTest">Test GitHub API</button><button id="vaultUnlock">Unlock</button><button id="vaultLock">Lock</button><button id="vaultDelete" class="danger">Delete Credentials</button><button id="vaultReset" class="danger">Reset Vault</button></div><p class="security-note">Delete Credentials and Reset Vault remove only Angel’s locally stored GitHub vault. They do not revoke the token on GitHub. You must enter your master password and type DELETE or RESET to confirm.</p><pre id="vaultResult">Checking vault…</pre></section></div>`;return `<section class="tool-card"><h3>Angel Nexus</h3><p>Use Angel AI to find and run maintained modules through approved workflows.</p><button data-page-target="modules">Browse Modules</button></section>`}
function wirePage(){$('#moduleSearch')?.addEventListener('input',e=>loadModules(e.target.value));document.querySelectorAll('[data-action]').forEach(b=>b.onclick=()=>action(b.dataset.action));document.querySelectorAll('[data-page-target]').forEach(b=>b.onclick=()=>renderPage(b.dataset.pageTarget));if(currentPage==='settings'){loadBackups();$('#backupModules')?.addEventListener('click',createBackup);$('#refreshBackups')?.addEventListener('click',loadBackups);$('#restoreModules')?.addEventListener('click',restoreBackup);wireVaultForm();}loadVaultStatus();$('#vaultSetup')?.addEventListener('click',setupVault);$('#vaultTest')?.addEventListener('click',testVault);$('#vaultUnlock')?.addEventListener('click',unlockVault);$('#vaultLock')?.addEventListener('click',lockVault);$('#vaultDelete')?.addEventListener('click',()=>removeVault('delete'));$('#vaultReset')?.addEventListener('click',()=>removeVault('reset'));if(currentPage==='modules'){loadModules();$('#closeInspector')?.addEventListener('click',()=>$('#moduleInspector')?.classList.add('hidden'));$('#addModule')?.addEventListener('click',()=>$('#moduleAddPanel')?.classList.remove('hidden'));$('#cancelAdd')?.addEventListener('click',()=>$('#moduleAddPanel')?.classList.add('hidden'));$('#saveModule')?.addEventListener('click',addModule);}}
async function loadModules(filter=''){const box=$('#moduleGrid');if(!box)return;const data=await fetch('/api/modules').then(r=>r.json());box.innerHTML=data.modules.filter(m=>(m.name+' '+m.category+' '+m.repo).toLowerCase().includes(filter.toLowerCase())).map(m=>`<article class="module-card"><h3>${esc(m.name)}</h3><small>${esc(m.category)}</small><p>${esc(m.description)}</p><code>${esc(m.repo)}</code><button data-module-id="${esc(m.id)}">Inspect Module</button></article>`).join('')||'<p>No modules match.</p>';box.querySelectorAll('[data-module-id]').forEach(b=>b.onclick=()=>inspectModule(b.dataset.moduleId));}
let selectedModuleId=null;let selectedModule=null;async function inspectModule(id){const panel=$('#moduleInspector');const result=$('#inspectorResult');if(!panel||!result)return;selectedModuleId=id;panel.classList.remove('hidden');result.textContent='Inspecting module…';try{const j=await fetch('/api/module?id='+encodeURIComponent(id)).then(r=>{if(!r.ok)throw Error('HTTP '+r.status);return r.json()});selectedModule=j.module;$('#inspectorTitle').textContent=j.module.name;result.textContent=JSON.stringify(j.module,null,2);$('#inspectRepo').onclick=()=>window.open('https://github.com/'+j.module.repo,'_blank','noopener');$('#openReadme').onclick=()=>window.open('/api/module-readme?id='+encodeURIComponent(id),'_blank','noopener');$('#openReadme').disabled=!j.module.prepared;$('#openReadme').title=j.module.prepared?'Open the local README as a readable webpage':'Prepare this module first to open its local README';const hasWeb=Boolean((j.module.entrypoints||[]).some(e=>e.type==='html'));$('#openWebModule').disabled=!hasWeb;$('#openWebModule').title=hasWeb?'Open the HTML module in a browser':'Prepare a module containing index.html or another HTML entrypoint first';$('#openWebModule').onclick=()=>window.open('/api/module-web?id='+encodeURIComponent(id),'_blank','noopener');$('#prepareModule').onclick=()=>action('module_prepare',{module_id:id});$('#configureModule').onclick=()=>configureModule();$('#runModule').onclick=()=>runSelectedModule();$('#removeModule').onclick=()=>removeModule();}catch(e){result.textContent='Inspection failed: '+e.message;}panel.scrollIntoView({behavior:'smooth',block:'start'});}
async function addModule(){const repo=$('#newRepo')?.value.trim();if(!repo)return alert('Enter a GitHub repository as owner/name.');const body={repo,name:$('#newName')?.value.trim(),category:$('#newCategory')?.value.trim()};const out=$('#addModuleResult');out.textContent='Adding module…';try{const r=await fetch('/api/modules/add',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Add failed');out.textContent='Added '+j.module.name+'. Inspect it, then prepare the workspace.';await loadModules();}catch(e){out.textContent='Add failed: '+e.message;}}
function configureModule(){if(!selectedModule)return;const type=prompt('Run type: python | powershell | batch | exe','python');if(!type)return;const file=prompt('Entrypoint file relative to module folder (example: main.py)','');if(!file)return;const args=prompt('Arguments (optional)','')??'';action('module_configure',{module_id:selectedModuleId,config:{type,file,args}}).then(()=>inspectModule(selectedModuleId));}
function runSelectedModule(){if(!selectedModule)return;const cfg=selectedModule.run_config;if(!cfg||!cfg.file){configureModule();return;}if(!confirm('Run '+selectedModule.name+' using '+cfg.file+'?'))return;action('module_run',{module_id:selectedModuleId,config:cfg});}
async function removeModule(){if(!selectedModule||!confirm('Remove '+selectedModule.name+' from the Angel catalog? Local files will be preserved.'))return;try{const r=await fetch('/api/modules/remove',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({module_id:selectedModuleId})});const j=await r.json();if(!r.ok)throw Error(j.error||'Remove failed');$('#moduleInspector')?.classList.add('hidden');await loadModules();setLiveMonitor(j.result,'Complete');refreshActivity();}catch(e){setLiveMonitor('Remove failed: '+e.message,'Error');}}
async function loadBackups(){const select=$('#moduleBackupSelect');if(!select)return;try{const j=await fetch('/api/module-backups').then(r=>r.json());select.innerHTML=j.backups.map(b=>`<option value="${esc(b.name)}">${esc(b.name)} · ${esc(b.created)}</option>`).join('')||'<option value="">No backups yet</option>';}catch(e){select.innerHTML='<option value="">Unable to load backups</option>';}}
async function createBackup(){const out=$('#backupResult');if(out)out.textContent='Creating backup…';try{const r=await fetch('/api/modules/backup',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const j=await r.json();if(!r.ok)throw Error(j.error||'Backup failed');if(out)out.textContent=j.result+'\nDownload: '+j.download;await loadBackups();setLiveMonitor(j.result,'Complete');refreshActivity();}catch(e){if(out)out.textContent='Backup failed: '+e.message;setLiveMonitor('Backup failed: '+e.message,'Error');}}
async function restoreBackup(){const name=$('#moduleBackupSelect')?.value;if(!name)return alert('Choose a saved backup first.');if(!confirm('Restore '+name+'? Current catalog metadata will be replaced.'))return;const out=$('#backupResult');if(out)out.textContent='Restoring backup…';try{const r=await fetch('/api/modules/restore',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name})});const j=await r.json();if(!r.ok)throw Error(j.error||'Restore failed');if(out)out.textContent=j.result;setLiveMonitor(j.result,'Complete');refreshActivity();}catch(e){if(out)out.textContent='Restore failed: '+e.message;setLiveMonitor('Restore failed: '+e.message,'Error');}}
async function loadVaultStatus(){const out=$('#vaultResult');if(!out)return;try{const s=await fetch('/api/vault/status').then(r=>r.json());out.textContent=s.configured?`Vault configured for ${s.username}. Status: ${s.unlocked?'Unlocked':'Locked'}.\n${s.algorithm}`:'Vault not configured. Create one to enable authenticated GitHub access.';}catch(e){out.textContent='Vault status failed: '+e.message;}}
function updateVaultForm(){const username=$('#vaultUsername')?.value.trim()||'';const token=$('#vaultToken')?.value.trim()||'';const password=$('#vaultPassword')?.value||'';const confirmation=$('#vaultConfirm')?.value||'';const acknowledged=Boolean($('#vaultConfirmAcknowledgement')?.checked);const url=$('#vaultProfileUrl');if(url){let login=username.replace(/^https?:\/\/github\.com\//i,'').split(/[/?#]/)[0];url.value=login?'https://github.com/'+login:'';}const setup=$('#vaultSetup');if(setup)setup.disabled=!(username&&token&&password.length>=12&&password===confirmation&&acknowledged);}
function wireVaultForm(){['vaultUsername','vaultToken','vaultPassword','vaultConfirm','vaultConfirmAcknowledgement'].forEach(id=>$('#'+id)?.addEventListener('input',updateVaultForm));$('#vaultConfirmAcknowledgement')?.addEventListener('change',updateVaultForm);updateVaultForm();}
async function setupVault(){const out=$('#vaultResult');const body={username:$('#vaultUsername')?.value||'',token:$('#vaultToken')?.value||'',password:$('#vaultPassword')?.value||'',confirmation:$('#vaultConfirm')?.value||'',confirmed:Boolean($('#vaultConfirmAcknowledgement')?.checked)};if(!confirm('Are you certain you can remember your Angel Platform master password or have a secure copy stored safely?'))return;out.textContent='Creating encrypted vault and testing GitHub API…';try{const r=await fetch('/api/vault/setup',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const j=await r.json();if(!r.ok)throw Error(j.error||'Setup failed');out.textContent=j.result;setLiveMonitor(j.result,'Complete');}catch(e){out.textContent=e.message;setLiveMonitor(e.message,'Error');}}
async function testVault(){const out=$('#vaultResult');if(out)out.textContent='Testing GitHub API connection…';try{const r=await fetch('/api/vault/test',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const j=await r.json();if(!r.ok)throw Error(j.error||'GitHub API test failed');if(out)out.textContent=j.result;setLiveMonitor(j.result,'Complete');}catch(e){if(out)out.textContent=e.message;setLiveMonitor(e.message,'Error');}}
async function unlockVault(){const out=$('#vaultResult');const password=$('#vaultPassword')?.value||prompt('Enter your GitHub vault master password:');if(!password)return;out.textContent='Unlocking vault…';try{const r=await fetch('/api/vault/unlock',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password})});const j=await r.json();if(!r.ok)throw Error(j.error||'Unlock failed');out.textContent=j.result;setLiveMonitor(j.result,'Complete');}catch(e){out.textContent=e.message;setLiveMonitor(e.message,'Error');}}
async function lockVault(){const out=$('#vaultResult');try{const r=await fetch('/api/vault/lock',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});const j=await r.json();out.textContent=j.result;setLiveMonitor(j.result,'Complete');}catch(e){out.textContent=e.message;}}
function clearVaultForm(){['vaultUsername','vaultProfileUrl','vaultToken','vaultPassword','vaultConfirm'].forEach(id=>{const el=$('#'+id);if(el)el.value='';});const acknowledgement=$('#vaultConfirmAcknowledgement');if(acknowledgement)acknowledgement.checked=false;updateVaultForm();}
async function removeVault(mode){const out=$('#vaultResult');const label=mode==='reset'?'reset':'delete';const password=$('#vaultPassword')?.value||prompt('Enter your GitHub vault master password:');if(!password)return;const confirmation=prompt('Type '+(mode==='reset'?'RESET':'DELETE')+' to permanently remove the local GitHub vault:','');if(!confirmation)return;if(!confirm('This removes only Angel’s local GitHub credentials and encrypted vault files. Continue?'))return;if(out)out.textContent='Removing GitHub credentials…';try{const r=await fetch('/api/vault/'+label,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({password,confirmation})});const j=await r.json();if(!r.ok)throw Error(j.error||'Vault removal failed');clearVaultForm();if(out)out.textContent=j.result;setLiveMonitor(j.result,'Complete');await loadVaultStatus();}catch(e){if(out)out.textContent=e.message;setLiveMonitor(e.message,'Error');}}
function setLiveMonitor(text,state='Idle'){const panel=$('#liveHero'),out=$('#liveOutput'),label=$('#liveState');if(out)out.textContent=text;if(label)label.textContent=state;if(panel)panel.classList.toggle('running',state==='Running');}
async function action(name,payload={}){const out=document.querySelector('#toolResult,#healthResult,#workspaceResult,#devopsResult,#policyResult,#memoryResult,#providerResult,#settingsResult,#moduleRunResult');const friendly=name.replaceAll('_',' ');if(out)out.textContent='Running '+friendly+'…';setLiveMonitor('> Starting '+friendly+'…\n> Connecting to Angel Nexus action service…','Running');try{const response=await fetch('/api/action',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({action:name,...payload})});if(!response.ok)throw Error('HTTP '+response.status);const j=await response.json();const result=j.result||'Completed.';if(out)out.textContent=result;setLiveMonitor('> Action: '+friendly+'\n> Status: Completed\n\n'+result,'Complete');refreshActivity()}catch(e){const msg='Action failed: '+e.message;if(out)out.textContent=msg;setLiveMonitor('> Action: '+friendly+'\n> Status: Failed\n\n'+msg,'Error');if(!out) addMessage('Angel AI',msg)}}
async function refreshStatus(){try{const s=await fetch('/api/status').then(r=>r.json());$('#ollamaState').textContent=s.ollama?'● Connected':'● Offline';$('#ollamaStatusLine').textContent=s.ollama?'◦ Ollama: Connected':'◦ Ollama: Offline';$('#engineState').textContent=s.ollama?'Ollama':'Offline';setLiveMonitor(s.ollama?'Ollama connected. Live Nexus monitor ready.':'Ollama offline. Live Nexus monitor ready for local actions.','Idle');$('#moduleCount').textContent=s.modules+' Registered'}catch(e){$('#ollamaState').textContent='● Offline';$('#ollamaStatusLine').textContent='◦ Ollama: Offline';$('#engineState').textContent='Offline'}}
async function refreshActivity(){const j=await fetch('/api/activity').then(r=>r.json());$('#activity').innerHTML=j.activity.map(x=>`<p>◉ ${esc(x.message)} <small>${esc(x.time)}</small></p>`).join('')||'<p>No activity yet.</p>'}
$('#send').onclick=send;
$('#newChat')?.addEventListener('click',startNewChat);$('#newChatSide')?.addEventListener('click',startNewChat);
$('#stopReading').onclick=stopReading;
$('#stopReading').disabled=true;
$('#prompt').addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send()}});
$('#voice').onclick=()=>{const R=window.SpeechRecognition||window.webkitSpeechRecognition;if(!R)return alert('Voice input is not available in this browser.');const r=new R();r.onresult=e=>$('#prompt').value=e.results[0][0].transcript;r.start()};
$('#nexusCommand').onclick=()=>{const x=prompt('Ask Nexus to inspect (system_health, module_scan, tool_inventory):','system_health');if(x)action(x)};
document.querySelectorAll('[data-page]').forEach(b=>b.onclick=()=>renderPage(b.dataset.page));
refreshStatus();refreshActivity();renderConversationHistory();loadPersistentServerHistory();
