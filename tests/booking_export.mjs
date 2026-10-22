import assert from 'node:assert/strict';
import {readFileSync} from 'node:fs';
import vm from 'node:vm';
const html=readFileSync(0,'utf8');
const payload=html.match(/<script type="application\/json" id="report">([\s\S]*?)<\/script>/)[1];
const script=html.match(/<script>([\s\S]*?)<\/script>/)[1];
const elements={report:{textContent:payload},download:{},status:{}};
let blob, clicked=false;
vm.runInNewContext(script,{
  document:{getElementById:id=>elements[id],querySelectorAll:()=>[],
    createElement:()=>({click(){clicked=true;}})},
  Blob,URL:{createObjectURL(value){blob=value;return 'blob:local';},revokeObjectURL(){}},
  setTimeout(fn){fn();}
});
elements.download.onclick();
assert.ok(clicked);
const text=await blob.text();
assert.ok(!text.includes('14:00'));
assert.ok(!text.includes('12:00'));
process.stdout.write(text);
