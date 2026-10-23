"""Seiten für den Laden selbst (nicht für Gäste):

docs/tv/      Speisekarte für einen Bildschirm im Laden (Fernseher mit Fire-TV-Stick o. Ä.).
              Gleiche Daten wie die Website: Preise, Aktionen, Mittagstisch, „heute aus“.
              Holt alle 60 s status.json (tagesaktuelle Sperren) und lädt sich neu, sobald die Seite neu gebaut wurde.
              Adresse: tv/?laden=freital  (weitere Parameter: sek=12 Sekunden je Seite, seiten=doener,pizza nur diese Gruppen)
docs/kueche/  Küchenansicht: Bestellungen aus dem Link „Für die Küche“ in der WhatsApp-Nachricht, groß und abhakbar,
              nach Abholzeit sortiert, mit Bon-Druck. Die Daten stehen im Link; gespeichert wird nur auf dem Gerät im Laden.
"""
import json

# Wörter, die auf eine Allergie oder Unverträglichkeit hindeuten (Deutsch, Englisch, Türkisch, Tschechisch, Russisch, Arabisch)
ALLERGIE_RE = 'allerg|unvertr[äa]g|intoleran|z[öo]liakie|gluten|laktose|lactose|milcheiwei|nuss|n[üu]sse|erdnuss|mandel|cashew|pistazie|sesam|soja|\\bei\\b|\\beier|eiwei|fisch|krebs|garnele|schalentier|weichtier|muschel|sellerie|senf|lupine|sulfit|schwefel|histamin|fru[ck]tose|glutamat|halal|schwein|celiac|coeliac|dairy|\\bnuts?\\b|peanut|almond|sesame|\\bsoy|\\begg|shellfish|mustard|celery|sulphite|sulfite|alerji|laktoz|f[ıi]st[ıi]k|f[ıi]nd[ıi]k|ceviz|susam|soya|yumurta|helal|domuz|alergi|lepek|lakt[óo]z|o[řr]ech|ara[šs][íi]d|sezam|s[óo]ja|vejce|аллерг|глютен|лактоз|орех|арахис|кунжут|соя|яйц|حساسية|جلوتين|لاكتوز|مكسرات|سمسم|صويا|بيض|حلال'

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
.fenster .fuss{display:none}
.fenster .heute{grid-template-columns:repeat(3,1fr);grid-template-rows:auto;grid-auto-rows:minmax(0,1fr);height:100%;align-content:stretch}
.fenster .karte{overflow:hidden}
.fenster .heute>h2{font-size:6vh;line-height:1.1}
.fenster .karte b{font-size:4.2vh}.fenster .karte span{font-size:2.6vh}.fenster .karte .gp{font-size:6vh}
.fenster .qr-gross{grid-row:span 2;align-items:center;justify-content:center;text-align:center;background:var(--tinte);color:#fff;border-color:var(--tinte)}
.fenster .qr-gross .kl{color:var(--gelb);font-size:3vh}
.qr-bild{background:#fff;padding:1.2vh;border-radius:1.6vh;width:min(100%,38vh);aspect-ratio:1;flex:none}.qr-bild svg{width:100%;height:100%;display:block}
.fenster .kopf h1{font-size:5.4vh}.fenster .status{font-size:3.4vh}.fenster .uhr{font-size:5vh}
@media (orientation:portrait){.fenster .heute{grid-template-columns:repeat(2,1fr)}}
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
var q=new URLSearchParams(location.search),LADEN=q.get('laden'),FENSTER=q.get('modus')==='fenster',SEK=Math.max(6,Math.min(120,+q.get('sek')||14)),NUR=(q.get('seiten')||'').split(',').filter(Boolean);
if(!D.laeden[LADEN]){
  document.body.innerHTML='<div class="wahl"><p>Welcher Laden?</p>'+Object.keys(D.laeden).map(function(k){return '<a href="?laden='+k+'">'+D.laeden[k].name+'</a>';}).join('')+'<p style="font-size:2vh">Tipp: Adresse als Startseite im Browser des Fernsehers speichern.</p></div>';
  return;
}
document.getElementById('ort').textContent=D.laeden[LADEN].name;if(FENSTER)document.body.classList.add('fenster');
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
  var s=el('div','seite'),h=el('div','heute');h.appendChild(el('h2',null,'Heute bei Saray'));var karten=FENSTER?2:0;
  if(FENSTER){var qk=el('div','karte qr-gross');qk.appendChild(el('span','kl','Jetzt vorbestellen'));
    var qb=el('div','qr-bild');qb.innerHTML=document.querySelector('.fuss .qr').innerHTML;qk.appendChild(qb);
    qk.appendChild(el('b',null,'Handy-Kamera drauf'));qk.appendChild(el('span',null,'Per WhatsApp bestellen, ohne Warten abholen. Nur Barzahlung.'));h.appendChild(qk);}
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
  if(FENSTER||!NUR.length||NUR.indexOf('heute')>-1)seiten.push(heuteSeite(n));
  var gs=FENSTER?[]:D.gruppen.filter(function(g){return !NUR.length||NUR.indexOf(g.id)>-1;}),grenze=window.innerWidth>window.innerHeight?44:30,akt=null,summe=0;
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
.summe{display:flex;justify-content:space-between;font-weight:700;font-size:1.1rem}.summe.rabatt{font-size:.95rem;color:var(--gruen)}
.knoepfe{display:flex;gap:8px}
.knopf{flex:1;min-height:48px;border-radius:12px;border:2px solid var(--tinte);background:#fff;color:var(--tinte);font-weight:700;cursor:pointer}
.knopf.voll{background:var(--tinte);color:var(--gelb)}
details.erledigt{margin:8px 16px}
.chips.hell .chip{border-color:var(--tinte);color:var(--tinte)}.chips.hell .chip[aria-pressed=true]{background:var(--tinte);color:var(--gelb)}
.abschluss table{border-collapse:collapse;width:100%;max-width:560px;margin:10px 0;background:#fff;border-radius:12px;overflow:hidden}
.abschluss td,.abschluss th{padding:8px 12px;border-bottom:1px solid var(--linie);text-align:left}.abschluss td.z{text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
.zahlen{display:flex;flex-wrap:wrap;gap:10px;margin:10px 0}.zahlen div{background:#fff;border:2px solid var(--tinte);border-radius:14px;padding:10px 14px;min-width:130px}
.zahlen b{display:block;font:700 1.6rem "Saray Slab",serif}.zahlen span{font-size:.9rem;color:var(--tinte-weich)}
.klein{font-size:.85rem;color:var(--tinte-weich)}
.allergie-band{background:var(--paprika);color:#fff;font-weight:700;border-radius:10px;padding:8px 10px;font-size:1.05rem}
.bon.allergie{border-color:var(--paprika);border-width:4px}.pos li .n.al{background:#FFE1D9;padding:2px 6px;border-radius:6px}
#plan table{border-collapse:collapse;width:100%}#plan th,#plan td{border-bottom:1px solid #999;padding:4px 6px;text-align:left;vertical-align:top;font-size:11pt}
#plan h1{font:700 18pt "Saray Slab",serif;margin:0 0 8px}#plan .al{color:#C8381E;font-weight:700}
body.plan-druck>*:not(#plan){display:none!important}body.plan-druck #plan{display:block!important}
.tel{margin:12px 16px;padding:14px 16px;background:#fff;border:3px solid var(--tinte);border-radius:18px;max-width:640px}
.tel h2{font:700 1.3rem "Saray Slab",serif;margin:0 0 10px}.tel label{display:block;font-weight:700;margin:8px 0 4px}
.tel input{display:block;width:100%;min-height:46px;border:2px solid var(--tinte);border-radius:12px;padding:0 12px;font:inherit;margin-top:4px}
.tel-reihe{display:flex;gap:10px}.tel-reihe label{flex:1}
#tel-treffer button{display:flex;width:100%;justify-content:space-between;gap:10px;min-height:44px;padding:0 12px;margin:4px 0;border:1px solid var(--linie);border-radius:10px;background:var(--gelb-blass);font:inherit;cursor:pointer;text-align:left}
.tel .pos li{cursor:default;align-items:center}.tel .pos input{min-height:38px;margin:4px 0 0;font-size:.95rem}
.tel .menge{display:flex;gap:6px;align-items:center}.tel .menge button{width:36px;height:36px;border-radius:50%;border:2px solid var(--tinte);background:#fff;font-weight:700;cursor:pointer}
.fehler{color:var(--paprika);font-weight:700}
.tel-marke.stamm{background:#E8A317;color:var(--tinte)}.tel-marke{display:inline-block;background:var(--tinte);color:var(--gelb);border-radius:99px;padding:1px 8px;font-size:.8rem;margin-left:6px}
.monat{background:#fff;border:2px solid var(--tinte);border-radius:14px;padding:12px 14px;margin:10px 0;max-width:620px}
body.monat-druck>*:not(#jahr){display:none!important}
.warte-vorschlag{margin:12px 16px 0;padding:12px 14px;border-radius:14px;background:var(--paprika);color:#fff;display:flex;flex-wrap:wrap;gap:10px;align-items:center;font-weight:700}
.warte-vorschlag[hidden]{display:none}.warte-vorschlag span{flex:1 1 240px}.warte-vorschlag button{min-height:44px;padding:0 16px;border-radius:12px;border:2px solid #fff;background:#fff;color:var(--paprika);font-weight:700;cursor:pointer}
.warte-vorschlag button.zweit{background:none;color:#fff}
.slot-info{margin:10px 16px 0;padding:10px 14px;border-radius:12px;background:#fff;border:2px solid var(--paprika);font-weight:700}.slot-info[hidden]{display:none}
.balken{display:grid;grid-template-columns:4.5em 1fr 4em;gap:6px 10px;align-items:center;max-width:560px;margin:10px 0}
.balken i{display:block;height:16px;border-radius:8px;background:var(--tinte);min-width:2px}
.balken span:nth-child(3n){text-align:right;font-weight:700;font-variant-numeric:tabular-nums}
.bedarf table{border-collapse:collapse;margin:8px 0;background:#fff;border-radius:12px;overflow:hidden;min-width:280px}
.bedarf td{padding:8px 12px;border-bottom:1px solid var(--linie);font-size:1.1rem}.bedarf td.z{text-align:right;font:700 1.3rem "Saray Slab",serif}
body.jahr-druck>*:not(#jahr){display:none!important}
.knoepfe.zwei{margin-top:-2px}
.knopf.ok{border-color:var(--gruen);color:var(--gruen)}
.gesendet{position:fixed;left:50%;bottom:16px;transform:translateX(-50%);background:var(--tinte);color:#fff;padding:10px 16px;border-radius:12px;font-weight:700;z-index:9;max-width:90vw}
details.erledigt summary{cursor:pointer;font-weight:700;padding:10px 0}
details.erledigt .liste{padding:8px 0}
details.erledigt .bon{opacity:.6}
@media print{
  body{background:#fff;padding:0}
  .kopf,.leer,details.erledigt,.knoepfe,.bon:not(.druck),.gesendet{display:none!important}
  .liste{display:block;padding:0}
  .bon.druck{border:0;box-shadow:none;width:72mm;padding:0;font-size:12pt;break-after:page}
  .pos li.ok{opacity:1;text-decoration:none}.pos li .hk{display:none}
  body.jahr-druck .bon.druck,body.monat-druck .bon.druck{display:none}
  body.monat-druck #jahr{display:block!important;margin:0}body.monat-druck #jahr>*:not(#monat-box){display:none!important}body.monat-druck #monat-box .knoepfe,body.monat-druck #monat-wahl{display:none}
  body.jahr-druck #jahr{display:block!important;margin:0}body.jahr-druck #jahr summary,body.jahr-druck .knoepfe,body.jahr-druck #jahr-wahl{display:none}
  .bon.druck{page:bon}
  @page bon{size:80mm auto;margin:4mm}
  @page{size:A4;margin:15mm}
}
</style>
</head>
<body>
<header class="kopf"><h1>Küche · Saray Döner</h1><button class="chip" type="button" id="tel-neu">📞 Telefonbestellung</button><button class="chip" type="button" id="plan-knopf">🖨 Tagesplan</button><button class="chip" type="button" id="sync-knopf">📲 An anderes Gerät</button><div class="chips" id="filter"></div></header>
<section class="tel" id="tel" hidden aria-label="Telefonbestellung"><h2>📞 Telefonbestellung</h2>
<div class="chips hell" id="tel-laden"></div>
<div class="tel-reihe"><label>Name<input id="tel-name" type="text" maxlength="40" autocomplete="off"></label><label>Abholung<input id="tel-zeit" type="time" step="300"></label></div>
<label>Gericht suchen<input id="tel-such" type="search" placeholder="Name oder Nummer" autocomplete="off"></label><div id="tel-treffer"></div>
<ul class="pos" id="tel-pos"></ul><div class="summe"><span>Summe (bar)</span><span id="tel-summe">0,00 €</span></div>
<p class="fehler" id="tel-fehler" hidden></p>
<div class="knoepfe"><button class="knopf" type="button" id="tel-ab">Abbrechen</button><button class="knopf voll" type="button" id="tel-ok">Bestellung anlegen</button></div></section>
<p class="leer" id="leer" hidden>Noch keine offenen Bestellungen. Sie erscheinen hier, wenn Sie in der WhatsApp-Nachricht eines Gastes auf den Link
„Für die Küche“ tippen. Die Bestellungen bleiben auf diesem Gerät gespeichert, sortiert nach Abholzeit. Antippen hakt ein Gericht ab.</p>
<div class="warte-vorschlag" id="warte-vorschlag" hidden></div>
<p class="slot-info" id="slot-info" hidden></p>
<details class="erledigt bedarf" id="bedarf" hidden><summary id="bedarf-titel">Was brauchen wir?</summary>
<div class="chips hell" id="bedarf-wahl"></div><table id="bedarf-liste"></table></details>
<div class="liste" id="offen"></div>
<details class="erledigt" id="erledigt-box" hidden><summary id="erledigt-titel">Erledigt</summary><div class="liste" id="erledigt"></div></details>
<details class="erledigt abschluss" id="abschluss"><summary>Tagesabschluss</summary>
<div class="chips hell" id="abschluss-tag"></div><div id="abschluss-inhalt"></div>
<p class="klein">Nur Bestellungen, die auf diesem Gerät geöffnet wurden (die letzten 7 Tage). Ersetzt keine Kasse und kein Kassenbuch.</p></details>
<details class="erledigt abschluss" id="jahr"><summary>Jahresrückblick</summary>
<div id="monat-box"><h3>Monatsbericht</h3><div class="chips hell" id="monat-wahl"></div><div id="monat-inhalt"></div>
<div class="knoepfe" style="max-width:420px"><button class="knopf" type="button" id="monat-drucken">Drucken</button><button class="knopf voll" type="button" id="monat-teilen">Per WhatsApp schicken</button></div></div>
<div class="chips hell" id="jahr-wahl"></div><div id="jahr-inhalt"></div>
<p class="klein">Zählt jede Bestellung, die auf diesem Gerät geöffnet wurde (ohne Testbestellungen), ab dem ersten Öffnen. Bleibt gut ein Jahr auf dem Gerät.</p>
<div class="knoepfe" style="max-width:320px"><button class="knopf" type="button" id="jahr-drucken">Rückblick drucken</button></div></details>
<section id="plan" hidden></section>
<p class="gesendet" id="gesendet" role="status" hidden></p>
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
    m:String(o.m||'').slice(0,40),s:+o.s||0,r:+o.r||0,rc:String(o.rc||'').slice(0,60),p:o.p,w:Array.isArray(o.w)?o.w.slice(0,60):[],g:String(o.g||'').slice(0,12),c:Math.max(0,Math.min(9999,+o.c||0)),sp:/^(de|en|cs|tr|ru|ar)$/.test(o.sp||'')?o.sp:'de',zug:String(o.zug||'').slice(0,5),f:String(o.f||'').replace(/[^a-z0-9]/g,'').slice(0,24),test:!!o.test,a:+o.a||Date.now(),fertig:0,neu:1};}catch(e){return null;}}
/* Link aus WhatsApp: Bestellung übernehmen (doppelt geöffnet = einmal gespeichert) */
var m=/[#&]b=([A-Za-z0-9_-]+)/.exec(location.hash);
/* Jahresstatistik: pro Tag Bestellungen, Summe, Gerichte, Uhrzeiten, Sprachen, Laden (ohne Tests) */
var JK='saray-kueche-jahr',JAHR={};try{JAHR=JSON.parse(localStorage.getItem(JK)||'{}')||{};}catch(e){JAHR={};}
function jahrZaehlen(x){if(x.test)return;var d=x.t?x.t.slice(0,10):new Date(x.a).toISOString().slice(0,10),j=JAHR[d]=JAHR[d]||{n:0,s:0,g:{},h:{},sp:{},l:{}};if(x.tel)j.tel=(j.tel||0)+1;
  j.n++;j.s+=x.s;x.p.forEach(function(p){var n=p.n.replace(/\s*\(.*\)$/,'');j.g[n]=(j.g[n]||0)+p.q;});
  if(x.t){var h=x.t.slice(11,13);j.h[h]=(j.h[h]||0)+1;}j.sp[x.sp]=(j.sp[x.sp]||0)+1;if(x.l)j.l[x.l]=(j.l[x.l]||0)+1;
  var grenze=new Date(Date.now()-400*864e5).toISOString().slice(0,10);Object.keys(JAHR).forEach(function(k){if(k<grenze)delete JAHR[k];});
  try{localStorage.setItem(JK,JSON.stringify(JAHR));}catch(e){}}
function aufnehmen(o){if(o&&!liste.some(function(x){return x.id===o.id;})){liste.push(o);jahrZaehlen(o);}}
if(m){aufnehmen(lesen(m[1]));speichern();history.replaceState(null,'',location.pathname+location.search);}
/* Bestellungen von einem anderen Gerät übernehmen (#sync=…): doppelte werden erkannt */
function syncLesen(){var s2=/[#&]sync=([A-Za-z0-9_-]+)/.exec(location.hash);if(!s2)return 0;var n=0;
  try{var d=JSON.parse(decodeURIComponent(escape(atob(s2[1].replace(/-/g,'+').replace(/_/g,'/')))));(d.o||[]).forEach(function(o){
    if(!o||typeof o.id!=='string'||!Array.isArray(o.p)||liste.some(function(x){return x.id===o.id;}))return;o.neu=0;aufnehmen(o);n++;});}catch(e){}
  speichern();history.replaceState(null,'',location.pathname+location.search);return n;}
var syncN=syncLesen();
/* alte Bestellungen (älter als 3 Tage) aufräumen */
liste=liste.filter(function(x){return x&&Array.isArray(x.p)&&Date.now()-x.a<7*864e5;});speichern();
/* Antworten an den Gast in seiner Sprache (Sprache der Website beim Bestellen) */
var TEXTE={
  de:{nochmal:'Nächstes Mal mit einem Tipp genau so bestellen:',hallo:'Hallo',heute:'heute um {z} Uhr',tag:'am {d} um {z} Uhr',ok:'{hallo}, danke für Ihre Bestellung {nr}! Sie ist {wann} in {ort} abholbereit. Bitte bar bezahlen: {summe}. Ihr Saray Döner',fertig:'Ihre Bestellung {nr} ist fertig und liegt in {ort} für Sie bereit. Bis gleich! Ihr Saray Döner'},
  en:{nochmal:'Order exactly the same again next time:',hallo:'Hello',heute:'today at {z}',tag:'on {d} at {z}',ok:'{hallo}, thank you for your order {nr}! It will be ready for pickup {wann} in {ort}. Please pay in cash: {summe}. Saray Döner',fertig:'Your order {nr} is ready for you in {ort}. See you soon! Saray Döner'},
  tr:{nochmal:'Bir dahaki sefere tek dokunuşla aynısını sipariş edin:',hallo:'Merhaba',heute:'bugün saat {z}',tag:'{d} saat {z}',ok:'{hallo}, {nr} numaralı siparişiniz için teşekkürler! Siparişiniz {wann} {ort} şubemizde hazır olacak. Lütfen nakit ödeyin: {summe}. Saray Döner',fertig:'{nr} numaralı siparişiniz {ort} şubemizde hazır. Görüşmek üzere! Saray Döner'},
  cs:{nochmal:'Příště objednáte totéž jedním klepnutím:',hallo:'Dobrý den',heute:'dnes v {z}',tag:'{d} v {z}',ok:'{hallo}, děkujeme za objednávku {nr}! Bude připravena k vyzvednutí {wann} v provozovně {ort}. Platba v hotovosti: {summe}. Saray Döner',fertig:'Vaše objednávka {nr} je hotová a čeká na vás v provozovně {ort}. Brzy na viděnou! Saray Döner'},
  ru:{nochmal:'В следующий раз закажите то же самое одним нажатием:',hallo:'Здравствуйте',heute:'сегодня в {z}',tag:'{d} в {z}',ok:'{hallo}! Спасибо за заказ {nr}! Его можно забрать {wann} в кафе {ort}. Оплата наличными: {summe}. Saray Döner',fertig:'Ваш заказ {nr} готов и ждёт вас в кафе {ort}. До встречи! Saray Döner'},
  ar:{nochmal:'في المرة القادمة اطلب الطلب نفسه بلمسة واحدة:',hallo:'مرحبًا',heute:'اليوم الساعة {z}',tag:'يوم {d} الساعة {z}',ok:'{hallo}، شكرًا لطلبك {nr}! سيكون جاهزًا للاستلام {wann} في فرع {ort}. الدفع نقدًا: {summe}. Saray Döner',fertig:'طلبك {nr} جاهز وبانتظارك في فرع {ort}. نراك قريبًا! Saray Döner'}};
var SP_NAME={de:'Deutsch',en:'Englisch',tr:'Türkisch',cs:'Tschechisch',ru:'Russisch',ar:'Arabisch'};
function fuell(t,w){return t.replace(/\{(\w+)\}/g,function(_,k){return w[k]!=null?w[k]:'';});}
function heuteISO(){var d=new Date();return d.getFullYear()+'-'+('0'+(d.getMonth()+1)).slice(-2)+'-'+('0'+d.getDate()).slice(-2);}
function antwort(x,art){var T=TEXTE[x.sp]||TEXTE.de,wann='';
  if(x.t){var d=x.t.slice(0,10),z=x.t.slice(11);wann=d===heuteISO()?fuell(T.heute,{z:z}):fuell(T.tag,{z:z,d:d.slice(8)+'.'+d.slice(5,7)+'.'});}
  var t=fuell(T[art],{hallo:T.hallo+(x.m?' '+x.m:''),nr:x.nr,wann:wann,ort:LAEDEN[x.l]||'',summe:euro(x.s)});
  if(art==='ok'&&x.w&&x.w.length)t+='\n\n'+T.nochmal+' '+nochmalLink(x);
  return t;}
function b64url(t){return btoa(unescape(encodeURIComponent(t))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
function nochmalLink(x){return location.origin+location.pathname.replace(/kueche\/?(index\.html)?$/,'')+'#nochmal='+b64url(JSON.stringify({l:x.l,p:x.w}));}
function melden(t){var g=document.getElementById('gesendet');g.textContent=t;g.hidden=false;clearTimeout(melden.t);melden.t=setTimeout(function(){g.hidden=true;},4000);}
/* WhatsApp öffnet die Kontaktauswahl: den Chat des Gastes antippen, senden */
/* „Abholbereit per Ton“: kurze Meldung an die offene Seite des Gastes (nur ok/fertig/zurueck, keine Bestelldaten) */
var NTFY=%%NTFY%%;
function tonMelden(x,art){if(!x.f||!NTFY)return;try{fetch(NTFY+'/saray-'+x.f,{method:'POST',body:art}).catch(function(){});}catch(e){}}
function senden(x,art){var t=antwort(x,art);x[art==='ok'?'bestaetigt':'gemeldet']=Date.now();x.neu=0;speichern();zeichnen();if(art==='ok')tonMelden(x,'ok');
  window.open('https://wa.me/?text='+encodeURIComponent(t),'_blank');
  melden((art==='ok'?'Bestätigung':'Fertig-Meldung')+(x.sp!=='de'?' auf '+SP_NAME[x.sp]:'')+' – in WhatsApp den Chat von '+(x.m||'dem Gast')+' wählen.');}
function zeitpunkt(x){return x.t?new Date(x.t+':00').getTime():x.a+20*60000;}
function rest(x){return Math.round((zeitpunkt(x)-Date.now())/60000);}
function filterZeigen(){var f=document.getElementById('filter');f.textContent='';[['','Alle']].concat(Object.keys(LAEDEN).map(function(k){return [k,LAEDEN[k]];})).forEach(function(o){
  var b=el('button','chip',o[1]);b.type='button';b.setAttribute('aria-pressed',String(filter===o[0]));
  b.addEventListener('click',function(){filter=o[0];try{localStorage.setItem(F,filter);}catch(e){}filterZeigen();zeichnen();});f.appendChild(b);});}
var ALLERGIE=new RegExp(%%ALLERGIE%%,'i');
function allergien(x){return x.p.map(function(p){return p.x;}).filter(function(t){return t&&ALLERGIE.test(t);});}
function bon(x){
  var b=el('article','bon'),r=rest(x),al=allergien(x);if(al.length)b.classList.add('allergie');if(!x.fertig){if(r<0)b.classList.add('spaet');else if(r<=15)b.classList.add('bald');}if(x.neu)b.classList.add('neu');
  b.dataset.id=x.id;
  var k=el('div','bon-kopf'),nr=el('span','bnr',x.nr);if(x.test)nr.appendChild(el('span','test','TEST'));k.appendChild(nr);
  var z=el('span','zeit',x.t?x.t.slice(11):'sofort');
  z.appendChild(el('small',null,x.fertig?'erledigt':r<0?'seit '+(-r)+' Min. fällig':r===0?'jetzt':'in '+(r>=120?Math.round(r/60)+' Std.':r+' Min.')));k.appendChild(z);b.appendChild(k);
  if(x.tel)nr.appendChild(el('span','tel-marke','📞 Telefon'));
  if(x.c>1)nr.appendChild(el('span','tel-marke'+(x.c>=5?' stamm':''),(x.c>=5?'⭐ Stammgast · ':'')+x.c+'. Bestellung'));
  if(al.length)b.appendChild(el('div','allergie-band','⚠ Allergie / Unverträglichkeit beachten: '+al.join(' · ')));
  b.appendChild(el('div','meta',[x.m||'ohne Name',LAEDEN[x.l]||'',x.zug?'Zug '+x.zug:'',x.z].filter(Boolean).join(' · ')));
  var ul=el('ul','pos');x.p.forEach(function(p){var li=el('li',p.ok?'ok':'');li.appendChild(el('span','m',p.q+'×'));
    var t=el('span',null,p.n);if(p.w)t.appendChild(el('span','w',p.w));if(p.f)t.appendChild(el('span','w','für '+p.f));if(p.x)t.appendChild(el('span','n'+(ALLERGIE.test(p.x)?' al':''),(ALLERGIE.test(p.x)?'⚠ ':'')+'Wunsch: '+p.x));li.appendChild(t);
    li.appendChild(el('span','hk'));li.setAttribute('role','checkbox');li.setAttribute('aria-checked',String(p.ok));li.tabIndex=0;
    function um(){p.ok=!p.ok;x.neu=0;speichern();zeichnen();}
    li.addEventListener('click',um);li.addEventListener('keydown',function(ev){if(ev.key===' '||ev.key==='Enter'){ev.preventDefault();um();}});ul.appendChild(li);});
  b.appendChild(ul);
  if(x.r){var rz=el('div','summe rabatt');rz.appendChild(el('span',null,'Firmen-Rabatt'+(x.rc?' ('+x.rc+')':'')));rz.appendChild(el('span',null,'−'+euro(x.r)));b.appendChild(rz);}
  var s=el('div','summe');s.appendChild(el('span',null,'Summe (bar)'));s.appendChild(el('span',null,euro(x.s)));b.appendChild(s);
  var kn=el('div','knoepfe'),dr=el('button','knopf','Bon drucken'),fe=el('button','knopf voll',x.fertig?'Zurückholen':'Fertig ✓');dr.type=fe.type='button';
  dr.addEventListener('click',function(){document.querySelectorAll('.bon.druck').forEach(function(y){y.classList.remove('druck');});b.classList.add('druck');window.print();});
  fe.addEventListener('click',function(){x.fertig=x.fertig?0:Date.now();x.neu=0;speichern();zeichnen();tonMelden(x,x.fertig?'fertig':'zurueck');
    if(x.fertig)melden(x.f?'Erledigt. Hat der Gast die Seite offen, hört er jetzt einen Ton. Unter „Erledigt“ können Sie ihm zusätzlich per WhatsApp Bescheid geben.':'Erledigt. Unter „Erledigt“ können Sie dem Gast Bescheid geben.');});
  kn.appendChild(dr);kn.appendChild(fe);b.appendChild(kn);
  var k2=el('div','knoepfe zwei');
  if(!x.fertig&&!x.tel){var be=el('button','knopf'+(x.bestaetigt?' ok':''),x.bestaetigt?'✓ Bestätigt':'Bestätigen');be.type='button';be.dataset.bestaetigen='';
    be.addEventListener('click',function(){senden(x,'ok');});k2.appendChild(be);}
  else if(!x.tel){var me=el('button','knopf'+(x.gemeldet?' ok':''),x.gemeldet?'✓ Gast Bescheid gegeben':'Gast: „Ist fertig“');me.type='button';me.dataset.melden='';
    me.addEventListener('click',function(){senden(x,'fertig');});k2.appendChild(me);}
  b.appendChild(k2);return b;}
function zeichnen(){
  var sicht=liste.filter(function(x){return !filter||x.l===filter;}),offen=sicht.filter(function(x){return !x.fertig;}).sort(function(a,b){return zeitpunkt(a)-zeitpunkt(b);}),
    fertig=sicht.filter(function(x){return x.fertig;}).sort(function(a,b){return b.fertig-a.fertig;});
  var o=document.getElementById('offen');o.textContent='';offen.forEach(function(x){o.appendChild(bon(x));});
  document.getElementById('leer').hidden=offen.length>0;
  var e=document.getElementById('erledigt');e.textContent='';fertig.forEach(function(x){e.appendChild(bon(x));});
  document.getElementById('erledigt-box').hidden=!fertig.length;document.getElementById('erledigt-titel').textContent='Erledigt ('+fertig.length+')';
  document.title=(offen.length?'('+offen.length+') ':'')+'Küche · Saray Döner';
  abschluss(sicht);bedarf(offen);jahrZeigen();monatZeigen();warteVorschlag();slotsPruefen();}
/* ---------- Telefonbestellung erfassen: landet in derselben Liste, im Tagesabschluss und im Jahresrückblick ---------- */
var KARTE=%%KARTE%%,telPos=[],telLaden='';
function telOeffnen(){var t=document.getElementById('tel');t.hidden=false;telPos=[];telLaden=filter||Object.keys(LAEDEN)[0];
  var d=new Date(Date.now()+20*60000),m=Math.ceil(d.getMinutes()/5)*5;d.setMinutes(m,0,0);
  document.getElementById('tel-zeit').value=('0'+d.getHours()).slice(-2)+':'+('0'+d.getMinutes()).slice(-2);
  document.getElementById('tel-name').value='';document.getElementById('tel-such').value='';document.getElementById('tel-treffer').textContent='';
  document.getElementById('tel-fehler').hidden=true;telZeichnen();document.getElementById('tel-name').focus();}
function telZeichnen(){
  var lb=document.getElementById('tel-laden');lb.textContent='';Object.keys(LAEDEN).forEach(function(id){var b=el('button','chip',LAEDEN[id]);b.type='button';
    b.setAttribute('aria-pressed',String(telLaden===id));b.addEventListener('click',function(){telLaden=id;telZeichnen();});lb.appendChild(b);});
  var ul=document.getElementById('tel-pos');ul.textContent='';var sum=0;
  telPos.forEach(function(p,i){sum+=p.c*p.q;var li=el('li');var mg=el('span','menge'),mi=el('button',null,'−'),pl=el('button',null,'+');mi.type=pl.type='button';
    mi.addEventListener('click',function(){if(p.q>1)p.q--;else telPos.splice(i,1);telZeichnen();});pl.addEventListener('click',function(){p.q++;telZeichnen();});
    mg.appendChild(mi);mg.appendChild(el('b',null,p.q+'×'));mg.appendChild(pl);li.appendChild(mg);
    var t=el('span');t.style.flex='1';t.appendChild(el('span',null,p.n));var no=el('input');no.placeholder='Wunsch (optional)';no.value=p.x;no.addEventListener('input',function(){p.x=no.value;});t.appendChild(no);li.appendChild(t);
    li.appendChild(el('b',null,euro(p.c*p.q)));ul.appendChild(li);});
  document.getElementById('tel-summe').textContent=euro(sum);}
document.getElementById('tel-neu').addEventListener('click',telOeffnen);
document.getElementById('tel-ab').addEventListener('click',function(){document.getElementById('tel').hidden=true;});
document.getElementById('tel-such').addEventListener('input',function(ev){var q=ev.target.value.trim().toLowerCase(),tr=document.getElementById('tel-treffer');tr.textContent='';if(!q)return;
  KARTE.filter(function(g){return g[0].toLowerCase().indexOf(q)>-1;}).slice(0,8).forEach(function(g){var b=el('button');b.type='button';b.appendChild(el('span',null,g[0]));b.appendChild(el('b',null,euro(g[1])));
    b.addEventListener('click',function(){var da=telPos.filter(function(p){return p.n===g[0]&&!p.x;})[0];if(da)da.q++;else telPos.push({n:g[0],c:g[1],q:1,x:''});
      ev.target.value='';tr.textContent='';telZeichnen();ev.target.focus();});tr.appendChild(b);});});
document.getElementById('tel-ok').addEventListener('click',function(){
  var f=document.getElementById('tel-fehler'),zeit=document.getElementById('tel-zeit').value,name=document.getElementById('tel-name').value.trim();
  if(!telPos.length){f.textContent='Bitte mindestens ein Gericht hinzufügen.';f.hidden=false;return;}
  if(!/^\d{2}:\d{2}$/.test(zeit)){f.textContent='Bitte die Abholzeit eintragen.';f.hidden=false;return;}
  var nr='T'+(10+Math.floor(Math.random()*90)),a=Date.now(),sum=telPos.reduce(function(s2,p){return s2+p.c*p.q;},0);
  var o={id:nr+'-'+a,nr:nr,l:telLaden,z:'Telefon, '+zeit+' Uhr',t:heuteISO()+'T'+zeit,m:name.slice(0,40),s:sum,r:0,rc:'',sp:'de',w:[],test:false,tel:1,a:a,fertig:0,neu:1,
    p:telPos.map(function(p){return {q:p.q,n:p.n,w:'',f:'',x:p.x.slice(0,200),c:p.c*p.q,ok:false};})};
  aufnehmen(o);speichern();document.getElementById('tel').hidden=true;zeichnen();melden('Telefonbestellung '+nr+' angelegt.');});
/* ---------- Monatsbericht: Zahlen eines Monats zum Drucken oder Weiterschicken (Besucher, falls GoatCounter-Schlüssel auf dem Gerät) ---------- */
var ZAEHLER=%%ZAEHLER%%,monatWahl=heuteISO().slice(0,7),besucher={};
function monatDaten(m){var r={n:0,s:0,tel:0,g:{},wt:{},sp:{}};Object.keys(JAHR).forEach(function(d){if(d.slice(0,7)!==m)return;var j=JAHR[d];r.n+=j.n;r.s+=j.s;r.tel+=j.tel||0;
  var w=new Date(d+'T12:00:00').getDay();r.wt[w]=(r.wt[w]||0)+j.n;Object.keys(j.g).forEach(function(k){r.g[k]=(r.g[k]||0)+j.g[k];});Object.keys(j.sp).forEach(function(k){r.sp[k]=(r.sp[k]||0)+j.sp[k];});});return r;}
var MONATE=['Januar','Februar','März','April','Mai','Juni','Juli','August','September','Oktober','November','Dezember'],WTAG=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
function monatName(m){return MONATE[+m.slice(5)-1]+' '+m.slice(0,4);}
function monatText(m){var r=monatDaten(m),top=Object.keys(r.g).sort(function(a,b){return r.g[b]-r.g[a];}).slice(0,5),wt=Object.keys(r.wt).sort(function(a,b){return r.wt[b]-r.wt[a];})[0];
  var z=['Saray Döner – Monatsbericht '+monatName(m),'','Bestellungen: '+r.n+' (davon '+r.tel+' per Telefon, '+(r.n-r.tel)+' online)','Summe (bar): '+euro(r.s)+(r.n?' · pro Bestellung '+euro(Math.round(r.s/r.n)):'')];
  if(besucher[m]!=null)z.push('Besuche auf der Website: '+besucher[m]);
  if(wt!=null)z.push('Stärkster Tag: '+WTAG[wt]);
  if(top.length){z.push('','Am meisten bestellt:');top.forEach(function(k,i){z.push((i+1)+'. '+k.replace(/^Nr\. \S+ /,'')+' – '+r.g[k]+'×');});}
  z.push('','Nur Bestellungen, die in der Küchenansicht geöffnet oder erfasst wurden.');return z.join('\n');}
function monatZeigen(){
  var ms=[];Object.keys(JAHR).forEach(function(d){var m=d.slice(0,7);if(ms.indexOf(m)<0)ms.push(m);});if(ms.indexOf(heuteISO().slice(0,7))<0)ms.push(heuteISO().slice(0,7));ms.sort().reverse();
  if(ms.indexOf(monatWahl)<0)monatWahl=ms[0];
  var w=document.getElementById('monat-wahl');w.textContent='';ms.slice(0,12).forEach(function(m){var b=el('button','chip',monatName(m));b.type='button';b.setAttribute('aria-pressed',String(m===monatWahl));
    b.addEventListener('click',function(){monatWahl=m;zeichnen();});w.appendChild(b);});
  var inh=document.getElementById('monat-inhalt');inh.textContent='';var pre=el('div','monat');pre.style.whiteSpace='pre-line';pre.textContent=monatText(monatWahl);inh.appendChild(pre);
  besucherHolen(monatWahl);}
function besucherHolen(m){var key='';try{key=localStorage.getItem('saray-chef-goatcounter')||'';}catch(e){}
  if(!key||!ZAEHLER||besucher[m]!=null||besucherHolen.laeuft)return;besucherHolen.laeuft=1;
  var start=m+'-01T00:00:00Z',e2=new Date(Date.UTC(+m.slice(0,4),+m.slice(5),1)).toISOString().replace('.000','');
  fetch('https://'+ZAEHLER+'.goatcounter.com/api/v0/stats/hits?limit=100&start='+encodeURIComponent(start)+'&end='+encodeURIComponent(e2),{headers:{'Authorization':'Bearer '+key,'Accept':'application/json'}})
    .then(function(r){return r.ok?r.json():null;}).then(function(d){besucherHolen.laeuft=0;if(!d)return;var n=0;(d.hits||[]).forEach(function(h){if(!h.event)n+=h.count;});besucher[m]=n;monatZeigen();},function(){besucherHolen.laeuft=0;});}
document.getElementById('monat-drucken').addEventListener('click',function(){document.body.classList.add('monat-druck');
  function weg(){document.body.classList.remove('monat-druck');window.removeEventListener('afterprint',weg);}window.addEventListener('afterprint',weg);window.print();});
document.getElementById('monat-teilen').addEventListener('click',function(){window.open('https://wa.me/?text='+encodeURIComponent(monatText(monatWahl)),'_blank');});
/* Viel los? Ab 8 offenen Bestellungen in der nächsten Stunde (je Laden) +15 Min. Wartezeit vorschlagen.
   Mit Chef-App-Zugang auf diesem Gerät wird direkt gespeichert (GitHub), sonst führt der Knopf in die Chef-App. */
var REPO=%%REPO%%,SCHWELLE=8,warteWeg={},warteGesetzt={};
function chefToken(){try{return localStorage.getItem('saray-chef-token')||'';}catch(e){return '';}}
function warteVorschlag(){
  var box=document.getElementById('warte-vorschlag'),h=heuteISO();box.textContent='';
  var l=Object.keys(LAEDEN).filter(function(id){return (!filter||filter===id)&&!warteWeg[id+h]&&!warteGesetzt[id+h]&&
    liste.filter(function(x){return !x.fertig&&x.l===id&&rest(x)<=60;}).length>=SCHWELLE;})[0];
  box.hidden=!l;if(!l)return;
  var n=liste.filter(function(x){return !x.fertig&&x.l===l&&rest(x)<=60;}).length;
  box.appendChild(el('span',null,'Viel los in '+LAEDEN[l]+': '+n+' Bestellungen in der nächsten Stunde. +15 Min. Wartezeit für Online-Bestellungen?'));
  var ja=el('button',null,'+15 Min.'),nein=el('button','zweit','Nein');ja.type=nein.type='button';ja.id='warte-ja';
  nein.addEventListener('click',function(){warteWeg[l+h]=1;warteVorschlag();});
  ja.addEventListener('click',function(){
    if(!chefToken()){location.href='../chef/';return;}
    ja.disabled=true;ja.textContent='Speichert …';
    warteSetzen(l,15).then(function(min){warteGesetzt[l+h]=1;warteVorschlag();melden('Wartezeit '+LAEDEN[l]+': +'+min+' Min. – in 2–3 Minuten auf der Seite.');},
      function(e){ja.disabled=false;ja.textContent='+15 Min.';melden('Speichern hat nicht geklappt ('+e.message+'). Bitte in der Chef-App einstellen.');});});
  box.appendChild(ja);box.appendChild(nein);
}
function warteSetzen(laden,plus){
  var api='https://api.github.com/repos/'+REPO+'/contents/daten/anpassungen.json',kopf={'Accept':'application/vnd.github+json','Authorization':'Bearer '+chefToken()};
  return fetch(api+'?ref=main',{headers:kopf,cache:'no-store'}).then(function(r){if(!r.ok&&r.status!==404)throw new Error(String(r.status));return r.status===404?{}:r.json();}).then(function(d){
    var anp=d.content?JSON.parse(decodeURIComponent(escape(atob(d.content.replace(/\s/g,'')))))||{}:{},h=heuteISO(),w=(anp.wartezeit=anp.wartezeit||{}),alt=w[laden]&&w[laden].datum===h?w[laden].min:0,min=Math.min(120,alt+plus);
    w[laden]={datum:h,min:min};
    return fetch(api,{method:'PUT',headers:kopf,body:JSON.stringify({message:'Küche: Wartezeit '+LAEDEN[laden]+' +'+min+' Min.',branch:'main',
      content:btoa(unescape(encodeURIComponent(JSON.stringify(anp,null,2)+'\n'))),sha:d.sha})}).then(function(r){if(!r.ok)throw new Error(String(r.status));return min;});});
}
/* Abholzeit-Slots: Sind für eine Viertelstunde so viele Bestellungen da wie in der Chef-App eingestellt (Standard 5),
   sperrt die Küche diese Zeit auf der Seite (mit Chef-App-Zugang auf diesem Gerät, sonst nur Hinweis). Die Seite schlägt dann die nächste freie Zeit vor. */
var SLOTS=%%SLOTS%%,vollBekannt={},vollLaeuft=0,vollFehler=0;
try{vollBekannt=JSON.parse(localStorage.getItem('saray-kueche-voll')||'{}')||{};}catch(e){}
Object.keys(SLOTS.voll||{}).forEach(function(l){Object.keys(SLOTS.voll[l]).forEach(function(d){SLOTS.voll[l][d].forEach(function(z){vollBekannt[l+'|'+d+'|'+z]=1;});});});
function slotVon(t){var m=Math.floor((+t.slice(11,13)*60+ +t.slice(14,16))/15)*15;return t.slice(0,10)+'|'+('0'+Math.floor(m/60)).slice(-2)+':'+('0'+m%60).slice(-2);}
function slotsPruefen(){
  var box=document.getElementById('slot-info'),h=heuteISO(),zahl={},neu=[];
  liste.forEach(function(x){if(x.test||!x.t||!x.l||x.t.slice(0,10)<h)return;var k=x.l+'|'+slotVon(x.t);zahl[k]=(zahl[k]||0)+1;});
  Object.keys(zahl).forEach(function(k){var l=k.split('|')[0],mx=(SLOTS.max||{})[l];if(mx&&zahl[k]>=mx&&!vollBekannt[k])neu.push(k);});
  var gesperrt=Object.keys(vollBekannt).filter(function(k){return k.split('|')[1]>=h&&(!filter||k.split('|')[0]===filter);}).sort();
  box.textContent='';
  if(neu.length&&!chefToken()){box.textContent='⚠ Ausgebucht: '+neu.map(function(k){var p=k.split('|');return LAEDEN[p[0]]+' '+(p[1]===h?'':p[1].slice(8,10)+'.'+p[1].slice(5,7)+'. ')+p[2];}).join(', ')+
    ' – ohne Chef-App-Zugang auf diesem Gerät kann die Küche die Zeit nicht online sperren.';box.hidden=false;return;}
  if(gesperrt.length){box.textContent='🔒 Online ausgebucht: '+gesperrt.map(function(k){var p=k.split('|');return LAEDEN[p[0]]+' '+(p[1]===h?'':p[1].slice(8,10)+'.'+p[1].slice(5,7)+'. ')+p[2];}).join(', ');box.hidden=false;}
  else box.hidden=true;
  if(!neu.length||vollLaeuft||Date.now()<vollFehler)return;
  vollLaeuft=1;
  anpAendern(function(anp){var v=anp.voll=anp.voll||{};Object.keys(v).forEach(function(l){Object.keys(v[l]||{}).forEach(function(d){if(d<h)delete v[l][d];});});
    neu.forEach(function(k){var p=k.split('|'),t=(v[p[0]]=v[p[0]]||{}),z=(t[p[1]]=t[p[1]]||[]);if(z.indexOf(p[2])<0)z.push(p[2]);z.sort();});},
    'Küche: ausgebucht '+neu.map(function(k){return k.replace(/\|/g,' ');}).join(', ')).then(function(){
    neu.forEach(function(k){vollBekannt[k]=1;});try{localStorage.setItem('saray-kueche-voll',JSON.stringify(vollBekannt));}catch(e){}
    vollLaeuft=0;melden('Ausgebucht gemeldet – in 2–3 Minuten bietet die Seite die nächste freie Zeit an.');slotsPruefen();},
    function(){vollLaeuft=0;vollFehler=Date.now()+60000;});
}
/* daten/anpassungen.json lesen, ändern, zurückschreiben (Chef-App-Zugang auf diesem Gerät) */
function anpAendern(aendern,nachricht){
  var api='https://api.github.com/repos/'+REPO+'/contents/daten/anpassungen.json',kopf={'Accept':'application/vnd.github+json','Authorization':'Bearer '+chefToken()};
  return fetch(api+'?ref=main',{headers:kopf,cache:'no-store'}).then(function(r){if(!r.ok&&r.status!==404)throw new Error(String(r.status));return r.status===404?{}:r.json();}).then(function(d){
    var anp=d.content?JSON.parse(decodeURIComponent(escape(atob(d.content.replace(/\s/g,'')))))||{}:{};aendern(anp);
    var body={message:nachricht,branch:'main',content:btoa(unescape(encodeURIComponent(JSON.stringify(anp,null,2)+'\n')))};if(d.sha)body.sha=d.sha;
    return fetch(api,{method:'PUT',headers:kopf,body:JSON.stringify(body)}).then(function(r){if(!r.ok)throw new Error(String(r.status));});});
}
var bedarfWahl='60';
function bedarf(offen){
  var box=document.getElementById('bedarf');box.hidden=!offen.length;if(!offen.length)return;
  var w=document.getElementById('bedarf-wahl');w.textContent='';
  [['60','Nächste Stunde'],['alle','Alle offenen']].forEach(function(o){var b=el('button','chip',o[1]);b.type='button';b.setAttribute('aria-pressed',String(bedarfWahl===o[0]));
    b.addEventListener('click',function(){bedarfWahl=o[0];zeichnen();});w.appendChild(b);});
  var zahl={};offen.filter(function(x){return bedarfWahl==='alle'||rest(x)<=60;}).forEach(function(x){x.p.forEach(function(p){if(!p.ok)zahl[p.n]=(zahl[p.n]||0)+p.q;});});
  var t=document.getElementById('bedarf-liste');t.textContent='';
  var ks=Object.keys(zahl).sort(function(a,b){return zahl[b]-zahl[a]||a.localeCompare(b);});
  ks.forEach(function(n){var tr=el('tr');tr.appendChild(el('td','z',zahl[n]+'×'));tr.appendChild(el('td',null,n));t.appendChild(tr);});
  if(!ks.length){var tr=el('tr');tr.appendChild(el('td',null,'Nichts mehr offen.'));t.appendChild(tr);}
  document.getElementById('bedarf-titel').textContent='Was brauchen wir? ('+ks.reduce(function(s,n){return s+zahl[n];},0)+' Gerichte)';}
var jahrWahl=String(new Date().getFullYear());
function balken(box,paare,format){var max=Math.max.apply(null,paare.map(function(p){return p[1];}).concat([1])),g=el('div','balken');
  paare.forEach(function(p){g.appendChild(el('span',null,p[0]));var i=el('i');i.style.width=(100*p[1]/max)+'%';var s2=el('span');s2.appendChild(i);g.appendChild(s2);g.appendChild(el('span',null,format?format(p[1]):String(p[1])));});box.appendChild(g);}
function jahrZeigen(){
  var jahre=[];Object.keys(JAHR).forEach(function(d){var y=d.slice(0,4);if(jahre.indexOf(y)<0)jahre.push(y);});
  if(jahre.indexOf(jahrWahl)<0)jahre.push(jahrWahl);jahre.sort().reverse();
  var w=document.getElementById('jahr-wahl');w.textContent='';jahre.forEach(function(y){var b=el('button','chip',y);b.type='button';b.setAttribute('aria-pressed',String(y===jahrWahl));
    b.addEventListener('click',function(){jahrWahl=y;zeichnen();});w.appendChild(b);});
  var inh=document.getElementById('jahr-inhalt');inh.textContent='';
  var tage=Object.keys(JAHR).filter(function(d){return d.slice(0,4)===jahrWahl;}),n=0,sum=0,g={},h={},sp={},l={},mon={},wt={};
  tage.forEach(function(d){var j=JAHR[d];n+=j.n;sum+=j.s;mon[d.slice(5,7)]=(mon[d.slice(5,7)]||0)+j.n;var w2=new Date(d+'T12:00:00').getDay();wt[w2]=(wt[w2]||0)+j.n;
    [[g,j.g],[h,j.h],[sp,j.sp],[l,j.l]].forEach(function(q){Object.keys(q[1]).forEach(function(k){q[0][k]=(q[0][k]||0)+q[1][k];});});});
  inh.appendChild(el('h3',null,'Saray Döner '+jahrWahl));
  if(!n){inh.appendChild(el('p','klein','Für '+jahrWahl+' noch keine Bestellungen auf diesem Gerät.'));return;}
  var gerichte=Object.keys(g).reduce(function(s,k){return s+g[k];},0),zahlen=el('div','zahlen');
  [[n,'Bestellungen'],[euro(sum),'Summe (bar)'],[gerichte,'Gerichte'],[euro(Math.round(sum/n)),'pro Bestellung']].forEach(function(z){var d=el('div');d.appendChild(el('b',null,String(z[0])));d.appendChild(el('span',null,z[1]));zahlen.appendChild(d);});
  inh.appendChild(zahlen);
  var MON=['Jan','Feb','Mär','Apr','Mai','Jun','Jul','Aug','Sep','Okt','Nov','Dez'],WT=['So','Mo','Di','Mi','Do','Fr','Sa'];
  inh.appendChild(el('h4',null,'Bestellungen je Monat'));balken(inh,MON.map(function(m2,i){return [m2,mon[('0'+(i+1)).slice(-2)]||0];}));
  inh.appendChild(el('h4',null,'Am meisten bestellt'));balken(inh,Object.keys(g).sort(function(a,b){return g[b]-g[a];}).slice(0,10).map(function(k){return [k.replace(/^Nr\. \S+ /,''),g[k]];}),function(v){return v+'×';});
  inh.querySelectorAll('.balken')[1].style.gridTemplateColumns='minmax(8em,14em) 1fr 4em';
  inh.appendChild(el('h4',null,'Wochentage'));balken(inh,[1,2,3,4,5,6,0].map(function(d){return [WT[d],wt[d]||0];}));
  var hs=Object.keys(h).sort();if(hs.length){inh.appendChild(el('h4',null,'Abholzeiten'));balken(inh,hs.map(function(k){return [(+k)+' Uhr',h[k]];}));}
  var SPN={de:'Deutsch',en:'Englisch',tr:'Türkisch',cs:'Tschechisch',ru:'Russisch',ar:'Arabisch'};
  inh.appendChild(el('h4',null,'Sprache der Gäste'));balken(inh,Object.keys(sp).sort(function(a,b){return sp[b]-sp[a];}).map(function(k){return [SPN[k]||k,sp[k]];}));
  if(!filter&&Object.keys(l).length>1){inh.appendChild(el('h4',null,'Läden'));balken(inh,Object.keys(l).map(function(k){return [LAEDEN[k]||k,l[k]];}));}
}
document.getElementById('jahr-drucken').addEventListener('click',function(){document.body.classList.add('jahr-druck');
  function weg(){document.body.classList.remove('jahr-druck');window.removeEventListener('afterprint',weg);}window.addEventListener('afterprint',weg);window.print();});
var abTag='';
function tagVon(x){return x.t?x.t.slice(0,10):new Date(x.a).toISOString().slice(0,10);}
function abschluss(sicht){
  var tage=[],box=document.getElementById('abschluss-tag'),inh=document.getElementById('abschluss-inhalt');
  sicht.forEach(function(x){var d=tagVon(x);if(tage.indexOf(d)<0)tage.push(d);});tage.sort().reverse();
  if(tage.indexOf(heuteISO())<0)tage.unshift(heuteISO());
  if(tage.indexOf(abTag)<0)abTag=tage[0];
  box.textContent='';tage.slice(0,7).forEach(function(d){var b=el('button','chip',d===heuteISO()?'Heute':d.slice(8)+'.'+d.slice(5,7)+'.');b.type='button';
    b.setAttribute('aria-pressed',String(d===abTag));b.addEventListener('click',function(){abTag=d;zeichnen();});box.appendChild(b);});
  var tag=sicht.filter(function(x){return tagVon(x)===abTag;}),echt=tag.filter(function(x){return !x.test;}),test=tag.length-echt.length;
  inh.textContent='';
  var umsatz=echt.reduce(function(s,x){return s+x.s;},0),stueck=0,gerichte={},stunden={};
  echt.forEach(function(x){x.p.forEach(function(p){stueck+=p.q;var n=p.n.replace(/\s*\(.*\)$/,'');gerichte[n]=(gerichte[n]||0)+p.q;});
    if(x.t){var h=x.t.slice(11,13);stunden[h]=(stunden[h]||0)+1;}});
  var zahlen=el('div','zahlen');
  [[echt.length,'Bestellungen'],[euro(umsatz),'Summe (bar)'],[stueck,'Gerichte'],[echt.length?euro(Math.round(umsatz/echt.length)):'–','pro Bestellung']].forEach(function(z){
    var d=el('div');d.appendChild(el('b',null,String(z[0])));d.appendChild(el('span',null,z[1]));zahlen.appendChild(d);});
  inh.appendChild(zahlen);
  if(test)inh.appendChild(el('p','klein','Dazu '+test+' Test-Bestellung'+(test===1?'':'en')+' (nicht mitgezählt).'));
  var top=Object.keys(gerichte).sort(function(a,b){return gerichte[b]-gerichte[a]||a.localeCompare(b);}).slice(0,10);
  if(top.length){var tb=el('table'),hd=el('tr');hd.appendChild(el('th',null,'Am meisten bestellt'));hd.appendChild(el('th',null,''));tb.appendChild(hd);
    top.forEach(function(n){var tr=el('tr');tr.appendChild(el('td',null,n));tr.appendChild(el('td','z',gerichte[n]+'×'));tb.appendChild(tr);});inh.appendChild(tb);}
  var hs=Object.keys(stunden).sort(function(a,b){return stunden[b]-stunden[a];});
  if(hs.length)inh.appendChild(el('p',null,'Meiste Abholungen: '+(+hs[0])+'–'+(+hs[0]+1)+' Uhr ('+stunden[hs[0]]+')'));
  if(!echt.length&&!test)inh.appendChild(el('p','klein','An diesem Tag noch keine Bestellungen.'));
}
window.addEventListener('storage',function(ev){if(ev.key===K){try{liste=JSON.parse(ev.newValue||'[]');}catch(e){}zeichnen();}});
window.addEventListener('hashchange',function(){var m2=/[#&]b=([A-Za-z0-9_-]+)/.exec(location.hash);if(!m2)return;var o2=lesen(m2[1]);
  aufnehmen(o2);speichern();history.replaceState(null,'',location.pathname+location.search);zeichnen();});
setInterval(zeichnen,30000);
setTimeout(function(){var neu=liste.some(function(x){return x.neu;});liste.forEach(function(x){x.neu=0;});if(neu)speichern();},4000);
filterZeigen();zeichnen();if(syncN)melden(syncN+' Bestellung'+(syncN===1?'':'en')+' vom anderen Gerät übernommen.');
document.getElementById('sync-knopf').addEventListener('click',function(){
  var o=liste.map(function(x){var y=JSON.parse(JSON.stringify(x));delete y.neu;delete y.w;return y;});
  if(!o.length){melden('Keine Bestellungen auf diesem Gerät.');return;}
  var link=location.origin+location.pathname+'#sync='+b64url(JSON.stringify({o:o}));
  var t='Bestellungen der letzten 7 Tage aus der Küchenansicht ('+o.length+'). Auf dem anderen Gerät öffnen:\n'+link;
  window._syncText=t;
  if(navigator.share&&matchMedia('(pointer:coarse)').matches)navigator.share({text:t}).catch(function(){});else window.open('https://wa.me/?text='+encodeURIComponent(t),'_blank');});
window.addEventListener('hashchange',function(){var n=syncLesen();if(n){zeichnen();melden(n+' Bestellung'+(n===1?'':'en')+' vom anderen Gerät übernommen.');}});
/* Tagesplan: alle Bestellungen für heute nach Uhrzeit, zum Aufhängen in der Küche */
document.getElementById('plan-knopf').addEventListener('click',function(){
  var h=heuteISO(),pl=document.getElementById('plan'),heute=liste.filter(function(x){return tagVon(x)===h&&(!filter||x.l===filter);}).sort(function(a,b){return zeitpunkt(a)-zeitpunkt(b);});
  pl.textContent='';pl.appendChild(el('h1',null,'Tagesplan '+h.slice(8)+'.'+h.slice(5,7)+'.'+h.slice(0,4)+(filter?' · '+LAEDEN[filter]:'')+' · '+heute.length+' Bestellungen'));
  var tb=el('table'),kopf=el('tr');['Zeit','Nr.','Name','Laden','Gerichte','Summe'].forEach(function(t){kopf.appendChild(el('th',null,t));});tb.appendChild(kopf);
  heute.forEach(function(x){var tr=el('tr');tr.appendChild(el('td',null,x.t?x.t.slice(11):'sofort'));tr.appendChild(el('td',null,x.nr+(x.tel?' 📞':'')+(x.fertig?' ✓':'')));
    tr.appendChild(el('td',null,x.m||''));tr.appendChild(el('td',null,LAEDEN[x.l]||''));
    var g=el('td');x.p.forEach(function(p){var d=el('div',null,p.q+'× '+p.n+(p.w?' – '+p.w:''));if(p.x){d.appendChild(el('span',ALLERGIE.test(p.x)?'al':'',' · '+(ALLERGIE.test(p.x)?'⚠ ':'')+p.x));}g.appendChild(d);});tr.appendChild(g);
    tr.appendChild(el('td',null,euro(x.s)));tb.appendChild(tr);});
  pl.appendChild(tb);if(!heute.length)pl.appendChild(el('p',null,'Für heute noch keine Bestellungen.'));
  pl.hidden=false;document.body.classList.add('plan-druck');function weg(){document.body.classList.remove('plan-druck');pl.hidden=true;window.removeEventListener('afterprint',weg);}
  window.addEventListener('afterprint',weg);window.print();});
})();
</script>
</body>
</html>
"""


def schreiben(aus, daten, laeden, seite_url, version, repo="", karte=(), zaehler="", ntfy="", slots=None):
    """daten: dict für den Bildschirm (siehe build.py); laeden: {id: name}; seite_url: Adresse für den QR-Code."""
    anzeige = seite_url.rstrip("/").replace("https://", "")
    (aus / "tv").mkdir(exist_ok=True)
    (aus / "tv" / "index.html").write_text(
        TV.replace("%%DATEN%%", json.dumps(daten, ensure_ascii=False, separators=(",", ":")))
          .replace("%%QR%%", qr_svg(seite_url, ecl="M", farbe="#3A1531", rand=1))
          .replace("%%ADRESSE%%", anzeige), encoding="utf-8")
    (aus / "kueche").mkdir(exist_ok=True)
    (aus / "kueche" / "index.html").write_text(KUECHE.replace("%%LAEDEN%%", json.dumps(laeden, ensure_ascii=False)).replace("%%REPO%%", json.dumps(repo)).replace("%%KARTE%%", json.dumps(list(karte), ensure_ascii=False)).replace("%%ZAEHLER%%", json.dumps(zaehler)).replace("%%ALLERGIE%%", json.dumps(ALLERGIE_RE)).replace("%%NTFY%%", json.dumps(ntfy)).replace("%%SLOTS%%", json.dumps(slots or {"max": {}, "voll": {}})), encoding="utf-8")
    (aus / "version.json").write_text(json.dumps({"v": version}) + "\n")
