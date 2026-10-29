const assert = require('assert/strict');
const fs = require('fs');
const vm = require('vm');
function harness() {
  let interval, pendingPoll, key='doc1', claimed=true;
  const calls=[];
  const context={console,makeId:()=> 'wps1',zc_clearRegistry:()=>calls.push('clear'),
    zc_bind:()=>({id:'http1',command:c=>{calls.push(c);return true;}}),
    Application:{Documents:{Count:1},get ActiveDocument(){return {DocID:key,FullName:key};}},
    window:{setInterval:fn=>{interval=fn;return 1;}},
    XMLHttpRequest:class {
      open(method,url,async){this.url=url;this.async=async;}
      setRequestHeader(){}
      send(raw){
        this.data=JSON.parse(raw);
        if(this.url.endsWith('/poll')){pendingPoll=this;return;}
        if(this.url.endsWith('/claim'))this.status=claimed?200:409;
        if(this.url.endsWith('/done'))calls.push({done:this.data});
      }
    }
  };
  vm.createContext(context);vm.runInContext(fs.readFileSync(__dirname+'/src/wps-bridge.js','utf8'),context);
  context.startWpsEasyCite();
  return {calls, poll:()=>interval(), change:k=>key=k, reject:()=>claimed=false,
    deliver:(id='r1',document='doc1:doc1')=>{pendingPoll.status=200;pendingPoll.responseText=JSON.stringify({id,document});pendingPoll.onload();}};
}
const a=harness();a.deliver();
assert.equal(a.calls.filter(x=>x==='addEditCitation').length,1);
assert.equal(a.calls.find(x=>x.done).done.ok,true);
a.poll();a.deliver();assert.equal(a.calls.filter(x=>x==='addEditCitation').length,1);
const b=harness();b.change('doc2');b.deliver();assert.equal(b.calls.length,0);
const c=harness();c.reject();c.deliver();assert.deepEqual(c.calls,['clear']);
console.log('PASS: WPS insertion, completion, no replay, document switch, rejected claim');
