// Receives Easier Citation requests from the local Zotero instance.
function startWpsEasyCite() {
  if (window.wpsEasyCiteTimer) return;
  const token = '__BRIDGE_TOKEN__';
  const clientId = makeId(32);
  const base = 'http://127.0.0.1:21931/wps-easier-citation/';
  let polling = false;
  let lastRequest = null;
  function documentKey() {
    try {
      if (!Application.Documents.Count) return '';
      const doc = Application.ActiveDocument;
      return String(doc.DocID) + ':' + doc.FullName;
    } catch (_) { return ''; }
  }
  function send(name, data, callback, synchronous) {
    const xhr = new XMLHttpRequest();
    xhr.open('POST', base + name, !synchronous);
    xhr.setRequestHeader('Content-Type', 'application/json');
    if (!synchronous) {
      xhr.timeout = 3500;
      xhr.onload = () => callback(xhr.status, xhr.responseText);
      xhr.onerror = xhr.ontimeout = () => callback(0, '');
    }
    xhr.send(JSON.stringify(Object.assign({ token: token, client: clientId }, data)));
    return xhr;
  }
  function poll() {
    if (polling) return;
    const key = documentKey();
    polling = true;
    try {
      send('poll', { document: key }, (status, text) => {
        try {
          if (status !== 200) return;
          const task = JSON.parse(text);
          if (!task.id || task.id === lastRequest || task.document !== documentKey()) return;
          const bound = zc_bind();
          try {
            const claim = send('claim', { id: task.id, document: key, integrationId: bound.id }, null, true);
            if (claim.status !== 200) return;
            lastRequest = task.id; // Never replay a request, even after an ambiguous response.
            let ok = false;
            try { ok = bound.command('addEditCitation') === true; }
            finally { send('done', { id: task.id, ok: ok }, function () {}, false); }
          } finally { zc_clearRegistry(); }
        } catch (error) { console.error('WPS Easier Citation:', error); }
        finally { polling = false; }
      }, false);
    } catch (_) { polling = false; }
  }
  window.wpsEasyCiteTimer = window.setInterval(poll, 1500);
  poll();
}
