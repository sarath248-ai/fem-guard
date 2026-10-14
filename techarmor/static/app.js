'use strict';
const $ = id => document.getElementById(id);
const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const csrf = document.querySelector('meta[name=csrf]').content;
let state = {cameras:[],incidents:[],audit:[],counts:{}};
let selectedId = null;
const titles = {overview:'Operations overview', incidents:'Incident queue', cameras:'Camera registry', lab:'Signal lab', audit:'Activity log'};
function toast(message) { $('toast').textContent = message; }
async function api(path, method='GET', data) {
 const response = await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},body:data === undefined ? undefined : JSON.stringify(data)});
 const body = await response.json();
 if(!response.ok) throw new Error(body.error || 'Request failed');
 return body;
}
function badge(value) {return `<span class="badge ${escape(value)}">${escape(value)}</span>`;}
function date(value) {return new Date(value).toLocaleString([], {month:'short',day:'numeric',hour:'2-digit',minute:'2-digit'});}
function cameraName(id) {return state.cameras.find(c=>c.id===id)?.name || `Camera ${id}`;}
function table(items) {
 if(!items.length) return '<div class="empty">No incidents here. Use the signal lab to test a scenario.</div>';
 return `<div class="table-wrap"><table><thead><tr><th>INCIDENT</th><th>ZONE</th><th>PRIORITY</th><th>SOURCE</th><th>TIME</th><th>STATUS</th><th>REVIEW</th></tr></thead><tbody>${items.map(i=>`<tr><td>#HT-${String(i.id).padStart(4,'0')}</td><td>${escape(cameraName(i.camera_id))}</td><td>${badge(i.level)}</td><td>${escape(i.source)}</td><td>${date(i.created_at)}</td><td>${badge(i.status)}</td><td><button data-incident="${i.id}">Open ↗</button></td></tr>`).join('')}</tbody></table></div>`;
}
function zones(manage=false) {
 return state.cameras.map(c=>`<article class="zone"><div class="zone-picture"><strong>▣</strong>NO VIDEO FEED CONNECTED</div><h3>${escape(c.name)} ${badge(c.status)}</h3><p>${escape(c.location)}</p><div class="zone-bottom"><span>${c.people} people · latest observation</span><span>CAM ${String(c.id).padStart(2,'0')}</span></div>${manage && document.querySelector('meta[name=role]').content==='admin' ? `<p><button data-camera="${c.id}" data-enabled="${!c.enabled}">${c.enabled?'Disable':'Enable'} zone</button></p>`:''}</article>`).join('') || '<div class="empty">Add your first camera.</div>';
}
function render() {
 const online=state.cameras.filter(c=>c.status==='online').length;
 const stats=[['Online zones',online,`${state.cameras.length} registered zones`],['High priority',state.counts.high||0,'Awaiting resolution'],['Review needed',state.counts.moderate||0,'Moderate priority events'],['Resolved',state.incidents.filter(i=>i.status==='resolved').length,'In latest 200 events']];
 $('stats').innerHTML=stats.map(([title,n,sub])=>`<article class="stat"><p>${title}</p><strong>${n.toString().padStart(2,'0')}</strong><small>${sub}</small></article>`).join('');
 $('zones').innerHTML=zones(); $('camera-list').innerHTML=zones(true); $('latest').innerHTML=table(state.incidents.slice(0,5));
 const filter=$('filter').value; $('queue').innerHTML=table(state.incidents.filter(i=>filter==='all'||i.status===filter||i.level===filter));
 const previous=$('signal-camera').value;
 $('signal-camera').innerHTML=state.cameras.filter(c=>c.enabled).map(c=>`<option value="${c.id}">${escape(c.name)}</option>`).join('');
 if([...$('signal-camera').options].some(o=>o.value===previous)) $('signal-camera').value=previous;
 $('audit-list').innerHTML=state.audit.length ? `<div class="table-wrap"><table><thead><tr><th>TIME</th><th>ACTOR</th><th>ACTION</th><th>DETAIL</th></tr></thead><tbody>${state.audit.map(a=>`<tr><td>${date(a.created_at)}</td><td>${escape(a.actor)}</td><td>${escape(a.action)}</td><td>${escape(a.detail)}</td></tr>`).join('')}</tbody></table></div>`:'<div class="empty">No activity yet.</div>';
 $('camera-form').classList.toggle('hidden',document.querySelector('meta[name=role]').content!=='admin');
}
async function refresh() {try{state=await api('/api/state');render();}catch(e){toast(e.message);}}
function showIncident(id) {
 const i=state.incidents.find(x=>x.id===id); if(!i) return;
 selectedId=id;
 $('detail-body').innerHTML=`<p class="eyebrow">INCIDENT / HT-${String(id).padStart(4,'0')}</p><h2>${escape(cameraName(i.camera_id))}</h2><div class="actions">${badge(i.level)} ${badge(i.status)} ${badge(i.source)}</div><dl><dt>Created</dt><dd>${date(i.created_at)}</dd><dt>Policy index</dt><dd>${i.score}/100</dd><dt>Reason</dt><dd>${i.reasons.map(escape).join('<br>')}</dd></dl><div class="detail-signals">${Object.entries(i.signals).map(([k,v])=>`<span class="pill">${escape(k)}: ${escape(v)}</span>`).join('')}</div><p class="muted small">Metadata only. No recorded CCTV, audio, or police dispatch is attached.</p>${i.note?`<p class="review-note">${escape(i.note)}</p>`:''}${i.status!=='resolved'?`<form id="review-form"><label>Review note<textarea id="note" minlength="3" maxlength="1000" required placeholder="Record the context and your decision"></textarea></label><button class="primary">${i.status==='open'?'Acknowledge incident':'Resolve incident'}</button></form>`:''}<p><a href="/api/incidents/${id}/export">Download metadata + SHA-256</a></p>`;
 if(!$('detail').open) $('detail').showModal();
 $('review-form')?.addEventListener('submit', async e=>{e.preventDefault();try{await api(`/api/incidents/${id}`,'PATCH',{status:i.status==='open'?'acknowledged':'resolved',note:$('note').value});await refresh();showIncident(id);}catch(err){toast(err.message);}});
}
document.addEventListener('click',async e=>{
 const view=e.target.closest('[data-view]'); if(view){document.querySelectorAll('.view').forEach(v=>v.classList.toggle('hidden',v.id!==view.dataset.view));document.querySelectorAll('nav button').forEach(b=>b.classList.toggle('active',b.dataset.view===view.dataset.view));$('page-title').textContent=titles[view.dataset.view];}
 const incident=e.target.closest('[data-incident]'); if(incident) showIncident(Number(incident.dataset.incident));
 const camera=e.target.closest('[data-camera]'); if(camera){try{await api(`/api/cameras/${camera.dataset.camera}`,'PATCH',{enabled:camera.dataset.enabled==='true'});await refresh();}catch(err){toast(err.message);}}
});
$('close-detail').onclick=()=>$('detail').close();
$('filter').onchange=render;
['gesture','scream','aggression'].forEach(k=>$(k).oninput=()=>$(k+'-value').value=Number($(k).value).toFixed(2));
$('preset').onclick=()=>{['gesture','scream','aggression'].forEach((k,n)=>{$(k).value=[.92,.89,.75][n];$(k).oninput();});$('manual').checked=false;};
$('signal-form').onsubmit=async e=>{e.preventDefault();if(!$('signal-camera').value){toast('Add an enabled camera first.');return;}const button=e.submitter;button.disabled=true;try{const r=await api('/api/simulate','POST',{camera_id:Number($('signal-camera').value),people:Number($('people').value),gesture:Number($('gesture').value),scream:Number($('scream').value),aggression:Number($('aggression').value),manual_sos:$('manual').checked});$('result').innerHTML=`<span class="signal-orb">◎</span>${badge(r.level)}<h2>${r.level==='low'?'No review threshold reached':'Incident queued for review'}</h2><p>Policy index ${r.score}/100</p><p class="muted">${r.reasons.map(escape).join('<br>')}</p><p class="small">Simulation · ${r.incident_id?'Incident #'+r.incident_id:'No incident created'}</p>`;toast('Scenario evaluated. No external alert was sent.');await refresh();}catch(err){toast(err.message);}finally{button.disabled=false;}};
$('camera-form').onsubmit=async e=>{e.preventDefault();try{await api('/api/cameras','POST',{name:$('camera-name').value,location:$('camera-location').value});e.target.reset();await refresh();toast('Monitoring zone added.');}catch(err){toast(err.message);}};
$('clock').textContent=new Date().toLocaleDateString([],{weekday:'short',month:'long',day:'numeric'});
refresh();setInterval(refresh,5000);
