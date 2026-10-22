"""Chef-App für den Inhaber: docs/chef/ (eine Seite, ohne fremde Bibliotheken).

Liest den Standard (docs/chef/standard.json, von build.py erzeugt) und die aktuellen Änderungen
(daten/anpassungen.json im Repo, über die GitHub-API) und schreibt Änderungen dorthin zurück.
Danach baut der GitHub-Workflow die Seite neu und veröffentlicht sie (ca. 2–3 Minuten).

Zugang: ein GitHub-Token (fine-grained, nur dieses Repo, „Contents: Read and write“, optional
„Actions: Read“ für die Fortschrittsanzeige). Einrichten über  …/chef/#token=<TOKEN>  – der Token
wird nur auf dem Gerät gespeichert (localStorage) und sofort aus der Adresse entfernt.
"""
import json

SEITE = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex, nofollow">
<title>Saray Chef</title>
<link rel="manifest" href="manifest.webmanifest">
<link rel="icon" href="../img/favicon-96.png" type="image/png">
<link rel="apple-touch-icon" href="../img/app-180.png">
<meta name="apple-mobile-web-app-title" content="Saray Chef">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="theme-color" content="#3A1531">
<style>
:root{--gelb:#FFD21F;--tinte:#3A1531;--paprika:#C8371A;--blass:#FFF3C2;--linie:#e6dbe2;--gruen:#1f7a3d}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:#f7f3f6;color:var(--tinte);font:400 17px/1.45 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif;
  padding-bottom:calc(150px + env(safe-area-inset-bottom))}
button,input,select,textarea{font:inherit;color:inherit}
header{position:sticky;top:0;z-index:20;background:var(--tinte);color:#fff;padding:calc(10px + env(safe-area-inset-top)) 16px 10px;
  display:flex;align-items:center;gap:10px}
header img{width:38px;height:38px}
header h1{margin:0;font-size:1.15rem}
header small{display:block;opacity:.75;font-size:.8rem}
main{max-width:720px;margin:0 auto;padding:14px 14px 0}
h2{font-size:1.3rem;margin:18px 4px 10px}
.karte{background:#fff;border-radius:16px;padding:14px;margin:0 0 12px;box-shadow:0 1px 0 var(--linie)}
.karte h3{margin:0 0 8px;font-size:1.08rem}
.reihe{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.knopf{min-height:48px;padding:0 16px;border-radius:12px;border:2px solid var(--tinte);background:#fff;font-weight:700;cursor:pointer}
.knopf.voll{background:var(--tinte);color:#fff}
.knopf.gelb{background:var(--gelb);border-color:var(--tinte)}
.knopf.rot{border-color:var(--paprika);color:var(--paprika)}
.knopf.rot.voll{background:var(--paprika);color:#fff}
.knopf.klein{min-height:40px;padding:0 12px;font-size:.92rem}
.knopf:disabled{opacity:.45}
.chip{display:inline-flex;align-items:center;gap:6px;min-height:36px;padding:0 6px 0 12px;border-radius:999px;background:var(--blass);
  border:1px solid #e9d78d;font-size:.92rem;font-weight:600}
.chip button{width:30px;height:30px;border:0;border-radius:50%;background:#fff;font-weight:700;cursor:pointer}
.chip.aus{background:#fde3dc;border-color:#f2b7a8}
.wahl{display:flex;gap:6px;flex-wrap:wrap}
.wahl button{min-height:44px;padding:0 14px;border-radius:999px;border:2px solid var(--tinte);background:#fff;font-weight:700}
.wahl button[aria-pressed=true]{background:var(--tinte);color:var(--gelb)}
label{display:block;font-weight:700;font-size:.92rem;margin:10px 0 4px}
input[type=text],input[type=date],input[type=search],select,textarea{width:100%;min-height:46px;border:2px solid #cdbfc8;border-radius:10px;padding:8px 10px;background:#fff}
input:focus,select:focus,textarea:focus{outline:3px solid var(--gelb);border-color:var(--tinte)}
/* iOS: Datumsfelder sonst breiter als die Karte */
input[type=date]{-webkit-appearance:none;appearance:none;display:block;min-width:0;max-width:100%}
input[type=date]::-webkit-date-and-time-value{text-align:left}
.reihe > div{min-width:0}
.karte > .reihe{margin-top:12px}
.hinweis{font-size:.9rem;opacity:.8;margin:6px 4px}
.fehler{color:var(--paprika);font-weight:700}
.liste-gericht{display:flex;align-items:center;gap:10px;width:100%;text-align:left;background:#fff;border:0;border-bottom:1px solid var(--linie);
  padding:12px 6px;min-height:56px;cursor:pointer}
.liste-gericht .nr{width:42px;flex:none;font-weight:700;opacity:.7}
.liste-gericht .nm{flex:1}
.liste-gericht .pr{font-weight:700;white-space:nowrap}
.liste-gericht.geloescht .nm{text-decoration:line-through;opacity:.5}
.marke{display:inline-block;margin-left:6px;padding:0 8px;border-radius:999px;font-size:.75rem;font-weight:700;background:var(--gelb);vertical-align:middle}
.marke.neu{background:#d6f0dc}.marke.weg{background:#fde3dc}
.abschnitt{margin:14px 4px 4px;font-weight:700;font-size:.85rem;text-transform:uppercase;letter-spacing:.05em;opacity:.7}
.tag{display:flex;gap:8px;align-items:center;padding:8px 4px;border-bottom:1px solid var(--linie)}
.tag strong{width:30px;flex:none}
.tag.anders{background:var(--blass);border-radius:8px}
.tag input[type=checkbox]{width:26px;height:26px;flex:none;margin:0}
.tag select{flex:1;min-width:0;min-height:44px;padding:4px 6px}
.tag .geschl{flex:1;opacity:.6;font-weight:700}
.schalter{display:flex;align-items:center;gap:8px;font-weight:700}
.schalter input{width:24px;height:24px}
nav.tabs{position:fixed;left:0;right:0;bottom:0;z-index:30;display:grid;grid-template-columns:repeat(4,1fr);background:#fff;
  border-top:1px solid var(--linie);padding-bottom:env(safe-area-inset-bottom)}
nav.tabs button{min-height:60px;border:0;background:none;font-weight:700;font-size:.85rem;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px}
nav.tabs button span{font-size:1.35rem;line-height:1}
nav.tabs button[aria-current=page]{color:var(--paprika)}
.speichern{position:fixed;left:10px;right:10px;bottom:calc(68px + env(safe-area-inset-bottom));z-index:31;display:flex;gap:10px;align-items:center;
  background:var(--gelb);border:2px solid var(--tinte);border-radius:16px;padding:8px 8px 8px 14px;box-shadow:0 10px 24px -10px rgba(58,21,49,.6)}
.speichern p{margin:0;flex:1;font-weight:700;font-size:.95rem;line-height:1.25}
.status{position:fixed;left:10px;right:10px;bottom:calc(68px + env(safe-area-inset-bottom));z-index:32;background:var(--tinte);color:#fff;
  border-radius:16px;padding:12px 14px;font-weight:700}
.status.ok{background:var(--gruen)}.status.rot{background:var(--paprika)}
.blatt{position:fixed;inset:0;z-index:50;background:rgba(58,21,49,.45);display:flex;align-items:flex-end;justify-content:center}
.blatt > div{background:#fff;width:100%;max-width:720px;max-height:92%;overflow:auto;border-radius:20px 20px 0 0;padding:18px 16px calc(18px + env(safe-area-inset-bottom))}
.blatt h3{margin:0 0 6px;font-size:1.2rem}
.blatt .reihe{margin-top:14px}
.gefahr-titel{color:var(--paprika)}
.karte.gefahr{border:2px solid var(--paprika);background:#fff7f4}
.checkliste summary{cursor:pointer;min-height:40px;display:flex;align-items:center;gap:4px;flex-wrap:wrap}
.cl-punkt{padding:8px 0;border-bottom:1px solid var(--linie)}
.karte.feiertag{border:2px solid var(--gelb);background:var(--blass)}
.foto-bereich{margin-top:14px;padding-top:10px;border-top:1px solid var(--linie)}
.foto-vorschau{display:block;width:100%;max-width:320px;aspect-ratio:4/3;object-fit:cover;border-radius:10px;margin:6px 0}
.foto-datei{position:absolute;width:1px;height:1px;opacity:0}
.gp-zeile{margin:8px 0}.gp-kopf{display:flex;justify-content:space-between;align-items:center;gap:8px;margin-bottom:4px}
.gp-zeile input,.gp-zeile textarea{width:100%;font-size:.95rem}
.cl-punkt .schalter{font-weight:700;align-items:flex-start}
.cl-punkt.erledigt .schalter span{text-decoration:line-through;opacity:.6}
.cl-punkt input[type=text]{margin-left:32px;width:calc(100% - 32px);min-height:40px}
table.zahlen{width:100%;border-collapse:collapse;margin:4px 0 10px}.zahlen th,.zahlen td{padding:7px 4px;border-bottom:1px solid var(--linie);text-align:right}
.zahlen th:first-child,.zahlen td:first-child{text-align:left}.zahlen th[scope=row]{text-align:left;font-weight:400}
.zahlen td{font-weight:700;font-variant-numeric:tabular-nums}.zahlen th[scope=col]{font-size:.78rem;white-space:nowrap;width:3.6em}
@media (max-width:360px){.zahlen{font-size:.9rem}}
.frueher{margin-top:12px;padding:8px 10px;background:var(--blass);border-radius:10px}.frueher .reihe{margin-top:6px}
a.knopf{color:inherit}
[hidden]{display:none!important}
</style>
</head>
<body>
<header><img src="../img/saray-koch-kopf.svg" alt=""><div><h1>Saray Chef</h1><small id="stand">Lädt …</small></div></header>
<main id="app"></main>
<div class="speichern" id="speichern" hidden><p id="speichern-text"></p>
  <button class="knopf klein" id="verwerfen">Verwerfen</button><button class="knopf voll" id="speichern-knopf">Speichern</button></div>
<div class="status" id="status" hidden></div>
<nav class="tabs" id="tabs" hidden>
  <button data-tab="heute" aria-current="page"><span>☀️</span>Heute</button>
  <button data-tab="karte"><span>📋</span>Karte</button>
  <button data-tab="zeiten"><span>🕑</span>Zeiten</button>
  <button data-tab="mehr"><span>⚙️</span>Mehr</button>
</nav>
<script>
(function(){
'use strict';
var REPO=%%REPO%%, DATEI='daten/anpassungen.json', API='https://api.github.com/repos/'+REPO;
var TK='saray-chef-token', STD=null, ANP={}, ALT='{}', SHA=null, TAB='heute', LADEN='alle', SUCHE='';
var app=document.getElementById('app');

/* ---------- Hilfen ---------- */
function el(tag,attrs,kinder){var e=document.createElement(tag);attrs=attrs||{};
  Object.keys(attrs).forEach(function(k){var v=attrs[k];if(v==null||v===false)return;
    if(k==='text')e.textContent=v;else if(k.slice(0,2)==='on')e.addEventListener(k.slice(2),v);else if(k==='class')e.className=v;else e.setAttribute(k,v===true?'':v);});
  (kinder||[]).forEach(function(c){if(c!=null)e.appendChild(typeof c==='string'?document.createTextNode(c):c);});return e;}
function heute(off){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+(off||0)*864e5));}
function datumDE(iso){var p=iso.split('-');return p[2]+'.'+p[1]+'.';}
function kopie(o){return JSON.parse(JSON.stringify(o));}
function b64enc(s){return btoa(unescape(encodeURIComponent(s)));}
function b64dec(s){return decodeURIComponent(escape(atob(s.replace(/\s/g,''))));}
function preisNorm(v){v=String(v).trim().replace('€','').trim().replace('.',',');if(/^\d{1,3}$/.test(v))v+=',00';if(/^\d{1,3},\d$/.test(v))v+='0';return /^\d{1,3},\d{2}$/.test(v)?v:null;}
function zeitListe(von,bis,schritt){var r=[];for(var m=von;m<=bis;m+=schritt)r.push(('0'+Math.floor(m/60)).slice(-2)+':'+('0'+m%60).slice(-2));return r;}
function frage(text,ja,nein){return new Promise(function(ok){var b=el('div',{class:'blatt'},[el('div',{},[el('h3',{text:text}),
  el('div',{class:'reihe'},[el('button',{class:'knopf',text:nein||'Abbrechen',onclick:function(){b.remove();ok(false);}}),
  el('button',{class:'knopf voll',text:ja||'Ja',onclick:function(){b.remove();ok(true);}})])])]);document.body.appendChild(b);});}
function status(text,art,dauer){var s=document.getElementById('status');s.textContent=text;s.className='status'+(art?' '+art:'');s.hidden=false;
  clearTimeout(status.t);if(dauer)status.t=setTimeout(function(){s.hidden=true;},dauer);}
function token(){try{return localStorage.getItem(TK)||'';}catch(e){return '';}}
function api(pfad,opt){opt=opt||{};opt.headers=Object.assign({'Accept':'application/vnd.github+json','Authorization':'Bearer '+token()},opt.headers||{});
  return fetch(pfad.indexOf('http')===0?pfad:API+pfad,opt);}

/* ---------- Daten ---------- */
function gerichte(){ /* aktuelle Karte = Standard + Änderungen, für die Anzeige */
  var res=[],ae=ANP.gerichte||{},weg=ANP.geloescht||[];
  STD.gruppen.forEach(function(g){g.abschnitte.forEach(function(a){
    a.gerichte.forEach(function(x){var o=ae[x.k]||{};res.push({k:x.k,g:g,a:a,nr:o.nr!=null?o.nr:x.nr,name:o.name!=null?o.name:x.name,desc:o.desc!=null?o.desc:x.desc,
      preise:o.preise||x.preise,std:x,geaendert:!!ae[x.k],geloescht:weg.indexOf(x.k)>-1,neu:false});});
    (ANP.neu||[]).forEach(function(n,i){if(n.gruppe===g.id&&n.abschnitt===a.titel)res.push({k:'neu:'+i,g:g,a:a,nr:n.nr||'',name:n.name,desc:n.desc||'',preise:n.preise,neu:true,index:i});});
  });});
  return res;
}
function schl(x){return x.neu?(x.nr||x.g.id+'|'+x.a.titel+'|'+x.name):x.k;}   /* gleicher Schlüssel wie build.py */
function preisSetzen(x,p){
  if(x.neu){ANP.neu[x.index].preise=p.slice();return;}
  ANP.gerichte=ANP.gerichte||{};var o=ANP.gerichte[x.k]||{};
  if(JSON.stringify(p)===JSON.stringify(x.std.preise))delete o.preise;else o.preise=p.slice();
  if(Object.keys(o).length)ANP.gerichte[x.k]=o;else delete ANP.gerichte[x.k];
}
function staende(){ /* [{name, preise:{schlüssel:[…]}, grund:true}] – Grundstand = gedruckte Karte */
  var grund={name:'Stand '+STD.grundstand,grund:true,preise:{}};
  STD.gruppen.forEach(function(g){g.abschnitte.forEach(function(a){a.gerichte.forEach(function(x){grund.preise[x.k]=x.preise;});});});
  return [grund].concat(ANP.staende||[]);
}
function aufraeumen(o){ /* leere Teile und abgelaufene Tagesregeln entfernen */
  var t=heute();
  if(o.verfuegbarkeit)o.verfuegbarkeit=o.verfuegbarkeit.filter(function(r){return !r.datum||r.datum>=t;});
  if(o.hinweise)o.hinweise=o.hinweise.filter(function(h){return h.bis>=t;});
  if(o.aktionen)o.aktionen=o.aktionen.filter(function(a){return a.bis>=t;});
  if(o.feiertage_ok)o.feiertage_ok=o.feiertage_ok.filter(function(d){return d>=t;});
  if(o.sonderzeiten)Object.keys(o.sonderzeiten).forEach(function(d){if(d<t||!Object.keys(o.sonderzeiten[d]).length)delete o.sonderzeiten[d];});
  if(o.wartezeit)Object.keys(o.wartezeit).forEach(function(l){var w=o.wartezeit[l];if(!w||w.datum<t||!w.min)delete o.wartezeit[l];});
  Object.keys(o).forEach(function(k){var v=o[k];if(v==null||(Array.isArray(v)&&!v.length)||(typeof v==='object'&&!Array.isArray(v)&&!Object.keys(v).length))delete o[k];});
  if(o.zeiten)Object.keys(o.zeiten).forEach(function(l){if(!Object.keys(o.zeiten[l]).length)delete o.zeiten[l];});
  if(o.zeiten&&!Object.keys(o.zeiten).length)delete o.zeiten;
  return o;
}
function geaendert(){return JSON.stringify(aufraeumen(kopie(ANP)))!==ALT;}
function zaehlen(){var a=aufraeumen(kopie(ANP)),b=JSON.parse(ALT),n=0;
  ['gerichte','zeiten','sonderzeiten','wartezeit','checkliste'].forEach(function(k){var x=a[k]||{},y=b[k]||{};Object.keys(Object.assign({},x,y)).forEach(function(i){if(JSON.stringify(x[i])!==JSON.stringify(y[i]))n++;});});
  ['geloescht','neu','verfuegbarkeit','hinweise','aktionen','staende','feiertage_ok'].forEach(function(k){var x=(a[k]||[]).map(JSON.stringify),y=(b[k]||[]).map(JSON.stringify);
    n+=x.filter(function(i){return y.indexOf(i)<0;}).length+y.filter(function(i){return x.indexOf(i)<0;}).length;});return n;}
function leiste(){var n=geaendert()?Math.max(1,zaehlen()):0;document.getElementById('speichern').hidden=!n;
  document.getElementById('speichern-text').textContent=(n===1?'1 Änderung':n+' Änderungen')+' – noch nicht gespeichert';}

/* ---------- Laden & Speichern ---------- */
function laden(){
  status('Lädt …');
  return Promise.all([fetch('standard.json',{cache:'no-store'}).then(function(r){return r.json();}),
    api('/contents/'+DATEI+'?ref=main',{cache:'no-store'})]).then(function(x){
    STD=x[0];var r=x[1];
    if(r.status===401||r.status===403)throw new Error('zugang');
    if(r.status===404){SHA=null;return {};}
    if(!r.ok)throw new Error('GitHub antwortet nicht ('+r.status+')');
    return r.json().then(function(d){SHA=d.sha;return JSON.parse(b64dec(d.content)||'{}');});
  }).then(function(d){ANP=d&&typeof d==='object'?d:{};ALT=JSON.stringify(aufraeumen(kopie(ANP)));
    document.getElementById('status').hidden=true;document.getElementById('tabs').hidden=false;
    document.getElementById('stand').textContent='Änderungen: '+(Object.keys(ANP).length?'vorhanden':'keine (Standard)');zeichnen();});
}
function speichern(nachricht){
  var neu=aufraeumen(kopie(ANP)),inhalt=JSON.stringify(neu,null,2)+'\n';
  status('Speichert …');
  var body={message:nachricht||('Chef-App: '+Math.max(1,zaehlen())+' Änderung(en)'),content:b64enc(inhalt),branch:'main'};if(SHA)body.sha=SHA;
  return api('/contents/'+DATEI,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}).then(function(r){
    if(r.status===409||r.status===422)throw new Error('konflikt');
    if(!r.ok)throw new Error('Speichern fehlgeschlagen ('+r.status+')');return r.json();
  }).then(function(d){SHA=d.content.sha;ANP=neu;ALT=JSON.stringify(neu);leiste();zeichnen();
    document.getElementById('stand').textContent='Änderungen: '+(Object.keys(ANP).length?'vorhanden':'keine (Standard)');
    beobachten(d.commit&&d.commit.sha);
  }).catch(function(e){
    if(e.message==='konflikt'){status('Jemand anderes hat inzwischen gespeichert. Bitte neu laden und noch einmal ändern.','rot');}
    else status(e.message+' – bitte später noch einmal versuchen.','rot');
  });
}
function beobachten(sha){ /* Fortschritt des GitHub-Workflows anzeigen (braucht „Actions: Read“) */
  var start=Date.now();status('Gespeichert ✓ Die Seite wird jetzt neu gebaut – ca. 2–3 Minuten …','ok');
  (function pruefen(){
    if(Date.now()-start>8*60e3){status('Gespeichert ✓ – Veröffentlichung dauert länger als üblich.','ok',8000);return;}
    api('/actions/runs?branch=main&per_page=5',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(d){
      if(!d){status('Gespeichert ✓ In ca. 3 Minuten ist die Seite aktuell.','ok',8000);return;}
      var run=(d.workflow_runs||[]).filter(function(w){return !sha||w.head_sha===sha;})[0];
      if(run&&run.status==='completed'){
        if(run.conclusion==='success')status('Online ✓ Die Seite ist aktuell.','ok',8000);
        else status('Veröffentlichen hat nicht geklappt. Bitte Michael Bescheid geben.','rot');
        return;}
      setTimeout(pruefen,10000);
    }).catch(function(){setTimeout(pruefen,15000);});
  })();
}

/* ---------- Ansichten ---------- */
function zeichnen(){app.textContent='';({heute:heuteTab,karte:karteTab,zeiten:zeitenTab,mehr:mehrTab})[TAB]();leiste();}

function regelText(r){var t=r.ab?'ab '+r.ab+' Uhr':r.bis?'bis '+r.bis+' Uhr':(r.datum?'aus':'dauerhaft aus');
  t+=r.datum?(r.datum===heute()?' (heute)':' ('+datumDE(r.datum)+')'):(r.ab||r.bis?' (jeden Tag)':'');
  if(r.laden)t+=' · '+(r.laden==='freital'?'Freital':'Altenberg');return t;}
function regelNeu(was,art,zeit,immer){var r={was:was};if(art==='ab')r.ab=zeit;if(!immer)r.datum=heute();if(LADEN!=='alle')r.laden=LADEN;
  ANP.verfuegbarkeit=(ANP.verfuegbarkeit||[]).filter(function(x){return !(x.was===was&&(x.laden||'alle')===LADEN);});
  ANP.verfuegbarkeit.push(r);zeichnen();}
function wartezeitKarte(){
  var t=heute(),k=el('div',{class:'karte'},[el('h3',{text:'Wartezeit heute'}),
    el('p',{class:'hinweis',text:'Bei viel Betrieb: Online-Bestellungen können erst später abgeholt werden. Gilt nur heute.'})]);
  STD.laeden.forEach(function(l){var w=(ANP.wartezeit||{})[l.id],akt=w&&w.datum===t?w.min:0;
    k.appendChild(el('p',{style:'margin:10px 0 4px;font-weight:700',text:l.name}));
    k.appendChild(el('div',{class:'wahl'},[0,15,30,45].map(function(m){
      return el('button',{'aria-pressed':String(akt===m),text:m?'+'+m+' Min.':'Normal',onclick:function(){
        ANP.wartezeit=ANP.wartezeit||{};if(m)ANP.wartezeit[l.id]={datum:t,min:m};else delete ANP.wartezeit[l.id];zeichnen();}});})));
  });
  return k;
}
function heuteTab(){
  var bald=offeneFeiertage(14);
  if(bald.length)app.appendChild(el('div',{class:'karte feiertag'},[el('b',{text:'📅 '+bald.map(function(f){return datumDE(f[0])+' '+f[1];}).join(', ')}),
    el('p',{class:'hinweis',style:'margin:4px 0 8px',text:'Öffnungszeiten für diesen Tag noch nicht festgelegt.'}),
    el('button',{class:'knopf klein voll',text:'Jetzt festlegen',onclick:function(){TAB='zeiten';[].forEach.call(document.querySelectorAll('[data-tab]'),function(x){if(x.dataset.tab==='zeiten')x.setAttribute('aria-current','page');else x.removeAttribute('aria-current');});zeichnen();window.scrollTo(0,0);}})]));
  app.appendChild(wartezeitKarte());
  app.appendChild(el('h2',{text:'Was gibt es heute nicht?'}));
  app.appendChild(el('div',{class:'karte'},[el('h3',{text:'Für welchen Laden?'}),
    el('div',{class:'wahl'},[['alle','Beide'],['freital','Freital'],['altenberg','Altenberg']].map(function(x){
      return el('button',{'aria-pressed':String(LADEN===x[0]),text:x[1],onclick:function(){LADEN=x[0];zeichnen();}});}))]));
  var t=heute();
  STD.sperren.forEach(function(g){
    var regeln=(ANP.verfuegbarkeit||[]).map(function(r,i){return {r:r,i:i};}).filter(function(x){return x.r.was===g.id&&(!x.r.datum||x.r.datum>=t);});
    var k=el('div',{class:'karte'},[el('h3',{text:g.name}),
      regeln.length?el('div',{class:'reihe'},regeln.map(function(x){return el('span',{class:'chip aus'},[regelText(x.r),
        el('button',{'aria-label':'Regel entfernen',text:'✕',onclick:function(){ANP.verfuegbarkeit.splice(x.i,1);zeichnen();}})]);})):el('p',{class:'hinweis',text:'Verfügbar'}),
      el('div',{class:'reihe',style:'margin-top:10px'},[
        el('button',{class:'knopf rot',text:'Heute aus',onclick:function(){regelNeu(g.id,'aus',null,false);}}),
        el('button',{class:'knopf',text:'Ab Uhrzeit …',onclick:function(){abUhrzeit(g);}}),
        el('button',{class:'knopf klein',text:'Dauerhaft aus',onclick:function(){frage(g.name+' dauerhaft aus? (bis Sie es wieder entfernen)','Dauerhaft aus').then(function(j){if(j)regelNeu(g.id,'aus',null,true);});}})])]);
    app.appendChild(k);
  });
  zutatenKarte();
}
function hinweisKarte(){ /* Hinweis-Band */
  var t=heute();
  app.appendChild(el('h2',{text:'Hinweis oben auf der Seite'}));
  var hk=el('div',{class:'karte'});
  (ANP.hinweise||[]).forEach(function(h,i){if(h.bis<t)return;hk.appendChild(el('p',{},[el('span',{class:'chip'},[h.text+' ('+datumDE(h.von)+'–'+datumDE(h.bis)+')',
    el('button',{'aria-label':'Hinweis entfernen',text:'✕',onclick:function(){ANP.hinweise.splice(i,1);zeichnen();}})])]));});
  var txt=el('input',{type:'text',id:'h-text',maxlength:'200',placeholder:'z. B. Heute ab 18 Uhr geschlossen'});
  var von=el('input',{type:'date',id:'h-von',value:t}),bis=el('input',{type:'date',id:'h-bis',value:t});
  hk.appendChild(el('label',{for:'h-text',text:'Neuer Hinweis'}));hk.appendChild(txt);
  hk.appendChild(el('div',{class:'reihe'},[el('div',{style:'flex:1'},[el('label',{for:'h-von',text:'von'}),von]),el('div',{style:'flex:1'},[el('label',{for:'h-bis',text:'bis'}),bis])]));
  hk.appendChild(el('div',{class:'reihe'},[el('button',{class:'knopf voll',text:'Hinweis hinzufügen',onclick:function(){
    if(!txt.value.trim()||!von.value||!bis.value||bis.value<von.value){status('Bitte Text und gültigen Zeitraum angeben.','rot',4000);return;}
    (ANP.hinweise=ANP.hinweise||[]).push({text:txt.value.trim(),von:von.value,bis:bis.value});zeichnen();}})]));
  app.appendChild(hk);
}
function zutatenKarte(){ /* einzelne Zutaten ausschalten – auf der Seite dann nicht wählbar */
  var t=heute();app.appendChild(el('h2',{text:'Zutaten'}));
  var k=el('div',{class:'karte'},[el('p',{class:'hinweis',style:'margin:0 0 8px',text:'Antippen = aus'+(LADEN==='alle'?' (beide Läden)':' in '+(LADEN==='freital'?'Freital':'Altenberg'))+', bis Sie es wieder einschalten. Ausgeschaltetes kann auf der Seite nicht gewählt werden. Pommes/Reis aus: Gerichte gibt es ohne diese Beilage, je 0,50 € günstiger. Noch einmal antippen = wieder da.'})]);
  STD.zutaten.forEach(function(gr){
    k.appendChild(el('p',{class:'abschnitt',style:'margin:10px 0 6px',text:gr[0]}));
    k.appendChild(el('div',{class:'reihe'},gr[1].map(function(z){
      var was='z:'+z,idx=(ANP.verfuegbarkeit||[]).map(function(r,i){return {r:r,i:i};}).filter(function(x){return x.r.was===was&&(x.r.laden||'alle')===LADEN&&(!x.r.datum||x.r.datum>=t);});
      var aus=idx.length>0;
      return el('button',{class:'knopf klein'+(aus?' rot voll':''),'aria-pressed':String(aus),'data-zutat':z,text:(aus?'✕ ':'')+z,onclick:function(){
        if(aus){var weg=idx.map(function(x){return x.i;});ANP.verfuegbarkeit=ANP.verfuegbarkeit.filter(function(_,i){return weg.indexOf(i)<0;});zeichnen();}
        else regelNeu(was,'aus',null,true);}});
    })));
  });
  app.appendChild(k);
}
function abUhrzeit(g){
  var sel=el('select',{id:'ab-zeit'},zeitListe(10*60,22*60,30).map(function(z){return el('option',{value:z,text:z+' Uhr'});}));sel.value='17:00';
  var immer=el('input',{type:'checkbox',id:'ab-immer'});
  var b=el('div',{class:'blatt'},[el('div',{},[el('h3',{text:g.name+' erst ab …'}),el('label',{for:'ab-zeit',text:'Uhrzeit'}),sel,
    el('label',{class:'schalter'},[immer,'jeden Tag (sonst nur heute)']),
    el('div',{class:'reihe'},[el('button',{class:'knopf',text:'Abbrechen',onclick:function(){b.remove();}}),
      el('button',{class:'knopf voll',text:'Übernehmen',onclick:function(){b.remove();regelNeu(g.id,'ab',sel.value,immer.checked);}})])])]);
  document.body.appendChild(b);
}

function slug(name,von){ /* gleiche Regel wie druck.py */
  var t=name.toLowerCase().replace(/ä/g,'ae').replace(/ö/g,'oe').replace(/ü/g,'ue').replace(/ß/g,'ss').replace(/[^a-z0-9]+/g,'-').replace(/^-+|-+$/g,'').slice(0,40).replace(/-+$/,'');
  return 'aktion-'+von+'-'+(t||'x');}
function aktionText(a){var t=a.name+' · '+datumDE(a.von)+'–'+datumDE(a.bis);
  if(a.tage&&a.tage.length)t+=' · '+a.tage.map(function(d){return TAGE[d];}).join(', ');
  if(a.zeit_ab)t+=' · '+a.zeit_ab+'–'+a.zeit_bis+' Uhr';
  if(a.laden)t+=' · nur '+(a.laden==='freital'?'Freital':'Altenberg');return t;}
function karteTab(){
  app.appendChild(el('h2',{text:'Sonderaktionen'}));
  var ak=el('div',{class:'karte'}),t=heute();
  (ANP.aktionen||[]).forEach(function(a,i){if(a.bis<t)return;
    ak.appendChild(el('p',{},[el('button',{class:'chip',style:'cursor:pointer;padding-right:12px','data-aktion':i,onclick:function(){aktionBearbeiten(i);}},[aktionText(a)])]));});
  if(!(ANP.aktionen||[]).some(function(a){return a.bis>=t;}))ak.appendChild(el('p',{class:'hinweis',style:'margin:0 0 8px',text:'Z. B. „Döner 5 €, Dürüm 6 €“ für eine Woche oder jeden Mittwoch. Die Seite zeigt den alten Preis durchgestrichen und rechnet mit dem Aktionspreis.'}));
  ak.appendChild(el('div',{class:'reihe'},[el('button',{class:'knopf voll',text:'+ Neue Aktion',onclick:function(){aktionBearbeiten(null);}})]));
  app.appendChild(ak);
  app.appendChild(el('h2',{text:'Speisekarte'}));
  var such=el('input',{type:'search',placeholder:'Name oder Nummer suchen',value:SUCHE,'aria-label':'Suchen',oninput:function(){SUCHE=such.value;liste();}});
  app.appendChild(el('div',{class:'reihe'},[el('div',{style:'flex:1'},[such]),el('button',{class:'knopf voll',text:'+ Neues Gericht',onclick:function(){bearbeiten(null);}})]));
  var box=el('div');app.appendChild(box);
  function liste(){box.textContent='';var q=SUCHE.trim().toLowerCase(),letzter='';
    gerichte().forEach(function(x){
      if(q&&(x.nr+' '+x.name).toLowerCase().indexOf(q)<0)return;
      var titel=x.g.titel+(x.a.titel&&x.a.titel!==x.g.titel?' · '+x.a.titel:'');
      if(titel!==letzter){box.appendChild(el('p',{class:'abschnitt',text:titel}));letzter=titel;}
      box.appendChild(el('button',{class:'liste-gericht'+(x.geloescht?' geloescht':''),'data-k':x.k,onclick:function(){bearbeiten(x);}},[
        el('span',{class:'nr',text:x.nr}),el('span',{class:'nm'},[x.name,x.neu?el('span',{class:'marke neu',text:'neu'}):null,
          x.geaendert&&!x.geloescht?el('span',{class:'marke',text:'geändert'}):null,x.geloescht?el('span',{class:'marke weg',text:'gelöscht'}):null]),
        el('span',{class:'pr',text:x.preise.join(' / ')+' €'})]));
    });}
  liste();
}
function bearbeiten(x){
  var neu=!x,abschnitte=[];STD.gruppen.forEach(function(g){g.abschnitte.forEach(function(a){abschnitte.push({g:g,a:a});});});
  var wahlAb=el('select',{id:'b-ab'},abschnitte.map(function(y,i){return el('option',{value:i,text:y.g.titel+(y.a.titel!==y.g.titel?' · '+y.a.titel:'')});}));
  var nr=el('input',{type:'text',id:'b-nr',value:x?x.nr:'',maxlength:'5',inputmode:'text'}),name=el('input',{type:'text',id:'b-name',value:x?x.name:'',maxlength:'80'});
  var desc=el('input',{type:'text',id:'b-desc',value:x?x.desc:'',maxlength:'200'}),preisBox=el('div');
  function preisFelder(){preisBox.textContent='';var a=x?x.a:abschnitte[+wahlAb.value].a,gr=a.groessen&&a.groessen.length?a.groessen:[''];
    gr.forEach(function(g,i){var f=el('input',{type:'text',inputmode:'decimal',id:'b-preis-'+i,value:x?x.preise[i]:'',placeholder:'z. B. 7,50'});
      preisBox.appendChild(el('label',{for:'b-preis-'+i,text:'Preis'+(g?' '+g:'')+' (€)'}));preisBox.appendChild(f);});}
  wahlAb.addEventListener('change',preisFelder);
  var fehler=el('p',{class:'fehler',hidden:true});
  var b=el('div',{class:'blatt'}),inhalt=el('div',{},[el('h3',{text:neu?'Neues Gericht':(x.nr?'Nr. '+x.nr+' ':'')+x.name}),
    neu?el('div',{},[el('label',{for:'b-ab',text:'Kategorie'}),wahlAb]):null,
    x&&!x.neu&&!x.std.nr?null:el('div',{},[el('label',{for:'b-nr',text:x&&!x.neu?'Nummer (muss frei sein; nur die angezeigte Nummer ändert sich)':'Nummer (optional, muss frei sein)'}),nr]),
    el('label',{for:'b-name',text:'Name'}),name,el('label',{for:'b-desc',text:'Beschreibung'}),desc,preisBox,fehler]);
  preisFelder();
  if(x){var frueher=staende().filter(function(st){var p=st.preise[schl(x)];return p&&JSON.stringify(p)!==JSON.stringify(x.preise);});
    if(frueher.length){var fb=el('div',{class:'frueher'},[el('label',{text:'Frühere Preise'})]);
      frueher.forEach(function(st){var p=st.preise[schl(x)];
        fb.appendChild(el('div',{class:'reihe'},[el('span',{style:'flex:1',text:st.name+': '+p.join(' / ')+' €'}),
          el('button',{class:'knopf klein',text:'Übernehmen',onclick:function(){[].forEach.call(preisBox.querySelectorAll('input'),function(f,i){f.value=p[i]||p[0];});}})]));});
      preisBox.after(fb);}}
  function uebernehmen(){
    var preise=[].map.call(preisBox.querySelectorAll('input'),function(f){return preisNorm(f.value);});
    if(!name.value.trim()){fehler.textContent='Bitte einen Namen eingeben.';fehler.hidden=false;return;}
    if(preise.some(function(p){return !p;})){fehler.textContent='Preis bitte so eingeben: 7,50';fehler.hidden=false;return;}
    if(neu||x.neu){var n=nr.value.trim();
      var belegt=gerichte().some(function(y){return (!x||y.k!==x.k)&&((y.nr&&y.nr===n)||(y.std&&y.std.nr===n));});
      if(n&&(belegt||!/^[0-9A-Za-z]{1,5}$/.test(n))){fehler.textContent='Nummer '+n+' ist schon vergeben oder ungültig.';fehler.hidden=false;return;}
      var ab=neu?abschnitte[+wahlAb.value]:{g:x.g,a:x.a},obj={gruppe:ab.g.id,abschnitt:ab.a.titel,nr:n,name:name.value.trim(),desc:desc.value.trim(),preise:preise};
      ANP.neu=ANP.neu||[];if(neu)ANP.neu.push(obj);else ANP.neu[x.index]=obj;
    }else{var s=x.std,o={};if(name.value.trim()!==s.name)o.name=name.value.trim();if(desc.value.trim()!==s.desc)o.desc=desc.value.trim();
      if(s.nr){var n2=nr.value.trim();
        if(n2!==s.nr){var belegt2=gerichte().some(function(y){return y.k!==x.k&&y.nr===n2;});
          if(!/^[0-9A-Za-z]{1,5}$/.test(n2)||belegt2){fehler.textContent='Nummer '+n2+' ist schon vergeben oder ungültig.';fehler.hidden=false;return;}
          o.nr=n2;}}
      if(JSON.stringify(preise)!==JSON.stringify(s.preise))o.preise=preise;
      ANP.gerichte=ANP.gerichte||{};if(Object.keys(o).length)ANP.gerichte[x.k]=o;else delete ANP.gerichte[x.k];}
    b.remove();zeichnen();}
  var knoepfe=[el('button',{class:'knopf',text:'Abbrechen',onclick:function(){b.remove();}})];
  if(x&&x.neu)knoepfe.push(el('button',{class:'knopf rot',text:'Löschen',onclick:function(){ANP.neu.splice(x.index,1);b.remove();zeichnen();}}));
  else if(x&&x.geloescht)knoepfe.push(el('button',{class:'knopf gelb',text:'Wieder anzeigen',onclick:function(){ANP.geloescht=ANP.geloescht.filter(function(k){return k!==x.k;});b.remove();zeichnen();}}));
  else if(x)knoepfe.push(el('button',{class:'knopf rot',text:'Löschen',onclick:function(){(ANP.geloescht=ANP.geloescht||[]).push(x.k);b.remove();zeichnen();}}));
  if(x&&x.geaendert)knoepfe.push(el('button',{class:'knopf klein',text:'Alles wie Stand '+STD.grundstand,onclick:function(){delete ANP.gerichte[x.k];b.remove();zeichnen();}}));
  if(!x||!x.geloescht)knoepfe.push(el('button',{class:'knopf voll',text:'Übernehmen',onclick:uebernehmen}));
  var fnr=x?(x.neu?x.nr:(x.std&&x.std.nr)):'';
  if(fnr&&(!x.neu||(JSON.parse(ALT).neu||[]).some(function(n){return n.nr===fnr;})))inhalt.appendChild(fotoBereich(fnr,x.name));
  inhalt.appendChild(el('div',{class:'reihe'},knoepfe));b.appendChild(inhalt);document.body.appendChild(b);name.focus();
}

/* ---------- Fotos der Gerichte: daten/fotos/nr-<Nummer>.jpg im Repo; die Seite zeigt sie verkleinert ---------- */
function fotoPfad(nr){return 'daten/fotos/nr-'+nr+'.jpg';}
function fotoSha(nr){return api('/contents/'+fotoPfad(nr)+'?ref=main',{cache:'no-store'}).then(function(r){
  if(r.status===404)return null;if(!r.ok)throw new Error('GitHub antwortet nicht ('+r.status+')');return r.json().then(function(d){return d.sha;});});}
function verkleinern(datei){ /* längste Seite 1600 px, JPEG – spart Speicher und Ladezeit */
  return new Promise(function(ok,nein){var url=URL.createObjectURL(datei),bild=new Image();
    bild.onload=function(){var f=Math.min(1,1600/Math.max(bild.naturalWidth,bild.naturalHeight)),c=document.createElement('canvas');
      c.width=Math.round(bild.naturalWidth*f);c.height=Math.round(bild.naturalHeight*f);c.getContext('2d').drawImage(bild,0,0,c.width,c.height);URL.revokeObjectURL(url);
      ok(c.toDataURL('image/jpeg',.85).split(',')[1]);};
    bild.onerror=function(){nein(new Error('Das Bild lässt sich nicht öffnen.'));};bild.src=url;});}
function fotoBereich(nr,name){
  var vorhanden=(STD.fotos||[]).indexOf(nr)>-1||fotoBereich.neu[nr];
  var vorschau=el('img',{class:'foto-vorschau',alt:'Foto '+name,hidden:!vorhanden});
  if(fotoBereich.neu[nr])vorschau.src='data:image/jpeg;base64,'+fotoBereich.neu[nr];else if(vorhanden)vorschau.src='../img/gerichte/nr-'+nr+'-400.webp?'+Date.now();
  var eingabe=el('input',{type:'file',accept:'image/*',id:'foto-datei',class:'foto-datei'}),meldung=el('p',{class:'hinweis',role:'status'});
  var loeschen=el('button',{class:'knopf klein rot',text:'Foto entfernen',hidden:!vorhanden,onclick:function(){
    frage('Foto von Nr. '+nr+' entfernen?','Entfernen').then(function(j){if(!j)return;meldung.textContent='Entfernt …';
      fotoSha(nr).then(function(sha){if(!sha)return null;return api('/contents/'+fotoPfad(nr),{method:'DELETE',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({message:'Chef-App: Foto Nr. '+nr+' entfernt',sha:sha,branch:'main'})}).then(function(r){if(!r.ok)throw new Error('Entfernen fehlgeschlagen ('+r.status+')');return r.json();});})
      .then(function(d){delete fotoBereich.neu[nr];STD.fotos=(STD.fotos||[]).filter(function(f){return f!==nr;});vorschau.hidden=true;loeschen.hidden=true;
        meldung.textContent='Foto entfernt – in ca. 3 Minuten auch auf der Seite.';if(d&&d.commit)beobachten(d.commit.sha);})
      .catch(function(e){meldung.textContent=e.message;});});}});
  eingabe.addEventListener('change',function(){var f=eingabe.files&&eingabe.files[0];if(!f)return;meldung.textContent='Foto wird vorbereitet …';
    verkleinern(f).then(function(b64){meldung.textContent='Wird hochgeladen …';vorschau.src='data:image/jpeg;base64,'+b64;vorschau.hidden=false;
      return fotoSha(nr).then(function(sha){var body={message:'Chef-App: Foto Nr. '+nr,content:b64,branch:'main'};if(sha)body.sha=sha;
        return api('/contents/'+fotoPfad(nr),{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});})
        .then(function(r){if(!r.ok)throw new Error('Hochladen fehlgeschlagen ('+r.status+')');return r.json();})
        .then(function(d){fotoBereich.neu[nr]=b64;loeschen.hidden=false;meldung.textContent='Foto gespeichert ✓ – in ca. 3 Minuten auf der Seite.';beobachten(d.commit&&d.commit.sha);});})
    .catch(function(e){meldung.textContent=e.message;});});
  return el('div',{class:'foto-bereich'},[el('label',{for:'foto-datei',text:'Foto des Gerichts'}),vorschau,
    el('div',{class:'reihe'},[el('label',{class:'knopf',for:'foto-datei',style:'display:inline-flex;align-items:center;margin:0',text:vorhanden?'Neues Foto …':'Foto aufnehmen oder auswählen'}),loeschen]),eingabe,meldung,
    el('p',{class:'hinweis',text:'Querformat wirkt am besten; die Seite schneidet auf 4:3 zu. Das Foto wird sofort gespeichert.'})]);
}
fotoBereich.neu={};

var TAGE=['So','Mo','Di','Mi','Do','Fr','Sa'],WOCHE=[1,2,3,4,5,6,0];
function aktionBearbeiten(index){
  var alt=index==null?{name:'',von:heute(),bis:heute(6),preise:{}}:kopie(ANP.aktionen[index]),a=kopie(alt);
  var alle=gerichte().filter(function(x){return !x.geloescht;}),nach={};alle.forEach(function(x){nach[schl(x)]=x;});
  var b=el('div',{class:'blatt'}),inhalt=el('div');b.appendChild(inhalt);document.body.appendChild(b);
  var name=el('input',{type:'text',id:'a-name',maxlength:'60',value:a.name,placeholder:'z. B. Döner 5 €, Dürüm 6 €'});
  var von=el('input',{type:'date',id:'a-von',value:a.von}),bis=el('input',{type:'date',id:'a-bis',value:a.bis});
  var tageBox=el('div',{class:'wahl'}),ladenBox=el('div',{class:'wahl'}),liste=el('div'),such=el('input',{type:'search',id:'a-such',placeholder:'Gericht hinzufügen: Name oder Nummer','aria-label':'Gericht suchen'}),treffer=el('div');
  var fehler=el('p',{class:'fehler',hidden:true}),zeitBox=el('div',{class:'wahl'}),zl=zeitListe(6*60,24*60-30,30);
  var zab=el('select',{id:'a-zab','aria-label':'Uhrzeit von'},zl.map(function(z){return el('option',{value:z,text:z});}));
  var zbis=el('select',{id:'a-zbis','aria-label':'Uhrzeit bis'},zl.concat(['24:00']).map(function(z){return el('option',{value:z,text:z});}));
  zab.value=a.zeit_ab||'11:00';zbis.value=a.zeit_bis||'14:00';var zeitReihe=el('div',{class:'reihe',hidden:!a.zeit_ab},[zab,'–',zbis,' Uhr']);
  function zeitZeichnen(){zeitBox.textContent='';[[false,'Ganztags'],[true,'Nur zu bestimmten Uhrzeiten']].forEach(function(o){
    zeitBox.appendChild(el('button',{'aria-pressed':String(!!a.zeit_ab===o[0]),text:o[1],onclick:function(){if(o[0]){a.zeit_ab=zab.value;a.zeit_bis=zbis.value;}else{delete a.zeit_ab;delete a.zeit_bis;}zeitReihe.hidden=!o[0];zeitZeichnen();}}));});}
  function tageZeichnen(){tageBox.textContent='';var ts=a.tage||[];
    tageBox.appendChild(el('button',{'aria-pressed':String(!ts.length),text:'Jeden Tag',onclick:function(){delete a.tage;tageZeichnen();}}));
    WOCHE.forEach(function(d){tageBox.appendChild(el('button',{'aria-pressed':String(ts.indexOf(d)>-1),text:TAGE[d],onclick:function(){
      var n=(a.tage||[]).slice(),i=n.indexOf(d);if(i>-1)n.splice(i,1);else n.push(d);if(n.length)a.tage=n;else delete a.tage;tageZeichnen();}}));});}
  function ladenZeichnen(){ladenBox.textContent='';[['','Beide'],['freital','Freital'],['altenberg','Altenberg']].forEach(function(o){
    ladenBox.appendChild(el('button',{'aria-pressed':String((a.laden||'')===o[0]),text:o[1],onclick:function(){if(o[0])a.laden=o[0];else delete a.laden;ladenZeichnen();}}));});}
  function listeZeichnen(){liste.textContent='';Object.keys(a.preise).forEach(function(k){var x=nach[k];if(!x)return;
    var felder=x.preise.map(function(p,i){return el('input',{type:'text',inputmode:'decimal',value:a.preise[k][i]||'','aria-label':'Aktionspreis '+x.name+(x.a.groessen.length?' '+x.a.groessen[i]:''),
      'data-ak':k,style:'width:92px;min-height:40px',oninput:function(ev){a.preise[k][i]=ev.target.value;}});});
    liste.appendChild(el('div',{class:'tag'},[el('span',{style:'flex:1',text:(x.nr?x.nr+' ':'')+x.name+' (sonst '+x.preise.join(' / ')+' €)'})].concat(felder,
      [el('button',{class:'knopf klein','aria-label':'Entfernen',text:'✕',onclick:function(){delete a.preise[k];listeZeichnen();}})])));});
    if(!Object.keys(a.preise).length)liste.appendChild(el('p',{class:'hinweis',text:'Noch keine Gerichte.'}));}
  such.addEventListener('input',function(){treffer.textContent='';var q=such.value.trim().toLowerCase();if(!q)return;
    alle.filter(function(x){return (x.nr+' '+x.name).toLowerCase().indexOf(q)>-1&&!a.preise[schl(x)];}).slice(0,8).forEach(function(x){
      treffer.appendChild(el('button',{class:'liste-gericht',onclick:function(){a.preise[schl(x)]=x.preise.map(function(){return '';});such.value='';treffer.textContent='';listeZeichnen();
        var f=liste.querySelector('[data-ak="'+schl(x).replace(/"/g,'')+'"]');if(f)f.focus();}},[el('span',{class:'nr',text:x.nr}),el('span',{class:'nm',text:x.name}),el('span',{class:'pr',text:x.preise.join(' / ')+' €'})]));});});
  function speichernA(){
    a.name=name.value.trim();a.von=von.value;a.bis=bis.value;
    if(a.zeit_ab){a.zeit_ab=zab.value;a.zeit_bis=zbis.value==='24:00'?'23:59':zbis.value;if(a.zeit_ab>=a.zeit_bis){fehler.textContent='Bei der Uhrzeit muss „bis“ nach „von“ liegen.';fehler.hidden=false;return;}}
    if(!a.name){fehler.textContent='Bitte einen Namen eingeben, z. B. „Döner 5 €“.';fehler.hidden=false;return;}
    if(!a.von||!a.bis||a.bis<a.von){fehler.textContent='Bitte einen gültigen Zeitraum wählen.';fehler.hidden=false;return;}
    var ks=Object.keys(a.preise);if(!ks.length){fehler.textContent='Bitte mindestens ein Gericht hinzufügen.';fehler.hidden=false;return;}
    for(var i=0;i<ks.length;i++){var ps=a.preise[ks[i]].map(preisNorm);if(ps.some(function(p){return !p;})){fehler.textContent='Aktionspreis für '+nach[ks[i]].name+' bitte so eingeben: 5,00';fehler.hidden=false;return;}a.preise[ks[i]]=ps;}
    ANP.aktionen=ANP.aktionen||[];if(index==null)ANP.aktionen.push(a);else ANP.aktionen[index]=a;b.remove();zeichnen();}
  var knoepfe=[el('button',{class:'knopf',text:'Abbrechen',onclick:function(){b.remove();}})];
  if(index!=null)knoepfe.push(el('button',{class:'knopf rot',text:'Aktion löschen',onclick:function(){ANP.aktionen.splice(index,1);b.remove();zeichnen();}}));
  knoepfe.push(el('button',{class:'knopf voll',text:'Übernehmen',onclick:speichernA}));
  [el('h3',{text:index==null?'Neue Sonderaktion':'Sonderaktion ändern'}),el('label',{for:'a-name',text:'Name (steht oben auf der Seite)'}),name,
   el('div',{class:'reihe'},[el('div',{style:'flex:1'},[el('label',{for:'a-von',text:'von'}),von]),el('div',{style:'flex:1'},[el('label',{for:'a-bis',text:'bis'}),bis])]),
   el('label',{text:'An welchen Tagen?'}),tageBox,el('label',{text:'Uhrzeit (z. B. Mittagsangebot)'}),zeitBox,zeitReihe,el('label',{text:'Welcher Laden?'}),ladenBox,
   el('label',{text:'Gerichte und Aktionspreise'}),liste,such,treffer,fehler,el('div',{class:'reihe'},knoepfe)].forEach(function(n){inhalt.appendChild(n);});
  tageZeichnen();ladenZeichnen();zeitZeichnen();listeZeichnen();name.focus();
}
function zeitenTab(){
  app.appendChild(el('h2',{text:'Öffnungszeiten'}));
  var zeiten=zeitListe(6*60,24*60-30,30);
  STD.laeden.forEach(function(l){
    var anp=((ANP.zeiten||{})[l.id])||{},k=el('div',{class:'karte'},[el('h3',{text:l.name})]);
    WOCHE.forEach(function(t){
      var std=l.zeiten[t]||null,akt=(String(t) in anp)?anp[t]:std,auf=!!akt;
      var cb=el('input',{type:'checkbox','aria-label':TAGE[t]+' geöffnet'});cb.checked=auf;
      var von=el('select',{'aria-label':TAGE[t]+' von'},zeiten.map(function(z){return el('option',{value:z,text:z});}));
      var bis=el('select',{'aria-label':TAGE[t]+' bis'},zeiten.concat(['24:00']).map(function(z){return el('option',{value:z,text:z});}));
      von.value=akt?akt[0]:(std?std[0]:'10:00');bis.value=akt?akt[1]:(std?std[1]:'22:00');von.disabled=bis.disabled=!auf;
      function setzen(){var wert=cb.checked?[von.value,bis.value==='24:00'?'23:59':bis.value]:null;
        if(wert&&wert[0]>=wert[1]){status('„bis“ muss nach „von“ liegen.','rot',3000);return;}
        ANP.zeiten=ANP.zeiten||{};var z=ANP.zeiten[l.id]=ANP.zeiten[l.id]||{};
        if(JSON.stringify(wert)===JSON.stringify(std))delete z[t];else z[t]=wert;zeichnen();}
      [cb,von,bis].forEach(function(f){f.addEventListener('change',setzen);});
      k.appendChild(el('div',{class:'tag'+(String(t) in anp?' anders':'')},[el('strong',{text:TAGE[t]}),cb].concat(
        auf?[von,'–',bis]:[el('span',{class:'geschl',text:'geschlossen'})])));
    });
    if(Object.keys(anp).length)k.appendChild(el('div',{class:'reihe',style:'margin-top:10px'},[el('button',{class:'knopf klein',text:'Standardzeiten für '+l.name,onclick:function(){delete ANP.zeiten[l.id];zeichnen();}})]));
    app.appendChild(k);
  });
  app.appendChild(el('p',{class:'hinweis',text:'Gelb markierte Tage weichen vom Standard ab.'}));
  sonderKarte();
}
/* Feiertage in Sachsen (plus Heiligabend und Silvester) für die nächsten Tage */
function iso(d){return d.getUTCFullYear()+'-'+('0'+(d.getUTCMonth()+1)).slice(-2)+'-'+('0'+d.getUTCDate()).slice(-2);}
function feiertage(jahr){
  var a=jahr%19,b=Math.floor(jahr/100),c=jahr%100,d=Math.floor(b/4),e=b%4,f=Math.floor((b+8)/25),g=Math.floor((b-f+1)/3),
      h=(19*a+b-d-g+15)%30,i=Math.floor(c/4),k=c%4,l=(32+2*e+2*i-h-k)%7,m=Math.floor((a+11*h+22*l)/451),
      mon=Math.floor((h+l-7*m+114)/31),tag=((h+l-7*m+114)%31)+1,ostern=Date.UTC(jahr,mon-1,tag);
  var plus=function(n){return iso(new Date(ostern+n*864e5));};
  var bb=new Date(Date.UTC(jahr,10,22));while(bb.getUTCDay()!==3)bb=new Date(bb.getTime()-864e5);
  return [[jahr+'-01-01','Neujahr'],[plus(-2),'Karfreitag'],[plus(1),'Ostermontag'],[jahr+'-05-01','Tag der Arbeit'],
    [plus(39),'Christi Himmelfahrt'],[plus(50),'Pfingstmontag'],[jahr+'-10-03','Tag der Deutschen Einheit'],[jahr+'-10-31','Reformationstag'],
    [iso(bb),'Buß- und Bettag'],[jahr+'-12-24','Heiligabend (kein Feiertag)'],[jahr+'-12-25','1. Weihnachtstag'],[jahr+'-12-26','2. Weihnachtstag'],
    [jahr+'-12-31','Silvester (kein Feiertag)']];
}
function offeneFeiertage(tage){
  var t=heute(),bis=heute(tage),j=+t.slice(0,4),SZ=ANP.sonderzeiten||{},ok=ANP.feiertage_ok||[];
  return feiertage(j).concat(feiertage(j+1)).filter(function(f){return f[0]>=t&&f[0]<=bis&&!SZ[f[0]]&&ok.indexOf(f[0])<0;});
}
function feiertagKarte(){
  var liste=offeneFeiertage(75);if(!liste.length)return;
  var k=el('div',{class:'karte feiertag'},[el('h3',{text:'Feiertage demnächst'}),el('p',{class:'hinweis',style:'margin:0 0 6px',text:'Wie ist an diesen Tagen geöffnet? Einmal antippen, dann steht es auf der Seite.'})]);
  liste.forEach(function(f){
    var wt=['So','Mo','Di','Mi','Do','Fr','Sa'][new Date(f[0]+'T12:00:00Z').getUTCDay()];
    k.appendChild(el('div',{class:'cl-punkt','data-feiertag':f[0]},[el('b',{text:wt+', '+datumDE(f[0])+' '+f[1]}),
      el('div',{class:'reihe',style:'margin-top:6px'},[
        el('button',{class:'knopf klein rot',text:'Beide geschlossen',onclick:function(){var e={};STD.laeden.forEach(function(l){e[l.id]=null;});(ANP.sonderzeiten=ANP.sonderzeiten||{})[f[0]]=e;zeichnen();}}),
        el('button',{class:'knopf klein',text:'Wie sonntags',onclick:function(){var e={};STD.laeden.forEach(function(l){var z=Object.assign({},l.zeiten,(ANP.zeiten||{})[l.id]||{})['0'];e[l.id]=z?[z[0],z[1]]:null;});
          (ANP.sonderzeiten=ANP.sonderzeiten||{})[f[0]]=e;zeichnen();}}),
        el('button',{class:'knopf klein',text:'Normal geöffnet',onclick:function(){(ANP.feiertage_ok=ANP.feiertage_ok||[]).push(f[0]);zeichnen();}})])]));
  });
  app.appendChild(k);
}
function sonderKarte(){
  app.appendChild(el('h2',{text:'Besondere Tage'}));
  feiertagKarte();
  var t=heute(),k=el('div',{class:'karte'},[el('p',{class:'hinweis',style:'margin:0 0 8px',text:'Z. B. Heiligabend, Feiertag, Betriebsferien. Gilt nur an diesem Datum – die Seite zeigt es an und bietet passende Abholzeiten an.'})]);
  var SZ=ANP.sonderzeiten||{},namen={};STD.laeden.forEach(function(l){namen[l.id]=l.name;});
  Object.keys(SZ).sort().forEach(function(d){if(d<t)return;Object.keys(SZ[d]).forEach(function(l){var w=SZ[d][l];
    k.appendChild(el('p',{},[el('span',{class:'chip'},[datumDE(d)+' '+namen[l]+': '+(w?w[0]+'–'+w[1]+' Uhr':'geschlossen'),
      el('button',{'aria-label':'Eintrag entfernen',text:'✕',onclick:function(){delete SZ[d][l];if(!Object.keys(SZ[d]).length)delete SZ[d];zeichnen();}})])]));});});
  var zeiten=zeitListe(6*60,24*60-30,30),datum=el('input',{type:'date',id:'s-datum',value:heute(1),min:t});
  var laden='alle',auf=false;
  var wahlL=el('div',{class:'wahl'}),wahlA=el('div',{class:'wahl'});
  var von=el('select',{id:'s-von','aria-label':'von'},zeiten.map(function(z){return el('option',{value:z,text:z});}));
  var bis=el('select',{id:'s-bis','aria-label':'bis'},zeiten.concat(['24:00']).map(function(z){return el('option',{value:z,text:z});}));
  von.value='10:00';bis.value='16:00';var zeitReihe=el('div',{class:'reihe',hidden:true},[von,'–',bis]);
  function wahl(box,opts,akt,setz){box.textContent='';opts.forEach(function(o){box.appendChild(el('button',{'aria-pressed':String(akt()===o[0]),text:o[1],onclick:function(){setz(o[0]);wahl(box,opts,akt,setz);}}));});}
  wahl(wahlL,[['alle','Beide'],['freital','Freital'],['altenberg','Altenberg']],function(){return laden;},function(v){laden=v;});
  wahl(wahlA,[[false,'Geschlossen'],[true,'Andere Zeiten']],function(){return auf;},function(v){auf=v;zeitReihe.hidden=!v;});
  [el('label',{for:'s-datum',text:'Datum'}),datum,el('label',{text:'Laden'}),wahlL,el('label',{text:'An diesem Tag'}),wahlA,zeitReihe,
   el('div',{class:'reihe'},[el('button',{class:'knopf voll',text:'Tag hinzufügen',onclick:function(){
     var d=datum.value,w=auf?[von.value,bis.value==='24:00'?'23:59':bis.value]:null;
     if(!d||d<t){status('Bitte ein Datum ab heute wählen.','rot',3000);return;}
     if(w&&w[0]>=w[1]){status('„bis“ muss nach „von“ liegen.','rot',3000);return;}
     ANP.sonderzeiten=ANP.sonderzeiten||{};var e=ANP.sonderzeiten[d]=ANP.sonderzeiten[d]||{};
     (laden==='alle'?STD.laeden.map(function(l){return l.id;}):[laden]).forEach(function(l){e[l]=w;});zeichnen();}})])
  ].forEach(function(x){k.appendChild(x);});
  app.appendChild(k);
}
function zahlenKarte(){
  if(!STD.zaehler)return;
  var GK='saray-chef-goatcounter',schl='';try{schl=localStorage.getItem(GK)||'';}catch(e){}
  var dash='https://'+STD.zaehler+'.goatcounter.com/',k=el('div',{class:'karte'},[el('h3',{text:'Besucher und Bestellungen'})]);
  app.appendChild(el('h2',{text:'Zahlen'}));app.appendChild(k);
  var link=el('a',{class:'knopf klein',href:dash,target:'_blank',rel:'noopener',style:'display:inline-flex;align-items:center;text-decoration:none',text:'Ausführliche Statistik'});
  if(!schl){var f=el('input',{type:'text',id:'gc-schl',autocomplete:'off','aria-label':'API-Schlüssel','placeholder':'API-Schlüssel von GoatCounter'});
    k.appendChild(el('p',{class:'hinweis',text:'Einmal einrichten: bei GoatCounter unter „API“ einen Schlüssel mit Leserechten erstellen und hier eintragen. Er bleibt nur auf diesem Gerät.'}));
    k.appendChild(f);k.appendChild(el('div',{class:'reihe'},[el('button',{class:'knopf voll',text:'Speichern',onclick:function(){try{localStorage.setItem(GK,f.value.replace(/\s+/g,''));}catch(e){}zeichnen();}}),link]));return;}
  var box=el('div',{},[el('p',{class:'hinweis',text:'Lädt …'})]);k.appendChild(box);
  k.appendChild(el('div',{class:'reihe'},[el('button',{class:'knopf klein',text:'Aktualisieren',onclick:function(){zahlenKarte.cache=null;zeichnen();}}),link,el('button',{class:'knopf klein',text:'Schlüssel entfernen',onclick:function(){try{localStorage.removeItem(GK);}catch(e){}zeichnen();}})]));
  function stunde(tage){var n=new Date(),h=+new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',hour:'2-digit',hourCycle:'h23'}).format(n);
    var d=new Date(n);d.setUTCMinutes(0,0,0);d=new Date(d.getTime()-(h+24*tage)*36e5);return d.toISOString().replace('.000','');}
  function holen(start){var ende=new Date();ende.setUTCMinutes(0,0,0);ende=new Date(ende.getTime()+36e5);
    return fetch(dash+'api/v0/stats/hits?limit=100&start='+encodeURIComponent(start)+'&end='+encodeURIComponent(ende.toISOString().replace('.000','')),
      {headers:{'Authorization':'Bearer '+schl,'Accept':'application/json'},cache:'no-store'})
      .then(function(r){if(r.ok)return r.json();
        return r.text().then(function(t){var m=t;try{var j=JSON.parse(t);m=j.error||JSON.stringify(j.errors||j);}catch(e){}
          throw new Error(r.status+(m?': '+String(m).slice(0,160):''));});});}
  function werte(d){var w={besuche:0};(d.hits||[]).forEach(function(h){if(h.event)w[h.path]=(w[h.path]||0)+h.count;else w.besuche+=h.count;});return w;}
  /* gezählt wird seit Oktober 2026 – „Gesamt“ beginnt dort */
  var spalten=[['Heute',stunde(0)],['7 Tage',stunde(6)],['30 Tage',stunde(29)],['Gesamt','2026-10-01T00:00:00Z']];
  /* nacheinander abfragen (GoatCounter begrenzt die Anfragen pro Sekunde), bei 429 kurz warten; Ergebnis 5 Minuten merken */
  function warten(ms){return new Promise(function(ok){setTimeout(ok,ms);});}
  /* GoatCounter bremst schon bei wenigen Anfragen pro Sekunde – auch die Vorab-Anfrage des Browsers. Wird die gebremst,
     meldet Safari nur „Load failed“. Darum: Abstand zwischen den Abfragen und bei 429 oder Netzfehler etwas warten und wiederholen. */
  function holenGeduldig(start,versuch){versuch=versuch||0;return holen(start).catch(function(e){var m=String(e.message||e),t=/try again in ([\d.]+)ms/.exec(m);
    var nochmal=/^429/.test(m)||e instanceof TypeError||/fetch|load|network/i.test(m);
    if(nochmal&&versuch<5)return warten((t?Math.ceil(+t[1]):1500*(versuch+1))+400).then(function(){return holenGeduldig(start,versuch+1);});throw e;});}
  var cache=zahlenKarte.cache&&Date.now()-zahlenKarte.cache.t<5*60e3&&zahlenKarte.cache.schl===schl?Promise.resolve(zahlenKarte.cache.x):
    spalten.reduce(function(kette,sp,i){return kette.then(function(liste){
      box.textContent='';box.appendChild(el('p',{class:'hinweis',text:'Lädt … ('+(i+1)+' von '+spalten.length+')'}));
      return (i?warten(1200):Promise.resolve()).then(function(){return holenGeduldig(sp[1]);}).then(function(d){return liste.concat([d]);});});},Promise.resolve([]))
      .then(function(x){zahlenKarte.cache={t:Date.now(),x:x,schl:schl};return x;});
  cache.then(function(x){var w=x.map(werte);box.textContent='';
    var z=[['Besucher',['besuche']],['WhatsApp Freital',['whatsapp-freital']],['WhatsApp Altenberg',['whatsapp-altenberg']],
      ['Anrufe Freital',['anrufen-freital']],['Anrufe Altenberg',['anrufen-altenberg']],['Bestellung geteilt',['bestellung-teilen']],
      ['Gemeinsam bestellt',['gemeinsam-bestellen']],['Zur Google-Bewertung',['bewertung-freital','bewertung-altenberg']]];
    var sum=function(w,ks){return ks.reduce(function(s,k){return s+(w[k]||0);},0);};
    var t=el('table',{class:'zahlen'},[el('tr',{},[el('th',{text:''})].concat(spalten.map(function(sp){return el('th',{scope:'col',text:sp[0]});})))]);
    z.forEach(function(r){t.appendChild(el('tr',{},[el('th',{scope:'row',text:r[0]})].concat(w.map(function(x){return el('td',{text:String(sum(x,r[1]))});}))));});
    box.appendChild(t);
  }).catch(function(e){box.textContent='';
    var m=String(e.message||e),t=/^404/.test(m)?'GoatCounter hat noch keine Zahlen geliefert ('+m+'). Das kommt vor, solange erst wenige Besuche gezählt sind – später noch einmal ansehen.'
      :/^40[13]/.test(m)?'Der Schlüssel wird nicht angenommen ('+m+'). Bitte bei GoatCounter einen Schlüssel mit „Read statistics“ anlegen.'
      :/fetch|network|load/i.test(m)?'GoatCounter erlaubt den Abruf aus der App nicht ('+m+'). Bitte die ausführliche Statistik öffnen.'
      :'Zahlen konnten nicht geladen werden ('+m+'). Schlüssel prüfen – oder die ausführliche Statistik öffnen.';
    box.appendChild(el('p',{class:'fehler',text:t}));
    box.appendChild(el('p',{class:'hinweis',text:'Abfrage: '+dash+'api/v0/stats/hits'}));});
}
function kopierZeile(titel,wert,lang){
  var k=el('button',{class:'knopf klein',text:'Kopieren',onclick:function(){
    var fertig=function(){k.textContent='Kopiert ✓';setTimeout(function(){k.textContent='Kopieren';},1500);};
    if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(wert).then(fertig,function(){t.select();});else t.select();}});
  var t=el(lang?'textarea':'input',{readonly:true,'aria-label':titel,rows:lang?'5':null});t.value=wert;
  return el('div',{class:'gp-zeile'},[el('div',{class:'gp-kopf'},[el('b',{text:titel}),k]),t]);
}
function googleKarte(){ /* Angaben fürs Google-Unternehmensprofil – zum Abgleichen und Kopieren */
  var T=['So','Mo','Di','Mi','Do','Fr','Sa'],W=[1,2,3,4,5,6,0];
  var d=el('details',{class:'karte checkliste'},[el('summary',{},[el('b',{text:'Google-Unternehmensprofil'}),' · Angaben zum Kopieren'])]);
  d.appendChild(el('p',{class:'hinweis',text:'In der Google-Maps-App oder auf business.google.com anmelden, das Profil des Ladens öffnen und diese Angaben vergleichen. Abweichungen übernehmen.'}));
  STD.laeden.forEach(function(l){
    var z=Object.assign({},l.zeiten,(ANP.zeiten||{})[l.id]||{}),zeilen=[];
    W.forEach(function(t){var w=z[String(t)];zeilen.push(T[t]+': '+(w?w[0]+'–'+w[1]:'geschlossen'));});
    d.appendChild(el('p',{class:'abschnitt',text:'Saray Döner '+l.name}));
    [['Name','Saray Döner '+l.name],['Adresse',l.strasse+', '+l.plz+' '+l.ort],['Telefon',l.tel],
     ['Website',STD.seite],['Link zum Bestellen (Speisekarte)',STD.seite+'?laden='+l.id+'#speisekarte'],
     ['Öffnungszeiten',zeilen.join('\n'),1],
     ['Zahlungsarten',l.bar?'Nur Barzahlung (bei Google unter „Zahlungen“: nur Bargeld)':'Bar'],
     ['Beschreibung (max. 750 Zeichen)','Saray Döner in '+l.ort+' – seit 1997 Döner, Dürüm, Pizza, Lahmacun, Salate und Teller. '+
       'Dönerfleisch aus Kalb und Pute, Hähnchen-Döner, viele vegetarische Gerichte mit Falafel und Halloumi. '+
       'Online vorbestellen: Gerichte auf der Website zusammenstellen und per WhatsApp schicken, dann ohne Warten abholen. '+
       (l.extra?l.extra+' ':'')+'Bezahlung nur bar.',1],
     ['Merkmale','Abholung: ja · Lieferung: nein · Vegetarische Gerichte: ja · Zahlungen: nur Bargeld'+(l.extra&&/draußen/.test(l.extra)?' · Sitzplätze im Freien: ja':'')]
    ].forEach(function(x){d.appendChild(kopierZeile(x[0],x[1],x[2]));});
  });
  d.appendChild(el('p',{class:'hinweis',text:'Außerdem: Kategorie „Döner-Restaurant“, Fotos vom Laden und von Gerichten hochladen, auf Bewertungen antworten. Halal nur angeben, wenn es bestätigt ist.'}));
  app.appendChild(d);
}
function mehrTab(){
  app.appendChild(el('h2',{text:'Mehr'}));
  checklisteKarte();
  hinweisKarte();
  zahlenKarte();
  googleKarte();
  app.appendChild(el('div',{class:'karte'},[el('h3',{text:'Seite ansehen'}),el('p',{class:'hinweis',text:'Änderungen sind nach dem Speichern in ca. 2–3 Minuten online.'}),
    el('div',{class:'reihe'},[el('a',{class:'knopf voll',href:'../',target:'_blank',rel:'noopener',style:'display:inline-flex;align-items:center;text-decoration:none',text:'Website öffnen'})])]));
  /* Preis-Stände */
  var sk=el('div',{class:'karte'},[el('h3',{text:'Preis-Stände'}),el('p',{class:'hinweis',text:'Den Stand '+STD.grundstand+' (gedruckte Karte) gibt es immer. Dazu bis zu drei eigene Stände, z. B. vor einer Preiserhöhung. Einzelne Preise holen Sie beim Gericht unter „Frühere Preise“ zurück.'})]);
  staende().forEach(function(st,i){
    var n=0;gerichte().forEach(function(x){var p=st.preise[schl(x)];if(p&&JSON.stringify(p)!==JSON.stringify(x.preise))n++;});
    var kn=[el('button',{class:'knopf klein',text:'Alle Preise so',disabled:!n,onclick:function(){frage('Alle Preise auf „'+st.name+'“ setzen? ('+n+' Preise ändern sich)','Ja, übernehmen').then(function(j){if(!j)return;
      gerichte().forEach(function(x){var p=st.preise[schl(x)];if(p&&p.length===x.preise.length)preisSetzen(x,p);});zeichnen();});}})];
    if(!st.grund)kn.push(el('button',{class:'knopf klein rot',text:'Löschen',onclick:function(){frage('„'+st.name+'“ löschen?','Löschen').then(function(j){if(j){ANP.staende.splice(i-1,1);zeichnen();}});}}));
    sk.appendChild(el('div',{class:'tag'},[el('span',{style:'flex:1;font-weight:700',text:st.name+(n?' · '+n+' Preise anders als jetzt':' · wie jetzt')})].concat(kn)));
  });
  var eigene=(ANP.staende||[]).length;
  sk.appendChild(el('div',{class:'reihe',style:'margin-top:10px'},[el('button',{class:'knopf voll',text:'Heutige Preise als Stand festlegen',disabled:eigene>=3,onclick:function(){
    var d=heute(),p=d.split('-'),st={name:'Stand '+p[2]+'.'+p[1]+'.'+p[0],datum:d,preise:{}};
    gerichte().forEach(function(x){if(!x.geloescht)st.preise[schl(x)]=x.preise.slice();});
    ANP.staende=(ANP.staende||[]).filter(function(s){return s.name!==st.name;}).concat([st]);zeichnen();}})]));
  if(eigene>=3)sk.appendChild(el('p',{class:'hinweis',text:'Höchstens drei eigene Stände – zum Festlegen bitte erst einen löschen.'}));
  app.appendChild(sk);
  /* Drucken */
  app.appendChild(el('div',{class:'karte'},[el('h3',{text:'Drucken'}),el('p',{class:'hinweis',text:'Immer mit den aktuellen Preisen (nach dem Speichern ca. 3 Minuten warten). Für die Druckerei oder den eigenen Drucker.'}),
    el('div',{class:'reihe'},[['../druck/flyer.pdf','Flyer (A4, Wickelfalz)']].concat(STD.laeden.map(function(l){return ['../druck/aufsteller-'+l.id+'.pdf','Aufsteller '+l.name+' (A5)'];}),
      [['../druck/flyer-gruppen.pdf','Flyer Firmen, Vereine, Feiern (A5)'],['../druck/allergenmappe.pdf','Allergenmappe für die Theke'],['../druck/aufkleber.pdf','Tüten-Aufkleber (24 × 70×37 mm)']],
      [].concat.apply([],(JSON.parse(ALT).aktionen||[]).filter(function(a){return a.bis>=heute();}).map(function(a){return [['../druck/'+slug(a.name,a.von)+'.pdf','Plakat: '+a.name+' (A4)'],
        ['../druck/'+slug(a.name,a.von)+'.png','Bild zum Posten: '+a.name]];})))
      .map(function(d){return el('a',{class:'knopf',href:d[0],target:'_blank',rel:'noopener',style:'display:inline-flex;align-items:center;text-decoration:none',text:d[1]});}))]));
  app.appendChild(el('div',{class:'karte'},[el('h3',{text:'Letzte Änderung rückgängig'}),
    el('p',{class:'hinweis',text:'Holt den Stand vor dem letzten Speichern zurück.'}),
    el('div',{class:'reihe'},[el('button',{class:'knopf',text:'Rückgängig machen …',onclick:rueckgaengig})])]));
  /* Gefahrenbereich: Aktionen, die sich nicht so einfach zurücknehmen lassen */
  app.appendChild(el('h2',{class:'gefahr-titel',text:'⚠️ Gefahrenbereich'}));
  app.appendChild(el('div',{class:'karte gefahr'},[
    el('p',{class:'hinweis',style:'margin:0 0 6px',text:'Nur benutzen, wenn Sie sicher sind.'}),
    el('h3',{text:'Standard wiederherstellen'}),
    el('p',{class:'hinweis',text:'Setzt Preise, Gerichte, Öffnungszeiten, Sperren, Zutaten, Aktionen und Hinweise auf den ursprünglichen Stand zurück. Die Checkliste „Vor dem Freischalten“ bleibt erhalten.'}),
    el('div',{class:'reihe'},[el('button',{class:'knopf rot voll',text:'Alles auf Standard zurücksetzen',onclick:function(){
      frage('Wirklich alle Änderungen löschen und den Standard wiederherstellen?','Ja, zurücksetzen').then(function(j){if(!j)return;
        var cl=ANP.checkliste;ANP=cl?{checkliste:cl}:{};speichern('Chef-App: Standard wiederhergestellt');});}})]),
    el('h3',{style:'margin-top:18px',text:'Zugang auf diesem Gerät'}),
    el('p',{class:'hinweis',text:'Der Zugang ist nur auf diesem Gerät gespeichert. Nach dem Abmelden braucht es einen neuen Zugangslink von Michael.'}),
    el('div',{class:'reihe'},[el('button',{class:'knopf rot',text:'Auf diesem Gerät abmelden',onclick:function(){frage('Zugang auf diesem Gerät löschen?','Abmelden').then(function(j){if(j){try{localStorage.removeItem(TK);}catch(e){}location.reload();}});}})])]));
}

/* Checkliste vor dem Freischalten – gespeichert in anpassungen.json („checkliste“), für die Seite ohne Wirkung */
var CHECKLISTE=%%CHECKLISTE%%;
function checklisteKarte(){
  var cl=ANP.checkliste||{},alle=[];CHECKLISTE.forEach(function(g){alle=alle.concat(g[1]);});
  var offen=alle.filter(function(x){return !(cl[x[0]]&&cl[x[0]].ok);}).length;
  var d=el('details',{class:'karte checkliste',open:offen?true:null},[el('summary',{},[el('b',{text:'Vor dem Freischalten'}),' · ',
    el('span',{text:offen?offen+' von '+alle.length+' offen':'alles erledigt ✓'})])]);
  CHECKLISTE.forEach(function(g){
    d.appendChild(el('p',{class:'abschnitt',text:g[0]}));
    g[1].forEach(function(x){var e=cl[x[0]]||{},id='cl-'+x[0];
      var cb=el('input',{type:'checkbox',id:id});cb.checked=!!e.ok;
      var no=el('input',{type:'text',id:id+'-n',placeholder:'Antwort / Notiz','aria-label':'Notiz: '+x[1],value:e.notiz||''});
      function setzen(){ANP.checkliste=ANP.checkliste||{};var w={};if(cb.checked)w.ok=true;if(no.value.trim())w.notiz=no.value.trim();
        if(Object.keys(w).length)ANP.checkliste[x[0]]=w;else delete ANP.checkliste[x[0]];leiste();}
      cb.addEventListener('change',function(){setzen();zeichnen();});no.addEventListener('change',setzen);
      d.appendChild(el('div',{class:'cl-punkt'+(e.ok?' erledigt':'')},[el('label',{class:'schalter',for:id},[cb,el('span',{},[x[1],x[3]?el('span',{class:'marke weg',text:'muss'}):null])]),
        x[2]?el('p',{class:'hinweis',style:'margin:2px 0 4px 32px',text:x[2]}):null,no]));});
  });
  app.appendChild(d);
}

function rueckgaengig(){
  if(geaendert()){status('Bitte zuerst speichern oder verwerfen.','rot',4000);return;}
  status('Sucht die letzte Änderung …');
  api('/commits?path='+encodeURIComponent(DATEI)+'&sha=main&per_page=2',{cache:'no-store'}).then(function(r){
    if(!r.ok)throw new Error('GitHub antwortet nicht ('+r.status+')');return r.json();
  }).then(function(c){
    if(!c.length)throw new Error('Es gibt noch keine gespeicherte Änderung');
    var letzte=c[0],davor=c[1],wann=new Date(letzte.commit.author.date).toLocaleString('de-DE',{day:'2-digit',month:'2-digit',hour:'2-digit',minute:'2-digit'});
    var inhalt=davor?api('/contents/'+DATEI+'?ref='+davor.sha,{cache:'no-store'}).then(function(r){if(!r.ok)throw new Error('Alter Stand nicht lesbar ('+r.status+')');return r.json();})
      .then(function(d){return JSON.parse(b64dec(d.content)||'{}');}):Promise.resolve({});
    return inhalt.then(function(alt){document.getElementById('status').hidden=true;
      return frage('Letzte Änderung vom '+wann+' rückgängig machen? („'+letzte.commit.message.split('\n')[0]+'“)','Ja, rückgängig').then(function(j){
        if(!j)return;ANP=alt&&typeof alt==='object'?alt:{};speichern('Chef-App: Rückgängig ('+wann+')');});});
  }).catch(function(e){status(e.message,'rot',6000);});
}

/* ---------- Einrichten ---------- */
function einrichten(meldung){
  document.getElementById('stand').textContent='Einrichten';
  var f=el('input',{type:'text',id:'tk',autocomplete:'off',placeholder:'github_pat_…'});
  app.textContent='';app.appendChild(el('div',{class:'karte'},[el('h3',{text:'Zugang einrichten'}),
    meldung?el('p',{class:'fehler',text:meldung}):null,
    el('p',{class:'hinweis',text:'Michael richtet den Zugang einmal pro Gerät ein. Danach diese Seite zum Home-Bildschirm hinzufügen.'}),
    el('label',{for:'tk',text:'Zugangsschlüssel'}),f,
    el('div',{class:'reihe'},[el('button',{class:'knopf voll',text:'Speichern',onclick:function(){try{localStorage.setItem(TK,f.value.replace(/\s+/g,''));}catch(e){}start();}})])]));
}
function start(){
  if(!token()){einrichten();return;}
  laden().catch(function(e){document.getElementById('status').hidden=true;
    einrichten(e.message==='zugang'?'Der Zugang ist ungültig oder abgelaufen.':'Laden fehlgeschlagen: '+e.message);});
}

document.getElementById('tabs').addEventListener('click',function(ev){var b=ev.target.closest('[data-tab]');if(!b)return;TAB=b.dataset.tab;
  [].forEach.call(this.querySelectorAll('[data-tab]'),function(x){if(x===b)x.setAttribute('aria-current','page');else x.removeAttribute('aria-current');});
  zeichnen();window.scrollTo(0,0);});
document.getElementById('speichern-knopf').addEventListener('click',function(){speichern();});
document.getElementById('verwerfen').addEventListener('click',function(){frage('Ungespeicherte Änderungen verwerfen?','Verwerfen').then(function(j){if(j){ANP=JSON.parse(ALT);zeichnen();}});});
window.addEventListener('beforeunload',function(e){if(STD&&geaendert()){e.preventDefault();e.returnValue='';}});
var m=/[#&]token=([^&]+)/.exec(location.hash);
if(m){try{localStorage.setItem(TK,decodeURIComponent(m[1]).replace(/\s+/g,''));}catch(e){}history.replaceState(null,'',location.pathname);}
start();
})();
</script>
</body>
</html>
"""


# Zutaten, die der Inhaber einzeln ausschalten kann (Namen wie auf der Seite; „Zwiebel“ gilt auch für „Zwiebeln“).
# Pommes/Reis: Gerichte gibt es dann ohne diese Beilage, je 0,50 € günstiger (BEILAGEN in build.py)
ZUTATEN_SCHALTER = [
    ["Soßen", ["Knoblauch", "Kräuter", "Chili"]],
    ["Salat und Gemüse", ["Eisbergsalat", "Tomate", "Gurken", "Zwiebel", "Rotkohl", "Weißkohl", "Paprika", "Champignon",
                          "Peperoni", "Ananas", "Oliven", "Brokkoli", "Mais"]],
    ["Beilagen", ["Pommes", "Reis"]],
    ["Käse", ["Käse", "Halloumikäse", "Fetakäse", "Mozzarella"]],
    ["Fleisch, Fisch, Ei", ["Dönerfleisch", "Hähnchen-Dönerfleisch", "Schinken", "Salami", "Thunfisch", "Ei"]],
]


# Offene Punkte vor dem Freischalten: [Gruppe, [[id, Text, Hinweis, muss]]]
CHECKLISTE = [
    ["Freischalten", [
        ["domain", "Domain saraydöner.de", "Wer hat Zugang zu Domain und DNS? Wo liegt die alte Seite?", 1],
        ["wa-freital", "WhatsApp Freital", "Ist 0157 37807403 das Laden-Handy für Bestellungen?", 1],
        ["wa-altenberg", "WhatsApp Altenberg", "Welche Nummer nimmt Bestellungen an?", 1],
        ["wa-wer", "Wer bestätigt die Bestellungen?", "Wer schaut während der Öffnungszeiten aufs Handy und antwortet?", 1],
        ["impressum", "Impressum", "Anschrift (Bahnhof 3 oder Dresdner Str. 23?), Firmenform, USt-IdNr. (falls vorhanden), E-Mail. Mehr als 10 Beschäftigte? Dann Hinweis zur Verbraucherschlichtung (§ 36 VSBG) nötig.", 1],
        ["allergene", "Allergene ergänzen und bestätigen", "Neu: h = Fisch (Nr. 71, 87, 97, 136, 154) und i = Ei in der Soße. Es fehlen noch Angaben für Extra-Portion, Fladenbrot und die Milchgetränke (Kaffee mit Milch, Kakao).", 1],
        ["goatcounter-av", "Besucherzählung: Auftragsverarbeitung", "Mit GoatCounter einen Vertrag zur Auftragsverarbeitung klären (oder Zählung abschalten).", 0],
        ["zeiten-altenberg", "Öffnungszeiten Altenberg samstags", "Ab 10 oder ab 11 Uhr? Google zeigt 11 Uhr.", 0],
        ["feiertage", "Feiertage", "Freital 11–22 Uhr, Altenberg? Reformationstag 31.10., Buß- und Bettag 18.11.", 0],
        ["preise", "Preise der Karte", "Gilt die Karte vom 01.02.2024 noch? In beiden Läden gleich?", 0],
        ["datenschutz", "Datenschutzerklärung", "Entwurf steht – wer prüft sie?", 0],
        ["logo", "Echtes Logo", "Original-Logo von Saray Döner als Datei (am besten SVG oder PDF, sonst großes PNG) – auch für Flyer und Aufsteller", 1],
        ["maskottchen", "Original-Maskottchen", "Den echten Saray-Koch als Datei; ersetzt die nachgezeichnete Figur auf Seite, App-Symbol und Druck", 1],
    ]],
    ["Chef-App und Abläufe", [
        ["chef-wer", "Wer bedient die Chef-App, auf welchen Handys?", "Pro Person ein eigener Zugang.", 0],
        ["einweisung", "Einweisung", "Heute aus, Zutaten, Wartezeit, besondere Tage, Aktionen, Hinweis, Drucken, Rückgängig", 0],
        ["gruppen-vorlauf", "Größere Bestellungen", "Ab wie vielen Portionen wie viel Vorlauf? Zum Beispiel „ab 10 Portionen am Vortag bestellen“. Kommt auf die Seite und den Gruppen-Flyer.", 0],
        ["vorbestellung", "Vorbestellung", "Bis 14 Tage im Voraus, frühestens 20 Minuten nach der Bestellung – passt das?", 0],
        ["beilage", "Pommes oder Reis aus = 0,50 € weniger", "So in Ordnung?", 0],
        ["zahlung", "Nur Barzahlung", "Kommt irgendwann Kartenzahlung dazu?", 0],
        ["aktion", "Erste Sonderaktion", "Zum Beispiel Mittagsangebot oder „Döner 5 €“", 0],
        ["druck", "Flyer und Aufsteller", "Probedruck ansehen, Anzahl, selbst drucken oder Druckerei?", 0],
    ]],
    ["Google und Fotos", [
        ["google", "Google-Unternehmensprofil", "Verwaltungszugriff, Link zur Seite, Zeiten angleichen, Barzahlung eintragen", 0],
        ["fotos", "Fotos der Gerichte", "Dürfen wir Fotos machen? Wann passt es?", 0],
    ]],
    ["Laufende Kosten", [
        ["domain-kosten", "Domain", "Wer zahlt die Domain, auf wen läuft sie?", 0],
        ["github-pro", "GitHub Pro", "Rund 4 US-$ im Monat. Nötig, damit Seite und Chef-Daten in einem privaten Repository liegen können. Wer zahlt?", 0],
    ]],
]


def schreiben(aus, gruppen, standorte, sperrgruppen, repo, zaehler="", cname="", fotos=()):
    """Schreibt docs/chef/: index.html, standard.json, manifest.webmanifest."""
    import anpassungen as ANP
    from menu import GRUNDSTAND
    ordner = aus / "chef"
    ordner.mkdir(exist_ok=True)
    zeit = lambda m: f"{m // 60:02d}:{m % 60:02d}"
    standard = {
        "gruppen": [{"id": g["id"], "titel": g["titel"], "abschnitte": [{
            "titel": a["titel"], "groessen": a.get("groessen") or [],
            "gerichte": [{"k": ANP.schluessel(g["id"], a["titel"], x), "nr": x[0], "name": x[1], "desc": x[2], "preise": list(x[3])}
                         for x in a["gerichte"]]} for a in g["abschnitte"]]} for g in gruppen],
        "grundstand": GRUNDSTAND,
        "zutaten": ZUTATEN_SCHALTER,
        "zaehler": zaehler,
        "seite": f"https://{cname}/",
        "fotos": sorted(fotos),
        "laeden": [{"id": s["id"], "name": s["name"], "strasse": s["strasse"], "plz": s["plz"], "ort": s["ort"], "tel": s["tel"],
                    "bar": bool(s.get("bar")), "extra": s.get("extra", ""),
                    "zeiten": {str(t): [zeit(v[0]), zeit(v[1])] for t, v in s["zeiten_standard"].items()}} for s in standorte],
        # Reihenfolge der Kärtchen unter „Heute“
        "sperren": [{"id": k, "name": sperrgruppen[k]["de"]} for k in
                    ["huhn", "nuggets", "falafel", "halloumi", "schnitzel-fleisch", "fisch",
                     "doener", "duerum", "teller", "pizza", "lahmacun", "baguette", "salate", "kinder"] if k in sperrgruppen],
    }
    (ordner / "standard.json").write_text(json.dumps(standard, ensure_ascii=False) + "\n", encoding="utf-8")
    (ordner / "index.html").write_text(SEITE.replace("%%REPO%%", json.dumps(repo))
                                        .replace("%%CHECKLISTE%%", json.dumps(CHECKLISTE, ensure_ascii=False)), encoding="utf-8")
    (ordner / "manifest.webmanifest").write_text(json.dumps({
        "name": "Saray Chef", "short_name": "Chef", "lang": "de", "start_url": "./", "scope": "./", "display": "standalone",
        "background_color": "#3A1531", "theme_color": "#3A1531",
        "icons": [{"src": f"../img/app-{g}.png", "sizes": f"{g}x{g}", "type": "image/png"} for g in (192, 512)],
    }, ensure_ascii=False, indent=2) + "\n")
