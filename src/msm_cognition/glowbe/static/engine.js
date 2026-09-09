/* Shared pure timing and file-validation logic, also exercised by Node tests. */
(function(root){
  const api = {
    stepAt(elapsed,bpm,division,length){return Math.floor(elapsed*bpm*division/60000)%length;},
    pattern(kind,x,y,index,length){return Array.from({length},(_,s)=>kind==='wave'?s%8===(x+y)%8:kind==='chase'?s===index%length:kind==='pulse'?s%4<2:kind==='alternate'?s%2===(x+y)%2:false);},
    validate(data){
      if(!data||data.version!==1||![8,16,32].includes(data.length)||!Number.isFinite(data.bpm)||data.bpm<20||data.bpm>300||![1,2,4].includes(data.division)||!Array.isArray(data.glowbes)||data.glowbes.length>64)throw Error('This is not a valid Glowbe pattern file.');
      const seen=new Set();
      const glowbes=data.glowbes.map(g=>{
        if(!g||!Number.isInteger(g.x)||!Number.isInteger(g.y)||g.x<0||g.x>7||g.y<0||g.y>7||!Array.isArray(g.steps)||g.steps.length!==data.length||g.steps.some(s=>typeof s!=='boolean')||seen.has(`${g.x},${g.y}`))throw Error('Invalid placement or lighting steps.');
        seen.add(`${g.x},${g.y}`);return {x:g.x,y:g.y,steps:[...g.steps]};
      });
      return {version:1,length:data.length,bpm:data.bpm,division:data.division,glowbes};
    }
  };
  if(typeof module!=='undefined')module.exports=api;else root.GlowbeEngine=api;
})(globalThis);
