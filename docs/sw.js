/* Saray Döner – offline-Speicher. Seite und status.json: erst Netz, sonst Speicher. Rest: erst Speicher. */
var V='saray-14e7df49b9',VOR=["./", "css/style.css?v=9a3eff3d", "js/main.js?v=daf8fa0a", "fonts/Roboto-Slab-Bold.sub.woff", "fonts/Roboto-Slab-Regular.sub.woff", "fonts/lato-bold.sub.woff", "fonts/lato-normal.sub.woff", "img/saray-koch-kopf.svg", "img/saray-koch.svg"];
self.addEventListener('install',function(e){e.waitUntil(caches.open(V).then(function(c){return c.addAll(VOR);}).then(function(){return self.skipWaiting();}));});
self.addEventListener('activate',function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.filter(function(k){return k!==V&&k.indexOf('saray-')===0;}).map(function(k){return caches.delete(k);}));}).then(function(){return self.clients.claim();}));});
self.addEventListener('fetch',function(e){
  var r=e.request,u=new URL(r.url);
  if(r.method!=='GET'||u.origin!==location.origin||u.pathname.indexOf('/chef/')>-1||u.pathname.indexOf('/druck/')>-1)return;
  var seite=r.mode==='navigate',schluessel=seite?'./':r;
  if(seite||/status\.json$/.test(u.pathname)){
    e.respondWith(fetch(r).then(function(res){if(res.ok){var k=res.clone();caches.open(V).then(function(c){c.put(schluessel,k);});}return res;})
      .catch(function(){return caches.match(schluessel).then(function(m){return m||Response.error();});}));
    return;
  }
  e.respondWith(caches.match(r).then(function(m){return m||fetch(r).then(function(res){if(res.ok){var k=res.clone();caches.open(V).then(function(c){c.put(r,k);});}return res;});}));
});
