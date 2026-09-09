const assert=require('node:assert/strict');
const test=require('node:test');
const E=require('../src/msm_cognition/glowbe/static/engine.js');
test('timing advances at subdivisions and wraps',()=>{
 assert.equal(E.stepAt(249,120,2,16),0);
 assert.equal(E.stepAt(250,120,2,16),1);
 assert.equal(E.stepAt(4000,120,2,16),0);
 assert.equal(E.stepAt(1000,60,4,8),4);
});
const valid=()=>({version:1,bpm:120,division:2,length:8,glowbes:[{x:0,y:7,steps:Array(8).fill(false)}]});
test('file round trip copies data',()=>{const s=valid(),r=E.validate(JSON.parse(JSON.stringify(s)));assert.deepEqual(r,s);r.glowbes[0].steps[0]=true;assert.equal(s.glowbes[0].steps[0],false);});
test('rejects malformed files and duplicate positions',()=>{
 for(const patch of [{bpm:0},{division:3},{length:7},{glowbes:[{x:8,y:0,steps:Array(8).fill(false)}]},{glowbes:[{x:0,y:0,steps:Array(8).fill(1)}]}])assert.throws(()=>E.validate({...valid(),...patch}));
 const s=valid();s.glowbes.push(s.glowbes[0]);assert.throws(()=>E.validate(s));
});
test('wave moves along diagonals and chase wraps',()=>{
 assert.equal(E.pattern('wave',2,3,0,16)[5],true);
 assert.equal(E.pattern('wave',2,3,0,16)[6],false);
 assert.equal(E.pattern('chase',0,0,17,16)[1],true);
 assert.ok(E.pattern('off',0,0,0,32).every(s=>!s));
});
