// Local Linux WPS adapter for Easier Citation 0.5.11.
// TOKEN is generated during packaging, and is never sent outside loopback.
var wpsEasyCite = (() => {
  const token = '__BRIDGE_TOKEN__';
  const prefix = '/wps-easier-citation/';
  const clients = new Map();
  const endpoints = new Map();
  let pending = null;
  function finish(error) {
    if (!pending) return;
    const task = pending;
    pending = null;
    window.clearTimeout(task.timer);
    error ? task.reject(new Error(error)) : task.resolve();
  }
  function reply(data) { return [200, 'application/json', JSON.stringify(data)]; }
  function register(name, handler) {
    const path = prefix + name;
    if (Zotero.Server.Endpoints[path]) throw new Error('WPS adapter endpoint already registered');
    const Endpoint = function () {};
    Endpoint.prototype = {
      supportedMethods: ['POST'], supportedDataTypes: ['application/json'],
      permitBookmarklet: false,
      init(request) {
        const data = request.data;
        if (!data || data.token !== token) return 403;
        return handler(data);
      }
    };
    endpoints.set(path, Endpoint);
    Zotero.Server.Endpoints[path] = Endpoint;
  }
  function start() {
    register('poll', data => {
      if (typeof data.client !== 'string' || typeof data.document !== 'string') return 400;
      clients.set(data.client, { document: data.document, seen: Date.now() });
      for (const [id, client] of clients) if (Date.now() - client.seen > 6000) clients.delete(id);
      if (pending && !pending.claimed && pending.client === data.client) {
        if (data.document !== pending.document) {
          finish('WPS 当前文档已切换。请重新定位光标后再按快捷键。');
          return reply({});
        }
        return reply({ id: pending.id, document: pending.document });
      }
      return reply({});
    });
    register('claim', data => {
      if (!pending || pending.claimed || pending.client !== data.client || pending.id !== data.id
          || pending.document !== data.document || !data.integrationId) return 409;
      if (Zotero.Integration.currentDoc) {
        finish('Zotero 正在处理其他引用操作，请完成后重试。');
        return 409;
      }
      pending.claimed = String(data.integrationId);
      window.clearTimeout(pending.timer);
      pending.timer = window.setTimeout(() => finish('引用操作等待超时。请检查 WPS 和 Zotero 对话框；确认文档结果后再重试。'), 180000);
      return reply({ accepted: true });
    });
    register('done', data => {
      if (!pending || pending.id !== data.id || pending.client !== data.client || !pending.claimed) return 409;
      finish(data.ok === true ? null : 'WPS 未完成引用插入。请检查文档是否可编辑及 Zotero 的提示。');
      return reply({ accepted: true });
    });
  }
  function execute() {
    if (pending) return Promise.reject(new Error('已有引用操作正在进行。'));
    const live = [...clients].filter(([, c]) => c.document && Date.now() - c.seen < 6000);
    if (!live.length) return Promise.reject(new Error('未连接到 WPS 文档。请打开 WPS 文档、定位光标，等待两秒后重试。'));
    if (live.length > 1) return Promise.reject(new Error('检测到多个 WPS 插件实例。请仅保留目标 WPS 窗口后再使用快捷键。'));
    const [client, info] = live[0];
    return new Promise((resolve, reject) => {
      pending = { client, document: info.document, id: Zotero.Utilities.randomString(24), resolve, reject, claimed: null };
      pending.timer = window.setTimeout(() => finish('WPS 没有及时响应，请确认文档已打开且没有对话框遮挡。'), 10000);
    });
  }
  function ownsCurrentDocument() {
    return Boolean(pending?.claimed && Zotero.Integration.currentDoc?._documentID === pending.claimed);
  }
  function stop() {
    finish('WPS 引用适配已停止。');
    for (const [path, Endpoint] of endpoints) if (Zotero.Server.Endpoints[path] === Endpoint) delete Zotero.Server.Endpoints[path];
    endpoints.clear();
    clients.clear();
  }
  return { start, execute, ownsCurrentDocument, stop };
})();
