const $=id=>document.getElementById(id), E=GlowbeEngine;
let state={version:1,length:16,bpm:120,division:2,glowbes:[]};
for(let x=1;x<7;x++)state.glowbes.push({x,y:3,steps:E.pattern('wave',x,3,x,16)});
let selected='1,3',step=0,playing=false,anchor=0;
const key=g=>`${g.x},${g.y}`;
function message(text){$('status').textContent=text;}
function render(){
 $('count').textContent=`${state.glowbes.length} Glowbes`;
 $('remove').disabled=!state.glowbes.some(g=>key(g)===selected);
 $('grid').replaceChildren();
 for(let y=0;y<8;y++)for(let x=0;x<8;x++){
  const g=state.glowbes.find(g=>g.x===x&&g.y===y),b=document.createElement('button');
  b.className=`tile ${g?'occupied':''} ${selected===`${x},${y}`?'selected':''}`;
  b.style.left=`${50+(x-y)*5.8}%`;b.style.top=`${16+(x+y)*4.5}%`;
  b.setAttribute('aria-label',`${g?'Select Glowbe':'Place Glowbe'} at ${x+1}, ${y+1}`);
  if(g){b.dataset.glowbe=key(g);const orb=document.createElement('span');orb.className='orb';b.append(orb);}
  b.onclick=()=>{if(!g)state.glowbes.push({x,y,steps:Array(state.length).fill(false)});selected=`${x},${y}`;render();};
  $('grid').append(b);
 }
 const g=state.glowbes.find(g=>key(g)===selected);
 $('selected-label').textContent=g?`Light · Glowbe at ${g.x+1}, ${g.y+1}`:'Select or place a Glowbe to edit its lights.';
 $('timeline').replaceChildren();
 if(g)g.steps.forEach((on,s)=>{
  const cell=document.createElement('div'),bulb=document.createElement('button'),preview=document.createElement('button');
  cell.className='light-step';cell.dataset.step=s;
  bulb.className=`bulb-toggle ${on?'on':''}`;
  bulb.setAttribute('aria-pressed',String(on));
  bulb.setAttribute('aria-label',`Step ${s+1}: light ${on?'on':'off'}`);
  bulb.innerHTML='<svg viewBox="0 0 32 40" aria-hidden="true"><path class="bulb-glass" d="M10 27v-3C10 20 5 18 5 12a11 11 0 0 1 22 0c0 6-5 8-5 12v3Z"/><path d="M11 31h10M12 35h8M14 38h4M12 14l4 4 4-4M16 18v9"/></svg>';
  bulb.onclick=()=>{g.steps[s]=!g.steps[s];bulb.classList.toggle('on',g.steps[s]);bulb.setAttribute('aria-pressed',String(g.steps[s]));bulb.setAttribute('aria-label',`Step ${s+1}: light ${g.steps[s]?'on':'off'}`);paint();};
  preview.className='step-preview';preview.textContent=s+1;preview.setAttribute('aria-label',`Preview step ${s+1}`);preview.onclick=()=>{pause();step=s;paint();};
  cell.append(bulb,preview);$('timeline').append(cell);
 });
 paint();
}
function paint(){
 document.querySelectorAll('[data-glowbe]').forEach(b=>b.classList.toggle('lit',state.glowbes.find(g=>key(g)===b.dataset.glowbe)?.steps[step]||false));
 document.querySelectorAll('[data-step]').forEach(c=>c.classList.toggle('current',Number(c.dataset.step)===step));
 $('position').textContent=`Step ${step+1} / ${state.length}`;
}
function pause(){playing=false;$('play').textContent='Play';}
function reanchor(){anchor=performance.now()-step*60000/(state.bpm*state.division);}
$('play').onclick=()=>{if(playing)pause();else{playing=true;reanchor();$('play').textContent='Pause';}};
$('reset').onclick=()=>{step=0;reanchor();paint();};
function frame(now){if(playing){const next=E.stepAt(now-anchor,state.bpm,state.division,state.length);if(next!==step){step=next;paint();}}requestAnimationFrame(frame);}
requestAnimationFrame(frame);
$('bpm').onchange=()=>{state.bpm=Math.max(20,Math.min(300,Number($('bpm').value)||120));$('bpm').value=state.bpm;reanchor();};
$('division').onchange=()=>{state.division=Number($('division').value);reanchor();};

$('remove').onclick=()=>{state.glowbes=state.glowbes.filter(g=>key(g)!==selected);selected=null;render();};
$('apply').onclick=()=>{state.glowbes.forEach((g,i)=>g.steps=E.pattern($('preset').value,g.x,g.y,i,state.length));render();message('Pattern applied to all placed Glowbes.');};
$('save').onclick=()=>{const url=URL.createObjectURL(new Blob([JSON.stringify(state,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='glowbe-pattern.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);message('Pattern saved. Load this file to continue later.');};
$('load').onclick=()=>$('file').click();
$('file').onchange=async()=>{const file=$('file').files[0];if(!file)return;try{if(file.size>100000)throw Error('Pattern file is too large.');const next=E.validate(JSON.parse(await file.text()));if(next.length!==16)throw Error("This editor uses 16-step patterns. Your file has "+next.length+" steps; it has not been changed.");pause();state=next;step=0;selected=state.glowbes[0]?key(state.glowbes[0]):null;for(const id of ['bpm','division','length'])$(id).value=state[id];render();message('Pattern loaded.');}catch(error){message(`Could not load: ${error.message}`);}$('file').value='';};
render();
// Optional browser-agent access uses exactly the same validated pattern format.
if(document.modelContext?.registerTool){
 const lifecycle=new AbortController();
 window.addEventListener('pagehide',()=>lifecycle.abort(),{once:true});
 try{Promise.resolve(document.modelContext.registerTool({
  name:'set_glowbe_pattern',description:'Replace the placement and lighting loop with a validated version-1 Glowbe pattern.',
  inputSchema:{type:'object',properties:{pattern:{type:'object'}},required:['pattern'],additionalProperties:false},
  annotations:{readOnlyHint:false},
  execute(input){const next=E.validate(input.pattern);if(next.length!==16)throw Error("This editor requires a 16-step pattern.");pause();state=next;step=0;selected=state.glowbes[0]?key(state.glowbes[0]):null;for(const id of ['bpm','division','length'])$(id).value=state[id];render();return {glowbes:state.glowbes.length,steps:state.length};}
 },{signal:lifecycle.signal})).catch(()=>{});}catch{}
}
