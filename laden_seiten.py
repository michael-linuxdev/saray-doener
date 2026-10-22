"""Seiten für den Laden selbst (nicht für Gäste):

docs/tv/      Speisekarte für einen Bildschirm im Laden (Fernseher mit Fire-TV-Stick o. Ä.).
              Gleiche Daten wie die Website: Preise, Aktionen, Mittagstisch, „heute aus“.
              Holt alle 60 s status.json (tagesaktuelle Sperren) und lädt sich neu, sobald die Seite neu gebaut wurde.
              Adresse: tv/?laden=freital  (weitere Parameter: sek=12 Sekunden je Seite, seiten=doener,pizza nur diese Gruppen)
docs/kueche/  Küchenansicht: Bestellungen aus dem Link „Für die Küche“ in der WhatsApp-Nachricht, groß und abhakbar,
              nach Abholzeit sortiert, mit Bon-Druck. Die Daten stehen im Link; gespeichert wird nur auf dem Gerät im Laden.
"""
import json

from qr import qr_svg

KOPF = r"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="robots" content="noindex">
<title>%%TITEL%%</title>
<link rel="icon" href="../img/favicon-96.png">
<style>
@font-face{font-family:"Saray Slab";src:url(../fonts/Roboto-Slab-Bold.sub.woff) format("woff");font-weight:700}
@font-face{font-family:"Saray Text";src:url(../fonts/lato-normal.sub.woff) format("woff");font-weight:400}
@font-face{font-family:"Saray Text";src:url(../fonts/lato-bold.sub.woff) format("woff");font-weight:700}
:root{--gelb:#FFD21F;--gelb-blass:#FFF1B8;--tinte:#3A1531;--tinte-weich:#6B4A63;--paprika:#C8381E;--gruen:#2E7D32;--linie:#E7DCC0}
*{box-sizing:border-box}
html,body{margin:0}
body{font-family:"Saray Text",system-ui,sans-serif;color:var(--tinte);background:#FFFBEF}
h1,h2,h3{font-family:"Saray Slab",Georgia,serif;margin:0}
button{font:inherit}
"""

# ---------------------------------------------------------------- Bildschirm (TV)
TV = KOPF.replace("%%TITEL%%", "Saray Döner – Bildschirm") + r"""
html,body{height:100%;overflow:hidden}
body{display:grid;grid-template-rows:auto 1fr auto;background:var(--gelb)}
.kopf{display:flex;align-items:center;gap:1.4vw;padding:1.2vh 2vw;background:var(--tinte);color:var(--gelb)}
.kopf img{height:6.5vh;width:auto}
.kopf h1{font-size:4.2vh;flex:1}
.kopf h1 small{font:700 2.4vh "Saray Text",sans-serif;color:#fff;margin-left:1vw}
.uhr{font:700 4.2vh "Saray Slab",serif;color:#fff}
.status{font:700 2.3vh "Saray Text";padding:.6vh 1.2vw;border-radius:99px;background:#fff;color:var(--tinte)}
.status.zu{background:var(--paprika);color:#fff}
.baender:empty{display:none}
.band{padding:1vh 2vw;background:var(--paprika);color:#fff;font:700 2.6vh "Saray Text";text-align:center}
.band.blau{background:#1E5B8C}
main{position:relative;overflow:hidden;padding:2vh 2vw 1vh}
.seite{position:absolute;inset:2vh 2vw 1vh;opacity:0;transition:opacity .8s;display:flex;flex-direction:column;--g:1}
.seite.an{opacity:1}
.spalten{columns:3;column-gap:2.4vw;column-fill:auto;flex:1;min-height:0;overflow:hidden;font-size:calc(2.35vh * var(--g))}
@media (orientation:portrait){.spalten{columns:2}}
.gruppe{margin:0 0 1.2em}
.gruppe>h2{font-size:2em;line-height:1.05;margin:0 0 .25em;padding:.15em .45em;background:var(--tinte);color:var(--gelb);border-radius:.4em;break-after:avoid}
.abschnitt{margin:0 0 .8em}
.abschnitt>h3{break-after:avoid;font-size:1.15em;margin:.4em 0 .2em;display:flex;justify-content:space-between;gap:1em;border-bottom:.12em solid var(--tinte)}
.abschnitt>h3 span{font:700 .8em "Saray Text";align-self:flex-end}
.g{display:grid;grid-template-columns:2.6em 1fr auto;column-gap:.5em;align-items:baseline;padding:.16em 0;break-inside:avoid}
.g .nr{font-weight:700;color:var(--tinte-weich);text-align:right}
.g .nm{font-weight:700;line-height:1.15}
.g .ds{display:block;font-weight:400;font-size:.78em;color:var(--tinte-weich);line-height:1.2}
.g .pr{font:700 1.1em "Saray Slab",serif;white-space:nowrap;color:var(--paprika)}
.g .alt{text-decoration:line-through;color:var(--tinte-weich);font-size:.8em;margin-right:.4em}
.g .marke{display:inline-block;font:700 .72em "Saray Text";padding:.05em .5em;border-radius:99px;background:var(--paprika);color:#fff;margin-left:.4em;vertical-align:.1em}
.g.aus{opacity:.38}
.g.aus .marke{background:var(--tinte)}
.heute{display:grid;grid-template-columns:repeat(3,1fr);gap:2vh 2vw;flex:1;align-content:start}
@media (orientation:portrait){.heute{grid-template-columns:repeat(2,1fr)}}
.heute>h2{grid-column:1/-1;font-size:5vh}
.karte{background:#fff;border:.35vh solid var(--tinte);border-radius:2.2vh;padding:2vh 1.4vw;display:flex;flex-direction:column;gap:.6vh;min-height:0}
.karte.rot{background:var(--paprika);color:#fff;border-color:var(--paprika)}
.karte .kl{font:700 2vh "Saray Text";text-transform:uppercase;letter-spacing:.06em}
.karte b{font:700 3.6vh "Saray Slab",serif;line-height:1.1}
.karte span{font-size:2.2vh}
.karte .gp{font:700 4.6vh "Saray Slab",serif;margin-top:auto}
.karte .gp s{font-size:.55em;opacity:.7;margin-right:.6vw}
.karte img{width:100%;aspect-ratio:4/3;object-fit:cover;border-radius:1.2vh}
.fuss{display:flex;align-items:center;gap:2vw;padding:1vh 2vw;background:var(--tinte);color:#fff;font:700 2.3vh "Saray Text"}
.fuss .qr{background:#fff;padding:.4vh;border-radius:.6vh;height:9vh;width:9vh}
.fuss .qr svg{width:100%;height:100%;display:block}
.fuss .text{flex:1}
.fuss .text small{display:block;font-weight:400;color:var(--gelb-blass)}
.punkte{display:flex;gap:.6vw}
.punkte i{width:1.2vh;height:1.2vh;border-radius:50%;background:rgba(255,255,255,.35)}
.punkte i.an{background:var(--gelb)}
.wahl{display:grid;place-content:center;gap:2vh;height:100vh;text-align:center;font-size:3vh}
.wahl a{display:block;padding:2vh 4vw;border-radius:2vh;background:var(--tinte);color:var(--gelb);font:700 4vh "Saray Slab",serif;text-decoration:none}
</style>
</head>
<body>
<header class="kopf"><img src="../img/saray-koch-kopf.svg" alt=""><h1>Saray Döner <small id="ort"></small></h1>
<span class="status" id="status"></span><span class="uhr" id="uhr"></span></header>
<main id="main"><div class="baender" id="baender"></div></main>
<footer class="fuss"><span class="qr">%%QR%%</span><span class="text">Vorbestellen per WhatsApp: %%ADRESSE%%<small>Handy-Kamera auf den Code halten · Nur Barzahlung · Alle Preise in Euro inkl. MwSt.</small></span><span class="punkte" id="punkte"></span></footer>
<script>
(function(){
'use strict';
var D=%%DATEN%%;
var q=new URLSearchParams(location.search),LADEN=q.get('laden'),SEK=Math.max(6,Math.min(120,+q.get('sek')||14)),NUR=(q.get('seiten')||'').split(',').filter(Boolean);
if(!D.laeden[LADEN]){
  document.body.innerHTML='<div class="wahl"><p>Welcher Laden?</p>'+Object.keys(D.laeden).map(function(k){return '<a href="?laden='+k+'">'+D.laeden[k].name+'</a>';}).join('')+'<p style="font-size:2vh">Tipp: Adresse als Startseite im Browser des Fernsehers speichern.</p></div>';
  return;
}
document.getElementById('ort').textContent=D.laeden[LADEN].name;
var REGELN=D.regeln.slice();
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function teile(){var f=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23',weekday:'short'}).formatToParts(new Date()),o={};
  f.forEach(function(p){o[p.type]=p.value;});var wt=['Sun','Mon','Tue','Wed','Thu','Fri','Sat'].indexOf(o.weekday);
  return {iso:o.year+'-'+o.month+'-'+o.day,min:(+o.hour)*60+(+o.minute),tag:wt,hh:o.hour,mm:o.minute};}
function minAus(t){var x=String(t).split(':');return (+x[0])*60+(+x[1]||0);}
function euro(c){return (c/100).toFixed(2).replace('.',',');}
function uhr(m){var h=Math.floor(m/60),r=m%60;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
function trifft(r,k){return [].concat(r.was||[]).some(function(v){v=String(v);return v===k||(D.sperr[v]&&D.sperr[v].nr.indexOf(k)>-1);});}
function gilt(r,n){
  if(r.laden&&r.laden!=='alle'&&r.laden!==LADEN)return false;
  if(r.datum&&[].concat(r.datum).indexOf(n.iso)<0)return false;
  if(r.tage&&r.tage.indexOf(n.tag)<0)return false;return true;}
function sperre(k,n){var res=null;REGELN.forEach(function(r){if(res&&res.art==='aus')return;if(!trifft(r,k)||!gilt(r,n))return;
  if(r.ab&&n.min<minAus(r.ab))res={art:'ab',t:'ab '+uhr(minAus(r.ab))};else if(r.bis&&n.min>=minAus(r.bis))res={art:'aus',t:'heute aus'};
  else if(!r.ab&&!r.bis)res={art:'aus',t:r.datum?'heute aus':'zurzeit aus'};});return res;}
function aktion(k,i,n){var best=null;D.aktionen.forEach(function(a){
  if(n.iso<a.von||n.iso>a.bis||(a.tage&&a.tage.indexOf(n.tag)<0)||(a.laden&&a.laden!==LADEN)||!a.p[k])return;
  if(a.za!=null&&(n.min<a.za||n.min>=a.zb))return;var c=a.p[k][i]!=null?a.p[k][i]:a.p[k][0];if(best==null||c<best.c)best={c:c,a:a};});return best;}
function oeffnung(n){var s=(D.laeden[LADEN].sonder||{})[n.iso],h=(n.iso in (D.laeden[LADEN].sonder||{}))?s:D.laeden[LADEN].zeiten[n.tag];
  var st=document.getElementById('status');
  if(h&&n.min>=h[0]&&n.min<h[1]){st.textContent='Geöffnet bis '+uhr(h[1]);st.className='status';}
  else{st.textContent=h&&n.min<h[0]?'Öffnet heute '+uhr(h[0]):'Geschlossen';st.className='status zu';}}
/* Seiten: „Heute bei Saray“ + Speisekarte, Gruppen so gepackt, dass jede Seite voll, aber nicht überfüllt ist */
function gruppeEl(g,n){
  var box=el('section','gruppe');box.appendChild(el('h2',null,g.titel));
  g.abschnitte.forEach(function(ab){var a=el('div','abschnitt');
    if(g.abschnitte.length>1||ab.groessen.length){var h=el('h3',null,g.abschnitte.length>1?ab.titel:'');if(ab.groessen.length)h.appendChild(el('span',null,ab.groessen.join(' / ')));a.appendChild(h);}
    ab.gerichte.forEach(function(x){var r=el('div','g'),sp=sperre(x.k,n);
      r.appendChild(el('span','nr',x.nr));var nm=el('span','nm',x.name);if(x.desc)nm.appendChild(el('span','ds',x.desc));
      var pr=el('span','pr'),ak=null;x.p.forEach(function(c,i){var a=aktion(x.k,i,n);if(a)ak=a;
        if(i)pr.appendChild(document.createTextNode(' / '));if(a&&a.c<c){pr.appendChild(el('span','alt',euro(c)));pr.appendChild(document.createTextNode(euro(a.c)));}else pr.appendChild(document.createTextNode(euro(c)));});
      if(sp){r.classList.toggle('aus',sp.art==='aus');nm.appendChild(el('span','marke',sp.t));}
      else if(ak)nm.appendChild(el('span','marke',ak.a.m?'Mittag':'Aktion'));
      r.appendChild(nm);r.appendChild(pr);a.appendChild(r);});
    box.appendChild(a);});
  return box;}
function zeilen(g){return g.abschnitte.reduce(function(s,a){return s+1.2+a.gerichte.length;},2);}
function heuteSeite(n){
  var s=el('div','seite'),h=el('div','heute');h.appendChild(el('h2',null,'Heute bei Saray'));var karten=0;
  D.aktionen.forEach(function(a){if(n.iso<a.von||n.iso>a.bis||(a.tage&&a.tage.indexOf(n.tag)<0)||(a.laden&&a.laden!==LADEN))return;
    if(a.zb!=null&&n.min>=a.zb)return;
    Object.keys(a.p).forEach(function(k){var x=D.index[k];if(!x||karten>=6)return;karten++;
      var c=el('div','karte rot');c.appendChild(el('span','kl',(a.m?'Mittagstisch':'Aktion')+(a.za!=null?' · '+uhr(a.za).replace(' Uhr','')+'–'+uhr(a.zb):'')));
      if(D.fotos[k])c.appendChild(Object.assign(el('img'),{src:D.fotos[k],alt:''}));
      c.appendChild(el('b',null,(x.nr?x.nr+' · ':'')+x.name));if(x.desc)c.appendChild(el('span',null,x.desc));
      var gp=el('span','gp');gp.appendChild(el('s',null,euro(x.p[0])));gp.appendChild(document.createTextNode(euro(a.p[k][0])+' €'));c.appendChild(gp);h.appendChild(c);});});
  D.empf.forEach(function(k){var x=D.index[k];if(!x||karten>=6||sperre(k,n))return;karten++;
    var c=el('div','karte');c.appendChild(el('span','kl','Wir empfehlen'));
    if(D.fotos[k])c.appendChild(Object.assign(el('img'),{src:D.fotos[k],alt:''}));
    c.appendChild(el('b',null,(x.nr?x.nr+' · ':'')+x.name));if(x.desc)c.appendChild(el('span',null,x.desc));
    var ak=aktion(k,0,n);c.appendChild(el('span','gp',euro(ak?ak.c:x.p[0])+' €'));h.appendChild(c);});
  s.appendChild(h);return s;}
var seiten=[],jetztI=0,timer=null;
function aufbauen(){
  var n=teile(),main=document.getElementById('main');
  main.querySelectorAll('.seite').forEach(function(x){x.remove();});seiten=[];
  if(!NUR.length||NUR.indexOf('heute')>-1)seiten.push(heuteSeite(n));
  var gs=D.gruppen.filter(function(g){return !NUR.length||NUR.indexOf(g.id)>-1;}),grenze=window.innerWidth>window.innerHeight?44:30,akt=null,summe=0;
  gs.forEach(function(g){var z=zeilen(g);if(!akt||summe+z>grenze){akt=el('div','seite');akt.appendChild(el('div','spalten'));seiten.push(akt);summe=0;}
    akt.firstChild.appendChild(gruppeEl(g,n));summe+=z;});
  seiten.forEach(function(s){main.appendChild(s);});
  /* zu voll? Schrift verkleinern, bis alles passt */
  seiten.forEach(function(s){s.classList.add('an');var sp=s.querySelector('.spalten');if(sp){var g=1;
    function zuViel(){var r=sp.getBoundingClientRect(),l=sp.lastElementChild&&sp.lastElementChild.lastElementChild;
      return [].some.call(sp.querySelectorAll('.g'),function(x){var q=x.getBoundingClientRect();return q.right>r.right+2||q.bottom>r.bottom+2;});}
    while(g>.5&&zuViel()){g-=.03;s.style.setProperty('--g',g.toFixed(2));}}
    s.classList.remove('an');});
  var pk=document.getElementById('punkte');pk.textContent='';seiten.forEach(function(){pk.appendChild(el('i'));});
  if(jetztI>=seiten.length)jetztI=0;zeigen();
  var b=document.getElementById('baender');b.textContent='';
  var aus=[];REGELN.forEach(function(r){[].concat(r.was||[]).forEach(function(v){v=String(v);if(v.indexOf('z:')===0&&!r.ab&&!r.bis&&gilt(r,n)&&aus.indexOf(v.slice(2))<0)aus.push(v.slice(2));});});
  if(aus.length){var t='Heute leider ohne: '+aus.join(', '),bl=aus.filter(function(z){return D.beilagen.indexOf(z)>-1;});
    if(bl.length)t+=' – Gerichte mit '+bl.join(' oder ')+' '+euro(D.rabatt)+' € günstiger';b.appendChild(el('div','band',t));}
  if(D.laeden[LADEN].warte&&D.laeden[LADEN].warte.datum===n.iso)b.appendChild(el('div','band blau','Gerade viel los – Wartezeit ca. '+D.laeden[LADEN].warte.min+' Minuten'));
  oeffnung(n);}
function zeigen(){seiten.forEach(function(s,i){s.classList.toggle('an',i===jetztI);});
  [].forEach.call(document.querySelectorAll('#punkte i'),function(p,i){p.classList.toggle('an',i===jetztI);});}
function weiter(){if(seiten.length>1){jetztI=(jetztI+1)%seiten.length;zeigen();}}
function uhrZeigen(){var n=teile();document.getElementById('uhr').textContent=n.hh+':'+n.mm;}
var letzteMin=-1;
setInterval(function(){uhrZeigen();var n=teile();if(n.min!==letzteMin){letzteMin=n.min;if(n.min%5===0)aufbauen();else oeffnung(n);}},1000);
timer=setInterval(weiter,SEK*1000);
function statusLaden(){fetch('../status.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():{};}).then(function(d){
  var neu=D.regeln.concat(Array.isArray(d.regeln)?d.regeln:[]);if(JSON.stringify(neu)!==JSON.stringify(REGELN)){REGELN=neu;aufbauen();}}).catch(function(){});}
function versionPruefen(){fetch('../version.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():null;}).then(function(v){
  if(v&&v.v&&v.v!==D.version)location.reload();}).catch(function(){});}
setInterval(statusLaden,60000);setInterval(versionPruefen,300000);
window.addEventListener('resize',function(){clearTimeout(window._rz);window._rz=setTimeout(aufbauen,300);});
/* Bildschirm nicht abdunkeln (wo der Browser es kann) */
function wach(){try{if(navigator.wakeLock)navigator.wakeLock.request('screen').catch(function(){});}catch(e){}}
document.addEventListener('visibilitychange',function(){if(!document.hidden)wach();});wach();
uhrZeigen();aufbauen();statusLaden();if(document.fonts&&document.fonts.ready)document.fonts.ready.then(aufbauen);
window.TV={aufbauen:aufbauen,weiter:weiter,seiten:function(){return seiten.length;}};
})();
</script>
</body>
</html>
"""

# ---------------------------------------------------------------- Küche
KUECHE = KOPF.replace("%%TITEL%%", "Saray Döner – Küche") + r"""
body{padding:0 0 40px}
.kopf{position:sticky;top:0;z-index:5;display:flex;flex-wrap:wrap;align-items:center;gap:10px;padding:12px 16px;background:var(--tinte);color:var(--gelb)}
.kopf h1{font-size:1.4rem;flex:1}
.chips{display:flex;gap:6px}
.chip{min-height:40px;padding:0 14px;border-radius:99px;border:2px solid var(--gelb);background:none;color:var(--gelb);font-weight:700;cursor:pointer}
.chip[aria-pressed=true]{background:var(--gelb);color:var(--tinte)}
.leer{max-width:640px;margin:24px auto;padding:0 16px;font-size:1.1rem;line-height:1.5}
.liste{display:grid;grid-template-columns:repeat(auto-fill,minmax(320px,1fr));gap:14px;padding:16px;align-items:start}
.bon{background:#fff;border:3px solid var(--tinte);border-radius:18px;padding:14px 16px;display:flex;flex-direction:column;gap:8px}
.bon.bald{border-color:var(--paprika);box-shadow:0 0 0 3px var(--paprika)}
.bon.spaet{background:#FFE9E3}
.bon.neu{animation:neu 1.2s ease 3}
@keyframes neu{50%{box-shadow:0 0 0 8px var(--gelb)}}
.bon-kopf{display:flex;justify-content:space-between;align-items:baseline;gap:8px}
.bnr{font:700 2.2rem "Saray Slab",serif;line-height:1}
.zeit{font:700 1.5rem "Saray Slab",serif;text-align:right}
.zeit small{display:block;font:700 .95rem "Saray Text";color:var(--tinte-weich)}
.bon.spaet .zeit small,.bon.bald .zeit small{color:var(--paprika)}
.meta{font-weight:700;color:var(--tinte-weich)}
.test{display:inline-block;background:var(--paprika);color:#fff;border-radius:99px;padding:1px 8px;font-size:.8rem;margin-left:6px}
.pos{list-style:none;margin:0;padding:0;border-top:2px dashed var(--linie)}
.pos li{display:flex;gap:10px;padding:10px 0;border-bottom:1px solid var(--linie);cursor:pointer;font-size:1.15rem;line-height:1.3}
.pos li .m{font:700 1.4rem "Saray Slab",serif;min-width:2.2em}
.pos li .w{display:block;font-size:.95rem;color:var(--tinte-weich)}
.pos li .n{display:block;font-size:.95rem;font-weight:700;color:var(--paprika)}
.pos li.ok{opacity:.4;text-decoration:line-through}
.pos li .hk{margin-left:auto;width:30px;height:30px;flex:none;border:3px solid var(--tinte);border-radius:8px;display:grid;place-items:center;font-weight:700}
.pos li.ok .hk::after{content:"✓"}
.summe{display:flex;justify-content:space-between;font-weight:700;font-size:1.1rem}
.knoepfe{display:flex;gap:8px}
.knopf{flex:1;min-height:48px;border-radius:12px;border:2px solid var(--tinte);background:#fff;color:var(--tinte);font-weight:700;cursor:pointer}
.knopf.voll{background:var(--tinte);color:var(--gelb)}
details.erledigt{margin:8px 16px}
details.erledigt summary{cursor:pointer;font-weight:700;padding:10px 0}
details.erledigt .liste{padding:8px 0}
details.erledigt .bon{opacity:.6}
@media print{
  body{background:#fff;padding:0}
  .kopf,.leer,details.erledigt,.knoepfe,.bon:not(.druck){display:none!important}
  .liste{display:block;padding:0}
  .bon.druck{border:0;box-shadow:none;width:72mm;padding:0;font-size:12pt;break-after:page}
  .pos li.ok{opacity:1;text-decoration:none}.pos li .hk{display:none}
  @page{size:80mm auto;margin:4mm}
}
</style>
</head>
<body>
<header class="kopf"><h1>Küche · Saray Döner</h1><div class="chips" id="filter"></div></header>
<p class="leer" id="leer" hidden>Noch keine offenen Bestellungen. Sie erscheinen hier, wenn Sie in der WhatsApp-Nachricht eines Gastes auf den Link
„Für die Küche“ tippen. Die Bestellungen bleiben auf diesem Gerät gespeichert, sortiert nach Abholzeit. Antippen hakt ein Gericht ab.</p>
<div class="liste" id="offen"></div>
<details class="erledigt" id="erledigt-box" hidden><summary id="erledigt-titel">Erledigt</summary><div class="liste" id="erledigt"></div></details>
<script>
(function(){
'use strict';
var LAEDEN=%%LAEDEN%%,K='saray-kueche',F='saray-kueche-filter',liste=[],filter='';
try{liste=JSON.parse(localStorage.getItem(K)||'[]');if(!Array.isArray(liste))liste=[];}catch(e){liste=[];}
try{filter=localStorage.getItem(F)||'';}catch(e){}
function speichern(){try{localStorage.setItem(K,JSON.stringify(liste));}catch(e){}}
function el(t,c,x){var e=document.createElement(t);if(c)e.className=c;if(x!=null)e.textContent=x;return e;}
function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
function lesen(b){try{var t=decodeURIComponent(escape(atob(b.replace(/-/g,'+').replace(/_/g,'/'))));var o=JSON.parse(t);
  if(!o||typeof o.nr!=='string'||!Array.isArray(o.p))return null;
  o.p=o.p.filter(Array.isArray).slice(0,60).map(function(x){return {q:Math.max(1,Math.min(99,+x[0]||1)),n:String(x[1]||'').slice(0,120),w:String(x[2]||'').slice(0,300),f:String(x[3]||'').slice(0,40),x:String(x[4]||'').slice(0,200),c:+x[5]||0,ok:false};});
  return {id:o.nr+'-'+(+o.a||0),nr:o.nr.slice(0,8),l:LAEDEN[o.l]?o.l:'',z:String(o.z||'').slice(0,60),t:/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}$/.test(o.t||'')?o.t:'',
    m:String(o.m||'').slice(0,40),s:+o.s||0,p:o.p,zug:String(o.zug||'').slice(0,5),test:!!o.test,a:+o.a||Date.now(),fertig:0,neu:1};}catch(e){return null;}}
/* Link aus WhatsApp: Bestellung übernehmen (doppelt geöffnet = einmal gespeichert) */
var m=/[#&]b=([A-Za-z0-9_-]+)/.exec(location.hash);
if(m){var o=lesen(m[1]);if(o&&!liste.some(function(x){return x.id===o.id;}))liste.push(o);speichern();history.replaceState(null,'',location.pathname+location.search);}
/* alte Bestellungen (älter als 3 Tage) aufräumen */
liste=liste.filter(function(x){return x&&Array.isArray(x.p)&&Date.now()-x.a<3*864e5;});speichern();
function zeitpunkt(x){return x.t?new Date(x.t+':00').getTime():x.a+20*60000;}
function rest(x){return Math.round((zeitpunkt(x)-Date.now())/60000);}
function filterZeigen(){var f=document.getElementById('filter');f.textContent='';[['','Alle']].concat(Object.keys(LAEDEN).map(function(k){return [k,LAEDEN[k]];})).forEach(function(o){
  var b=el('button','chip',o[1]);b.type='button';b.setAttribute('aria-pressed',String(filter===o[0]));
  b.addEventListener('click',function(){filter=o[0];try{localStorage.setItem(F,filter);}catch(e){}filterZeigen();zeichnen();});f.appendChild(b);});}
function bon(x){
  var b=el('article','bon'),r=rest(x);if(!x.fertig){if(r<0)b.classList.add('spaet');else if(r<=15)b.classList.add('bald');}if(x.neu)b.classList.add('neu');
  b.dataset.id=x.id;
  var k=el('div','bon-kopf'),nr=el('span','bnr',x.nr);if(x.test)nr.appendChild(el('span','test','TEST'));k.appendChild(nr);
  var z=el('span','zeit',x.t?x.t.slice(11):'sofort');
  z.appendChild(el('small',null,x.fertig?'erledigt':r<0?'seit '+(-r)+' Min. fällig':r===0?'jetzt':'in '+(r>=120?Math.round(r/60)+' Std.':r+' Min.')));k.appendChild(z);b.appendChild(k);
  b.appendChild(el('div','meta',[x.m||'ohne Name',LAEDEN[x.l]||'',x.zug?'Zug '+x.zug:'',x.z].filter(Boolean).join(' · ')));
  var ul=el('ul','pos');x.p.forEach(function(p){var li=el('li',p.ok?'ok':'');li.appendChild(el('span','m',p.q+'×'));
    var t=el('span',null,p.n);if(p.w)t.appendChild(el('span','w',p.w));if(p.f)t.appendChild(el('span','w','für '+p.f));if(p.x)t.appendChild(el('span','n','Wunsch: '+p.x));li.appendChild(t);
    li.appendChild(el('span','hk'));li.setAttribute('role','checkbox');li.setAttribute('aria-checked',String(p.ok));li.tabIndex=0;
    function um(){p.ok=!p.ok;x.neu=0;speichern();zeichnen();}
    li.addEventListener('click',um);li.addEventListener('keydown',function(ev){if(ev.key===' '||ev.key==='Enter'){ev.preventDefault();um();}});ul.appendChild(li);});
  b.appendChild(ul);
  var s=el('div','summe');s.appendChild(el('span',null,'Summe (bar)'));s.appendChild(el('span',null,euro(x.s)));b.appendChild(s);
  var kn=el('div','knoepfe'),dr=el('button','knopf','Bon drucken'),fe=el('button','knopf voll',x.fertig?'Zurückholen':'Fertig ✓');dr.type=fe.type='button';
  dr.addEventListener('click',function(){document.querySelectorAll('.bon.druck').forEach(function(y){y.classList.remove('druck');});b.classList.add('druck');window.print();});
  fe.addEventListener('click',function(){x.fertig=x.fertig?0:Date.now();x.neu=0;speichern();zeichnen();});
  kn.appendChild(dr);kn.appendChild(fe);b.appendChild(kn);return b;}
function zeichnen(){
  var sicht=liste.filter(function(x){return !filter||x.l===filter;}),offen=sicht.filter(function(x){return !x.fertig;}).sort(function(a,b){return zeitpunkt(a)-zeitpunkt(b);}),
    fertig=sicht.filter(function(x){return x.fertig;}).sort(function(a,b){return b.fertig-a.fertig;});
  var o=document.getElementById('offen');o.textContent='';offen.forEach(function(x){o.appendChild(bon(x));});
  document.getElementById('leer').hidden=offen.length>0;
  var e=document.getElementById('erledigt');e.textContent='';fertig.forEach(function(x){e.appendChild(bon(x));});
  document.getElementById('erledigt-box').hidden=!fertig.length;document.getElementById('erledigt-titel').textContent='Erledigt ('+fertig.length+')';
  document.title=(offen.length?'('+offen.length+') ':'')+'Küche · Saray Döner';}
window.addEventListener('storage',function(ev){if(ev.key===K){try{liste=JSON.parse(ev.newValue||'[]');}catch(e){}zeichnen();}});
window.addEventListener('hashchange',function(){var m2=/[#&]b=([A-Za-z0-9_-]+)/.exec(location.hash);if(!m2)return;var o2=lesen(m2[1]);
  if(o2&&!liste.some(function(x){return x.id===o2.id;}))liste.push(o2);speichern();history.replaceState(null,'',location.pathname+location.search);zeichnen();});
setInterval(zeichnen,30000);
setTimeout(function(){var neu=liste.some(function(x){return x.neu;});liste.forEach(function(x){x.neu=0;});if(neu)speichern();},4000);
filterZeigen();zeichnen();
})();
</script>
</body>
</html>
"""


def schreiben(aus, daten, laeden, seite_url, version):
    """daten: dict für den Bildschirm (siehe build.py); laeden: {id: name}; seite_url: Adresse für den QR-Code."""
    anzeige = seite_url.rstrip("/").replace("https://", "")
    (aus / "tv").mkdir(exist_ok=True)
    (aus / "tv" / "index.html").write_text(
        TV.replace("%%DATEN%%", json.dumps(daten, ensure_ascii=False, separators=(",", ":")))
          .replace("%%QR%%", qr_svg(seite_url, ecl="M", farbe="#3A1531", rand=1))
          .replace("%%ADRESSE%%", anzeige), encoding="utf-8")
    (aus / "kueche").mkdir(exist_ok=True)
    (aus / "kueche" / "index.html").write_text(KUECHE.replace("%%LAEDEN%%", json.dumps(laeden, ensure_ascii=False)), encoding="utf-8")
    (aus / "version.json").write_text(json.dumps({"v": version}) + "\n")
