const fs = require('fs');
const vm = require('vm');
const assert = require('assert/strict');
const timers = new Map();
let timerId = 0;
let now = 10000;
const context = { Date: {now: () => now}, window: {
  setTimeout: fn => { timers.set(++timerId, fn); return timerId; },
  clearTimeout: id => timers.delete(id)
}, Zotero: {Server: {Endpoints: {}}, Integration: {}, Utilities: {randomString: () => 'request-' + (++timerId)}} };
vm.createContext(context);
vm.runInContext(fs.readFileSync(__dirname + '/src/zotero-bridge.js', 'utf8'), context);
const bridge = context.wpsEasyCite;
bridge.start();
function call(name, data = {}, token = '__BRIDGE_TOKEN__') {
  return new context.Zotero.Server.Endpoints['/wps-easier-citation/' + name]().init({data:{token,...data}});
}
function body(result) { assert.equal(result[0], 200); return JSON.parse(result[2]); }
(async () => {
  assert.equal(call('poll', {}, 'wrong'), 403);
  await assert.rejects(bridge.execute(), /未连接/);
  body(call('poll', {client:'wps1',document:'doc1'}));
  let task = bridge.execute();
  await assert.rejects(bridge.execute(), /正在进行/);
  const request = body(call('poll', {client:'wps1',document:'doc1'}));
  assert.equal(request.document, 'doc1');
  assert.equal(call('claim',{client:'wps2',id:request.id,document:'doc1',integrationId:'http1'}),409);
  body(call('claim',{client:'wps1',id:request.id,document:'doc1',integrationId:'http1'}));
  assert.deepEqual(body(call('poll',{client:'wps1',document:'doc1'})),{});
  assert.equal(call('claim',{client:'wps1',id:request.id,document:'doc1',integrationId:'http1'}),409);
  context.Zotero.Integration.currentDoc = {_documentID:'other'};
  assert.equal(bridge.ownsCurrentDocument(),false);
  context.Zotero.Integration.currentDoc = {_documentID:'http1'};
  assert.equal(bridge.ownsCurrentDocument(),true);
  body(call('done',{client:'wps1',id:request.id,ok:true}));
  await task;
  context.Zotero.Integration.currentDoc = null;
  task = bridge.execute();
  const switched = assert.rejects(task,/文档已切换/);
  body(call('poll',{client:'wps1',document:'doc2'}));
  await switched;
  task = bridge.execute();
  const expired = assert.rejects(task,/及时响应/);
  [...timers.values()][0]();
  await expired;
  body(call('poll',{client:'wps2',document:'doc3'}));
  await assert.rejects(bridge.execute(),/多个 WPS/);
  now += 7000;
  await assert.rejects(bridge.execute(),/未连接/);
  bridge.stop();
  assert.equal(Object.keys(context.Zotero.Server.Endpoints).length,0);
  console.log('PASS: authorization, unavailable WPS, concurrency, ownership, duplicate claim, document switch, timeout, stale clients, cleanup');
})().catch(error => {console.error(error);process.exitCode=1;});
