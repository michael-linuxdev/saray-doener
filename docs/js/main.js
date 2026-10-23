(function(){
  var ZEITEN={"freital": {"1": [600, 1320], "2": [600, 1320], "3": [600, 1320], "4": [600, 1320], "5": [600, 1320], "6": [660, 1320], "0": [660, 1320]}, "altenberg": {"1": [600, 1260], "2": [600, 1260], "3": [600, 1260], "4": [600, 1260], "5": [600, 1260], "6": [600, 1260], "0": [660, 1260]}},SONDER={"freital": {}, "altenberg": {}},WARTE={},AKTIONEN=[];
  var TAGE=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
  var TAGE_E=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  /* Sprache: gespeicherte Wahl, sonst Browsersprache (Suchmaschinen bekommen immer Deutsch) */
  /* Weitere Sprachen: Wörterbuch Englisch -> Sprache (docs/lang/<code>.json); fehlt ein Text, bleibt Englisch.
     Zahlen im Text werden als {n} nachgeschlagen, damit „3 dishes found“ und „{n} dishes found“ zusammenpassen. */
  var SPRACHEN=[["de", "Deutsch"], ["en", "English"], ["cs", "Čeština"], ["tr", "Türkçe"], ["ru", "Русский"], ["ar", "العربية"]],DICT={},LOC={de:'de-DE',en:'en-GB',cs:'cs-CZ',ru:'ru-RU',tr:'tr-TR',ar:'ar-u-nu-latn'};
  var SPK='saray-sprache',SP='de';
  try{SP=localStorage.getItem(SPK)||'';}catch(e){SP='';}
  if(!SPRACHEN.some(function(x){return x[0]===SP;})){
    var langs=(navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'de']);
    SP='en';
    if(/bot|crawl|spider|lighthouse/i.test(navigator.userAgent))SP='de';
    else for(var li0=0;li0<langs.length;li0++){var k0=String(langs[li0]).slice(0,2).toLowerCase();if(SPRACHEN.some(function(x){return x[0]===k0;})){SP=k0;break;}}
  }
  function T(en){
    if(SP==='en'||SP==='de'||en==null)return en;var d=DICT[SP]||{},r=en;
    if(d[en]!=null)r=d[en];
    else{var z=[],k=String(en).replace(/\d+(?:[.,:]\d+)*/g,function(m){z.push(m);return '{n}';});
      if(z.length&&d[k]!=null){var i=0;r=d[k].replace(/\{n\}/g,function(){return z[i++];});}}
    return LTR_ZAHLEN(r);
  }
  /* Rechts-nach-links (Arabisch): Telefonnummern, Uhrzeiten und Preise als Block links-nach-rechts halten */
  function LTR_ZAHLEN(r){
    if(document.documentElement.dir!=='rtl'||typeof r!=='string')return r;
    return r.split(/(<[^>]*>)/).map(function(t){return t.charAt(0)==='<'?t:t.replace(/\+?\d[\d.,:\u2013\- ]*\d(?: ?€)?|\d(?: ?€)?/g,function(m){return '\u2066'+m+'\u2069';});}).join('');
  }
  function L(de,en){return SP==='de'?de:T(en);}
  function fuell(tpl,w){return tpl.replace(/\{(\w+)\}/g,function(_,k){return w[k]!=null?w[k]:'';});}
  /* Linkshänder-Modus: auf diesem Gerät gemerkt */
  var HK='saray-hand',linkshand=false;
  try{linkshand=localStorage.getItem(HK)==='links';}catch(e){}
  function handZeigen(){document.documentElement.classList.toggle('links',linkshand);
    document.querySelectorAll('[data-hand]').forEach(function(b){b.textContent=linkshand?L('✋ Rechtshänder? Knöpfe nach rechts','✋ Right-handed? Buttons to the right'):L('✋ Linkshänder? Knöpfe nach links','✋ Left-handed? Buttons to the left');
      b.setAttribute('aria-pressed',String(linkshand));});}
  document.addEventListener('click',function(ev){if(!ev.target.closest('[data-hand]'))return;linkshand=!linkshand;
    try{localStorage.setItem(HK,linkshand?'links':'rechts');}catch(e){}handZeigen();});
  handZeigen();
  function handSetzen(v){linkshand=v;try{localStorage.setItem(HK,v?'links':'rechts');}catch(e){}handZeigen();}
  /* Kleiner Hinweis-Kasten unten (z. B. „Hat’s geschmeckt?“) */
  var handTimer=null;
  function handTippZeigen(text,knoepfe,dauer){
    var box=document.getElementById('hand-tipp');box.textContent='';
    var pa=document.createElement('p');pa.innerHTML=text;box.appendChild(pa);
    var reihe=document.createElement('div');
    knoepfe.forEach(function(k,i){var b=document.createElement('button');b.type='button';b.textContent=k[0];if(i)b.className='zweit';
      b.addEventListener('click',k[1]);reihe.appendChild(b);});
    box.appendChild(reihe);box.hidden=false;
    clearTimeout(handTimer);handTimer=setTimeout(handTippZu,dauer||12000);
  }
  function handTippZu(){clearTimeout(handTimer);document.getElementById('hand-tipp').hidden=true;}
  var KURZ={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6};
  var weniger=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  function jetzt(){
    var o={};
    new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})
      .formatToParts(new Date()).forEach(function(p){o[p.type]=p.value;});
    return {tag:KURZ[o.weekday],min:(+o.hour)*60+(+o.minute)};
  }
  /* ISO-Datum (deutsche Zeit) in off Tagen; Öffnungszeit dieses Tages – besondere Tage gehen vor */
  function isoTag(off){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+(off||0)*864e5));}
  function tagZeit(ort,off){var s=SONDER[ort]||{},d=isoTag(off);if(d in s)return s[d];return ZEITEN[ort][(jetzt().tag+off)%7]||null;}
  /* Sonderaktion für Gericht k (Größe i) an Datum iso und Laden (null = noch nicht gewählt) */
  function aktion(k,i,iso,laden,min){
    var wt=new Date(iso+'T12:00:00Z').getUTCDay();
    for(var j=0;j<AKTIONEN.length;j++){var a=AKTIONEN[j],p=a.p[k];
      if(!p||iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0)||(a.laden&&a.laden!==laden))continue;
      if(a.za!=null&&(min==null||min<a.za||min>=a.zb))continue;
      return {c:p[Math.min(i||0,p.length-1)],a:a};}
    return null;
  }
  function euroK(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  /* Speisekarte: heute laufende Aktionen markieren (alter Preis durchgestrichen, Aktionspreis als Marke) */
  function aktionenZeigen(){
    document.querySelectorAll('[data-neu-bis]').forEach(function(m){m.hidden=isoTag(0)>m.dataset.neuBis;});
    document.querySelectorAll('li.paket').forEach(function(p){var h=isoTag(0);p.hidden=(p.dataset.von&&h<p.dataset.von)||(p.dataset.bis&&h>p.dataset.bis);});
    var pk=document.querySelector('.pakete');if(pk)pk.hidden=!pk.querySelector('li.paket:not([hidden])');
    var iso=isoTag(0),wt=new Date(iso+'T12:00:00Z').getUTCDay(),jm=jetzt().min;
    document.querySelectorAll('[data-mittag]').forEach(function(sec){var a=AKTIONEN[+sec.dataset.mittag];
      sec.hidden=!a||iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0)||(a.zb!=null&&jm>=a.zb);});
    document.querySelectorAll('.marke-aktion').forEach(function(m){m.remove();});
    document.querySelectorAll('.preis-alt').forEach(function(m){m.classList.remove('preis-alt');});
    AKTIONEN.forEach(function(a){
      if(iso<a.von||iso>a.bis||(a.tage&&a.tage.indexOf(wt)<0))return;
      Object.keys(a.p).forEach(function(k){
        var st=document.querySelector('.sticker');
        if(k==='1'&&st&&!a.laden&&a.za==null){var c=a.p[k][0],sp=st.querySelector('.sticker-preis');st.querySelector('small').textContent=L('Aktion','Offer');
          if(sp)sp.innerHTML=Math.floor(c/100)+'<span class="ct">'+('0'+c%100).slice(-2)+'</span>';st.classList.add('sticker-aktion');}
        document.querySelectorAll('li[data-k="'+(window.CSS&&CSS.escape?CSS.escape(k):k)+'"]').forEach(function(li){
          var ziel=li.querySelector('.name, .tipp-name');if(!ziel)return;
          var m=document.createElement('span');m.className='marke-beliebt marke-aktion';
          var ort=a.laden?(a.laden==='freital'?' Freital':' Altenberg'):'';
          var uz=a.za!=null?' '+uhr(a.za).replace(' Uhr','')+'–'+uhr(a.zb):'';
          m.textContent=(a.m?L('Mittag ','Lunch '):L('Aktion ','Offer '))+a.p[k].map(euroK).join(' / ')+uz+(ort?(SP==='de'?' (nur'+ort+')':' '+fuell(T('({ort} only)'),{ort:ort.trim()})):'');
          ziel.appendChild(document.createTextNode(' '));ziel.appendChild(m);
          li.querySelectorAll('.preis, .tipp-preis').forEach(function(p){p.classList.add('preis-alt');});
        });
      });
    });
  }
  /* Bestell-Pause aus der Chef-App: bis zur Uhrzeit keine Online-Bestellungen für heute (Vorbestellen für andere Tage geht) */
  var PAUSE={};
  function pause(ort){var p=PAUSE[ort],n=jetzt();if(!p||p.bis.slice(0,10)!==isoTag(0))return null;var m=minAus(p.bis.slice(11));return n.min<m?m:null;}
  function warte(ort){var w=WARTE[ort];return w&&w.datum===isoTag(0)?w.min:0;}
  function uhr(m){var h=Math.floor(m/60),r=m%60;if(SP!=='de')return h+':'+(r<10?'0':'')+r;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
  function lage(ort){
    var n=jetzt(),h=tagZeit(ort,0),w=warte(ort);
    var pz=pause(ort);
    if(h&&n.min>=h[0]&&n.min<h[1]&&pz)return{offen:true,bald:true,text:SP==='de'?'Online-Bestellungen pausiert bis '+uhr(pz)+' – anrufen geht':fuell(T('Online orders paused until {zeit} – please call'),{zeit:uhr(pz)})};
    if(h&&n.min>=h[0]&&n.min<h[1]-30)return{offen:true,text:(SP==='de'?'Jetzt geöffnet, bis '+uhr(h[1]):fuell(T('Open now, until {zeit}'),{zeit:uhr(h[1])}))+(w?L(' · Wartezeit ca. '+w+' Min.',' · waiting time approx. '+w+' min'):'')};
    if(h&&n.min>=h[0]&&n.min<h[1])return{offen:true,bald:true,text:SP==='de'?'Bald Feierabend – geöffnet bis '+uhr(h[1]):fuell(T('Closing soon – open until {zeit}'),{zeit:uhr(h[1])})};
    if(h&&n.min<h[0])return{offen:false,text:SP==='de'?'Geschlossen, öffnet heute um '+uhr(h[0]):fuell(T('Closed, opens today at {zeit}'),{zeit:uhr(h[0])})};
    for(var i=1;i<=14;i++){var t=(n.tag+i)%7,zi=tagZeit(ort,i);if(zi)return{offen:false,text:SP!=='de'?(SP==='en'?'Closed, opens '+(i===1?'tomorrow':i<7?'on '+TAGE_E[t]:'on '+TAGE_E[t]+' '+isoTag(i).slice(8)+'/'+isoTag(i).slice(5,7))+' at '+uhr(zi[0])
        :fuell(T(i===1?'Closed, opens tomorrow at {zeit}':'Closed, opens on {tag} at {zeit}'),{zeit:uhr(zi[0]),tag:new Intl.DateTimeFormat(LOC[SP],Object.assign({timeZone:'Europe/Berlin',weekday:'long'},i<7?{}:{day:'numeric',month:'numeric'})).format(new Date(Date.now()+i*864e5))})):'Geschlossen, öffnet '+(i===1?'morgen':i<7?'am '+TAGE[t]:'am '+TAGE[t]+', '+isoTag(i).slice(8)+'.'+isoTag(i).slice(5,7)+'.')+' um '+uhr(zi[0])};}
    return{offen:false,text:''};
  }
  function aktualisieren(){
    document.querySelectorAll('[data-status]').forEach(function(el){
      var s=lage(el.getAttribute('data-status'));el.setAttribute('data-offen',s.offen?(s.bald?'bald':'ja'):'nein');
      el.querySelector('.status-text').textContent=s.text;
    });
    var tag=jetzt().tag,hi=isoTag(0);
    document.querySelectorAll('.sonder li[data-datum]').forEach(function(li){li.hidden=li.dataset.datum<hi;li.classList.toggle('heute',li.dataset.datum===hi);});
    document.querySelectorAll('.sonder').forEach(function(b){b.hidden=!b.querySelector('li:not([hidden])');});
    document.querySelectorAll('tr[data-tage]').forEach(function(tr){
      tr.classList.toggle('heute',tr.getAttribute('data-tage').split(',').indexOf(String(tag))>-1);
    });
  }
  try{aktualisieren();setInterval(aktualisieren,60000);}catch(e){}
  try{aktionenZeigen();}catch(e){}
  /* Zählen ohne Cookies (GoatCounter-Pixel, nur wenn ZAEHLER gesetzt) */
  var GC="saraymicana";
  function zaehlen(pfad,ereignis){
    if(!GC||navigator.doNotTrack==='1'||/^(localhost|127\.)/.test(location.hostname))return;
    try{(new Image()).src='https://'+GC+'.goatcounter.com/count?p='+encodeURIComponent(pfad)+(ereignis?'&e=true&t='+encodeURIComponent(pfad):'&t='+encodeURIComponent(document.title))+'&rnd='+Math.random().toString(36).slice(2);}catch(e){}
  }
  zaehlen(location.pathname);
  document.addEventListener('click',function(ev){
    var a=ev.target.closest('a,button');if(!a)return;var laden=a.dataset.anruf||'',href=a.getAttribute('href')||'';
    if(!laden&&/^tel:/.test(href))try{Object.keys(TEL).forEach(function(l){if('tel:'+TEL[l][1]===href)laden=l;});}catch(e){}
    if(a.id==='zettel-whatsapp')zaehlen('whatsapp-'+((typeof abh==='object'&&abh&&abh.laden)||'bestellung'));
    else if(/^tel:/.test(href))zaehlen('anrufen'+(laden?'-'+laden:''));
    else if(a.id==='zettel-kopieren')zaehlen('bestellung-teilen');
    else if(a.id==='sammel-einladen')zaehlen('gemeinsam-bestellen');
  },true);
  /* Offline: Speisekarte bleibt verfügbar (Service Worker, nur auf der echten Seite) */
  if(true&&'serviceWorker' in navigator&&location.protocol==='https:')window.addEventListener('load',function(){navigator.serviceWorker.register('sw.js').catch(function(){});});
  /* „Hat's geschmeckt?“ – einmal, beim nächsten Besuch nach einer WhatsApp-Bestellung (2 Std. bis 14 Tage später) */
  var GOOGLE={"freital": "ChIJi62UlB_FCUcRyZITkeCfe8Q", "altenberg": "ChIJ7XWZiUmTCUcRxe2o2WmxkxQ"};
  setTimeout(function(){
    var bw=null;try{bw=JSON.parse(localStorage.getItem('saray-bewertung')||'null');}catch(e){return;}
    if(!bw||bw.fertig||!GOOGLE[bw.l])return;var alt=Date.now()-bw.t;if(alt<2*36e5||alt>14*864e5)return;
    if(!document.getElementById('hand-tipp').hidden)return;
    try{bw.fertig=1;localStorage.setItem('saray-bewertung',JSON.stringify(bw));}catch(e){return;}
    var ort=bw.l==='freital'?'Freital':'Altenberg';
    /* Erst fragen: War alles gut? Ja -> Google-Bewertung. Nein -> Nachricht direkt an den Laden statt öffentlicher Kritik */
    function google(){handTippZeigen('<b>'+L('Danke!','Thank you!')+'</b><br>'+(SP==='de'?'Über eine Google-Bewertung für Saray Döner '+ort+' freuen wir uns sehr.':fuell(T('We would love a Google review for Saray Döner {ort}.'),{ort:ort})),
      [[L('⭐ Bewerten','⭐ Review'),function(){zaehlen('bewertung-'+bw.l);window.open('https://search.google.com/local/writereview?placeid='+GOOGLE[bw.l],'_blank','noopener');handTippZu();}],
       [L('Nein danke','No thanks'),handTippZu]],25000);}
    function laden(){zaehlen('rueckmeldung-'+bw.l);var nr=WA[bw.l],t='Rückmeldung zu meiner Bestellung'+(bw.nr?' '+bw.nr:'')+' bei Saray Döner '+ort+': ';
      handTippZeigen('<b>'+L('Das tut uns leid.','We are sorry.')+'</b><br>'+L('Sagen Sie es uns direkt – wir kümmern uns darum.','Tell us directly – we will take care of it.'),
        [[nr?L('💬 Nachricht an den Laden','💬 Message the shop'):L('📞 Laden anrufen','📞 Call the shop'),function(){
          if(nr)window.open('https://wa.me/'+nr+'?text='+encodeURIComponent(t),'_blank','noopener');else location.href='tel:'+TEL[bw.l][1];handTippZu();}],
         [L('Schließen','Close'),handTippZu]],25000);}
    handTippZeigen('<b>'+L('Hat alles gepasst?','Was everything okay?')+'</b><br>'+(SP==='de'?'Ihre Bestellung bei Saray Döner '+ort:fuell(T('Your order at Saray Döner {ort}'),{ort:ort})),
      [[L('👍 Ja, lecker','👍 Yes, delicious'),google],[L('👎 Nicht ganz','👎 Not quite'),laden]],25000);
  },1500);
  /* „Inhaltsstoffe … · Allergene …“ öffnet die Liste unten */
  document.addEventListener('click',function(ev){if(!ev.target.closest('[data-allergene]'))return;var d=document.getElementById('allergene');if(d)d.open=true;});
  if(location.hash==='#allergene'){var dA=document.getElementById('allergene');if(dA)dA.open=true;}

  /* Kategorien: Die angeklickte Kategorie wird sofort markiert und bleibt es.
     Erst wenn man selbst scrollt, wandert die Markierung mit dem Inhalt mit. */
  var nav=document.querySelector('.kategorien'),leiste=nav&&nav.querySelector('ul');
  var links={},gruppen=[].slice.call(document.querySelectorAll('.gruppe')),aktiv=null,fest=null,geplant=false;
  nav&&nav.querySelectorAll('a').forEach(function(a){links[a.getAttribute('href').slice(1)]=a;});
  function markiere(id){
    if(id===aktiv)return;aktiv=id;
    Object.keys(links).forEach(function(k){
      if(k===id)links[k].setAttribute('aria-current','true');else links[k].removeAttribute('aria-current');
    });
    var a=id&&links[id];
    if(a&&leiste&&leiste.scrollWidth>leiste.clientWidth){
      leiste.scrollTo({left:a.offsetLeft-leiste.clientWidth/2+a.offsetWidth/2,behavior:weniger?'auto':'smooth'});
    }
  }
  function imBlick(){
    var linie=Math.min(window.innerHeight*0.35,170),id=null;
    for(var i=0;i<gruppen.length;i++){
      if(gruppen[i].hidden)continue;
      if(gruppen[i].getBoundingClientRect().top<=linie)id=gruppen[i].id;else break;
    }
    return id;
  }
  /* Kategorie-Band klebt oben? Dann weiß darüber und weiße Browserleiste */
  /* Klebt das Band? Dann liegt es tiefer als die unsichtbare Marke direkt davor.
     Solange es klebt, liegt eine feste weiße Fläche dahinter (.deckel-oben): Safari 26 färbt danach den Bereich
     unter der gläsernen Adressleiste weiß. Wichtig: kein anderes festes Element darf ganz oben darüber liegen. */
  var marke=document.querySelector('.kat-marke'),deckel=null,glas=null;
  function klebtPruefen(){if(!nav||!marke)return;
    /* klebt = steht oben fest; am Ende der Speisekarte schiebt der Inhalt das Band nach oben weg – dann darf die weiße Fläche nicht stehen bleiben */
    var r=nav.getBoundingClientRect(),k=getComputedStyle(nav).position==='sticky'&&r.top-marke.getBoundingClientRect().bottom>1&&r.bottom>0;
    if(k!==nav.classList.contains('klebt'))nav.classList.toggle('klebt',k);
    if(k&&glas){glas.remove();glas=null;}
    if(!k&&!glas){glas=document.createElement('div');glas.className='glas-oben';glas.setAttribute('aria-hidden','true');document.body.appendChild(glas);}
    if(k&&!deckel){deckel=document.createElement('div');deckel.className='deckel-oben';deckel.setAttribute('aria-hidden','true');document.body.appendChild(deckel);}
    if(deckel)deckel.style.height=Math.max(0,Math.round(r.bottom))+'px';
    if(!k&&deckel){deckel.remove();deckel=null;}
    if(dbg){var vv=window.visualViewport;dbg.textContent='scrollY '+Math.round(scrollY)+'\ninnerH '+innerHeight+' vv.h '+(vv?Math.round(vv.height):'-')+' vv.top '+(vv?Math.round(vv.offsetTop):'-')+
      '\nnav.top '+Math.round(nav.getBoundingClientRect().top)+' marke.bottom '+Math.round(marke.getBoundingClientRect().bottom)+
      '\nposition '+getComputedStyle(nav).position+' top '+getComputedStyle(nav).top+'\nklebt '+nav.classList.contains('klebt')+
      '\ndeckel '+(deckel?deckel.style.height:'-')+' glas '+(glas?'ja':'-')+'\nsafe-top '+getComputedStyle(document.documentElement).getPropertyValue('--sat');}}
  var dbg=null;
  if(/[?&]debug/.test(location.search)){dbg=document.createElement('div');dbg.id='debug-info';document.body.appendChild(dbg);
    document.documentElement.style.setProperty('--sat','env(safe-area-inset-top)');
    var tst=document.createElement('div');tst.style.cssText='position:fixed;top:0;height:env(safe-area-inset-top)';document.body.appendChild(tst);
    document.documentElement.style.setProperty('--sat',tst.getBoundingClientRect().height+'px');}
  function verfolgen(){klebtPruefen();if(!fest)markiere(imBlick());}
  function loesen(){fest=null;}
  window.addEventListener('scroll',function(){
    if(geplant)return;geplant=true;
    requestAnimationFrame(function(){geplant=false;verfolgen();});
  },{passive:true});
  window.addEventListener('resize',verfolgen);window.addEventListener('pageshow',verfolgen);window.addEventListener('load',verfolgen);
  window.addEventListener('wheel',loesen,{passive:true});
  window.addEventListener('touchmove',loesen,{passive:true});
  window.addEventListener('mousedown',function(ev){if(!(nav&&nav.contains(ev.target)))loesen();});
  window.addEventListener('keydown',function(ev){
    var t=ev.target&&ev.target.tagName;
    if(t!=='INPUT'&&t!=='TEXTAREA'&&/^(ArrowUp|ArrowDown|PageUp|PageDown|Home|End| )$/.test(ev.key))loesen();
  });
  Object.keys(links).forEach(function(id){
    links[id].addEventListener('click',function(){fest=id;markiere(id);});
  });
  if(links[location.hash.slice(1)]){fest=location.hash.slice(1);markiere(fest);}else verfolgen();

  /* Suche */
  function norm(s){
    return s.toLowerCase().replace(/ä|ae/g,'a').replace(/ö|oe/g,'o').replace(/ü|ue/g,'u').replace(/ß/g,'ss')
      .normalize('NFD').replace(/[̀-ͯ]/g,'');
  }
  /* Ernährung: '' | 'veg' | 'pesc' – filtert die Karte und blendet im Zettel Fleisch (und bei veg Fisch) aus */
  var DIAET='',vegK=document.getElementById('veg-schalter');
  document.querySelectorAll('[data-diaet]').forEach(function(k){k.addEventListener('click',function(){
    DIAET=DIAET===k.dataset.diaet?'':k.dataset.diaet;
    document.querySelectorAll('[data-diaet]').forEach(function(x){x.setAttribute('aria-pressed',String(x.dataset.diaet===DIAET));});
    suchen();try{zeichnen();}catch(e){}});});
  var feld=document.getElementById('suche-feld'),gerichte=[].slice.call(document.querySelectorAll('.gericht'));
  var treffer=document.querySelector('.treffer'),nichts=document.querySelector('.nichts'),wort=nichts&&nichts.querySelector('q');
  gerichte.forEach(function(g){g._s=norm(g.getAttribute('data-s'));});
  function suchen(){
    var roh=feld.value.trim(),q=norm(roh),teile=q.split(/\s+/).filter(Boolean),n=0,veg=!!DIAET;
    gerichte.forEach(function(g){var ok=teile.every(function(w){return g._s.indexOf(w)>-1;})&&(!DIAET||g.hasAttribute('data-veg')||(DIAET==='pesc'&&g.hasAttribute('data-fisch')));g.hidden=!ok;if(ok)n++;});
    document.querySelectorAll('.liste').forEach(function(l){
      var v=l.querySelectorAll('.gericht:not([hidden])').length;l.style.setProperty('--zeilen',Math.max(1,Math.ceil(v/2)));
      l.closest('.abschnitt').hidden=v===0;
    });
    document.querySelectorAll('.gruppe').forEach(function(g){
      var leer=!g.querySelector('.gericht:not([hidden])');g.hidden=leer;if(links[g.id])links[g.id].classList.toggle('leer',leer);
    });
    treffer.hidden=!(teile.length||veg)||n===0;
    treffer.textContent=n===1?L('1 Gericht gefunden','1 dish found'):n+L(' Gerichte gefunden',' dishes found');
    nichts.hidden=!(teile.length&&n===0);if(wort)wort.textContent=roh;
    document.body.classList.toggle('sucht',teile.length>0);
    var bl=document.querySelector('.beliebt');if(bl){bl.hidden=teile.length>0;
      bl.querySelectorAll('.tipp').forEach(function(t){t.hidden=DIAET?!(t.hasAttribute('data-veg')||(DIAET==='pesc'&&t.hasAttribute('data-fisch'))):t.hasAttribute('data-nur-diaet');});
      bl.querySelectorAll('ul.tipps').forEach(function(u){var leer=!u.querySelector('.tipp:not([hidden])');u.hidden=leer;
        var h=u.previousElementSibling;if(h&&h.classList.contains('beliebt-titel'))h.hidden=leer;});
      if(!bl.querySelector('.tipp:not([hidden])'))bl.hidden=true;}
    if(typeof letzteZeigen==='function')letzteZeigen();
    fest=null;verfolgen();
  }

  /* Bestellzettel mit Wünschen je Gericht */
  var ZK='saray-bestellzettel-2',zettel=[],uidZ=1,offen=null;
  var SOSSEN=['Knoblauch','Kräuter','Chili'],OHNE=['Zwiebeln','Tomaten','Gurken','Rotkohl','Weißkohl','Eisbergsalat'];
  var GEMUESE=['Paprika','Zwiebel','Champignon','Tomate','Peperoni','Ananas','Oliven','Brokkoli','Mais'];
  var FLEISCH=['Schinken','Salami','Dönerfleisch','Hähnchen-Dönerfleisch'],KAESE=['Käse','Halloumikäse','Fetakäse'];
  /* Pizzabrötchen: ein Belag zur Wahl (laut Karte Salami, Schinken, Dönerfleisch oder nach Wahl) */
  var BELAG=['Salami','Schinken','Dönerfleisch','Hähnchen-Dönerfleisch','Käse','Halloumikäse','Fetakäse','Gemüse'];
  var PAARE=[['1','2'],['3','4'],['6','7'],['9','10'],['11','12'],['13','14'],['15','16'],['23','25'],['30','31'],['32','33'],['36','37'],
    ['40','41'],['42','43'],['50','51'],['52','53'],['54','55'],['60','61'],['123','124']],OHNE_K={},MIT_K={};
  PAARE.forEach(function(pq){OHNE_K[pq[0]]=pq[1];MIT_K[pq[1]]=pq[0];});
  /* Varianten: Form, Füllung, extra Fleisch (Super), Käse, Beilage.
     Die Schalter im Zettel suchen damit das passende Gericht der Karte. */
  var VAR={},FUELL=['kalb','huhn','beide','veg','falafel','halloumi','hack','schinken','schinkenananas','hawaii','tonno','bauern','mozzarella'];
  var F_NAME={kalb:['Dönerfleisch','Döner meat'],huhn:['Hähnchen','Chicken'],veg:['ohne Fleisch','No meat'],falafel:['Falafel','Falafel'],
    halloumi:['Halloumi','Halloumi'],hack:['Hackfleisch','Minced meat'],beide:['Döner + Hähnchen (Saray)','Döner + chicken (Saray)'],
    schinken:['Schinken','Ham'],schinkenananas:['Schinken + Ananas','Ham + pineapple'],hawaii:['Ananas','Pineapple'],tonno:['Thunfisch','Tuna'],
    bauern:['Bauernsalat (Käse, Oliven, Peperoni)','Farmer’s (cheese, olives, hot peppers)'],mozzarella:['Mozzarella','Mozzarella']};
  var FLEISCH_F=['kalb','huhn','beide','hack','schinken','schinkenananas'],FISCH_F=['tonno'];
  function erlaubtF(f){return !(DIAET&&FLEISCH_F.indexOf(f)>-1)&&!(DIAET==='veg'&&FISCH_F.indexOf(f)>-1);}
  function ohneFleisch(liste){return DIAET?liste.filter(function(v){return FLEISCH.indexOf(v)<0&&['Salami','Schinken','Dönerfleisch','Hähnchen-Dönerfleisch'].indexOf(v)<0;}):liste;}
  /* Pizza: Zutaten aus Name/Beschreibung (gleiche Namen wie bei den Extras) – zum Abwählen */
  var PZ_WORT=[['thunfisch','Thunfisch'],['dönerfleisch','Dönerfleisch'],['salami','Salami'],['schinken','Schinken'],['champignon','Champignon'],
    ['paprika','Paprika'],['brokkoli','Brokkoli'],['zwiebel','Zwiebel'],['tomate','Tomate'],['ananas','Ananas'],['oliven','Oliven'],['peperoni','Peperoni'],
    ['mais','Mais'],['knoblauch','Knoblauch'],['feta','Fetakäse'],['halloumi','Halloumikäse'],['mozzarella','Mozzarella']];
  function pizzaZutaten(x){
    var t=(x.n+' '+(x.d||'')+' '+((x.o&&x.o.va)||'')).toLowerCase(),r=[];
    if(/hähnchen-?döner/.test(t)){r.push('Hähnchen-Dönerfleisch');t=t.replace(/hähnchen-?dönerfleisch/g,'');}
    PZ_WORT.forEach(function(w){if(t.indexOf(w[0])>-1&&r.indexOf(w[1])<0)r.push(w[1]);});
    if(/(^|[^a-zäöü])ei([^a-zäöü]|$)/.test(t))r.push('Ei');
    r.push('Käse');return r;
  }
  var BEI=['S','P','SP'],BEI_NAME={S:['Salat','Salad'],P:['Pommes','Fries'],SP:['Salat + Pommes','Salad + fries']};
  [ /* k, Form, Füllung, Super, Käse, Beilage */
    ['1','doener','kalb',0,0],['2','doener','kalb',0,1],['6','doener','kalb',1,0],['7','doener','kalb',1,1],
    ['30','doener','huhn',0,0],['31','doener','huhn',0,1],['32','doener','huhn',1,0],['33','doener','huhn',1,1],
    ['3','doener','veg',0,0],['4','doener','veg',0,1],['5','doener','halloumi',0,0],['11','doener','falafel',0,0],['12','doener','falafel',0,1],
    ['50','duerum','kalb',0,0],['51','duerum','kalb',0,1],['54','duerum','kalb',1,0],['55','duerum','kalb',1,1],
    ['40','duerum','huhn',0,0],['41','duerum','huhn',0,1],['42','duerum','huhn',1,0],['43','duerum','huhn',1,1],
    ['52','duerum','veg',0,0],['53','duerum','veg',0,1],['57','duerum','halloumi',0,0],['58','duerum','falafel',0,0],
    ['13','box','kalb',0,0],['14','box','kalb',0,1],['15','box','huhn',0,0],['16','box','huhn',0,1],
    ['21','teller','kalb',0,0,'S'],['22','teller','kalb',0,0,'P'],['23','teller','kalb',0,0,'SP'],['25','teller','kalb',0,1,'SP'],
    ['34','teller','huhn',0,0,'S'],['35','teller','huhn',0,0,'P'],['36','teller','huhn',0,0,'SP'],['37','teller','huhn',0,1,'SP'],
    ['24','teller','veg',0,0,'SP'],['26','teller','beide',0,0,'SPR'],['28','ueber','kalb',0,0],['38','ueber','huhn',0,0],['18','kinder','kalb',0,0],['19','kinder','huhn',0,0],
    ['130','salat','veg',0,0],['132','salat','veg',0,1],['131','salat','kalb',0,0],['133','salat','kalb',0,1],['134','salat','huhn',0,0],['135','salat','huhn',0,1],
    ['136','salat','tonno',0,0],['137','salat','hawaii',0,0],['138','salat','schinken',0,0],['139','salat','schinkenananas',0,0],['140','salat','bauern',0,0],
    ['141','salat','halloumi',0,0],['142','salat','falafel',0,0],['143','salat','mozzarella',0,0],
    ['121','lahmacun','hack',0,0],['123','lahmacun','kalb',0,0],['124','lahmacun','kalb',0,1]
  ].forEach(function(v){VAR[v[0]]={k:v[0],form:v[1],f:v[2],sup:v[3],kae:v[4],bei:v[5]||''};});
  /* bestes Gericht mit den gewünschten Merkmalen; Vorrang: Beilage, Käse, Super */
  function variante(k,wunsch,streng){
    var a=VAR[k];if(!a)return null;var w=Object.assign({},a,wunsch),best=null,bp=-1;
    Object.keys(VAR).forEach(function(kk){var v=VAR[kk];if(v.form!==a.form||v.f!==w.f||!gerichtLi(kk))return;
      if(streng&&(v.sup!==w.sup||v.kae!==w.kae||v.bei!==w.bei))return;
      var pkt=(v.bei===w.bei?4:0)+(v.kae===w.kae?2:0)+(v.sup===w.sup?1:0)+(v.bei==='SP'?.5:0);if(pkt>bp){bp=pkt;best=kk;}});
    return best===k?null:best;
  }
  function kaesePartner(k){return VAR[k]?variante(k,{kae:VAR[k].kae?0:1},true):(OHNE_K[k]||MIT_K[k]||null);}
  /* Verfügbarkeit: feste Regeln aus build.py + tagesaktuelle aus status.json */
  var SPERR={"doener": {"de": "Döner", "en": "Döner", "nr": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "30", "31", "32", "33", "34", "35", "36", "37", "38"]}, "duerum": {"de": "Dürüm", "en": "Dürüm", "nr": ["50", "51", "52", "53", "54", "55", "56", "57", "58", "40", "41", "42", "43"]}, "teller": {"de": "Box & Teller", "en": "Boxes & plates", "nr": ["13", "14", "15", "16", "21", "22", "23", "24", "25", "26", "28"]}, "pizza": {"de": "Pizza", "en": "Pizza", "nr": ["80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102", "103", "104", "105", "125"]}, "lahmacun": {"de": "Lahmacun", "en": "Lahmacun", "nr": ["120", "121", "122", "123", "124"]}, "baguette": {"de": "Baguette", "en": "Baguette", "nr": ["150", "151", "152", "153", "154", "156", "157", "158", "159", "160"]}, "salate": {"de": "Salate", "en": "Salads", "nr": ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143"]}, "schnitzel": {"de": "Schnitzel & Nuggets", "en": "Schnitzel & nuggets", "nr": ["70", "71", "72", "73", "60", "61", "62", "63", "64", "65"]}, "kinder": {"de": "Für Kinder", "en": "For kids", "nr": ["17", "18", "19", "20"]}, "getraenke": {"de": "Getränke", "en": "Drinks", "nr": []}, "huhn": {"de": "Hähnchen", "en": "Chicken", "nr": ["30", "31", "32", "33", "34", "35", "36", "37", "38", "40", "41", "42", "43", "15", "16", "26", "102", "105", "134", "135", "19"]}, "nuggets": {"de": "Nuggets", "en": "Nuggets", "nr": ["60", "61", "62", "63", "64", "65", "20"]}, "falafel": {"de": "Falafel", "en": "Falafel", "nr": ["11", "12", "58", "24", "142"]}, "halloumi": {"de": "Halloumi", "en": "Halloumi", "nr": ["5", "57", "24", "26", "98", "99", "158", "141"]}, "schnitzel-fleisch": {"de": "Schnitzel", "en": "Schnitzel", "nr": ["9", "10", "159", "70"]}, "fisch": {"de": "Fisch", "en": "Fish", "nr": ["71"]}, "z:Pommes": {"de": "Pommes", "en": "Fries", "nr": ["72", "73"]}},REGELN_FEST=[],REGELN=REGELN_FEST.slice(),LADEN_N={freital:'Freital',altenberg:'Altenberg'};
  function datumISO(off){return new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date(Date.now()+off*864e5));}
  function minAus(t){var q=String(t).split(':');return (+q[0])*60+(+q[1]||0);}
  function trifft(r,k){var w=[].concat(r.was||[]);return w.some(function(v){v=String(v);return v===k||(SPERR[v]&&SPERR[v].nr.indexOf(k)>-1);});}
  /* null = verfügbar, sonst {art:'aus'|'ab'|'bis', zeit} für Laden, Tag (0 = heute) und Uhrzeit (Minuten) */
  function sperre(k,laden,off,min){
    var tag=(jetzt().tag+off)%7,d=datumISO(off),res=null;
    REGELN.forEach(function(r){
      if(res&&res.art==='aus')return;if(!trifft(r,k))return;
      if(r.laden&&r.laden!=='alle'&&r.laden!==laden)return;
      if(r.datum&&[].concat(r.datum).indexOf(d)<0)return;
      if(r.tage&&r.tage.indexOf(tag)<0)return;
      if(r.ab&&min<minAus(r.ab))res={art:'ab',zeit:r.ab};
      else if(r.bis&&min>=minAus(r.bis))res={art:'bis',zeit:r.bis};
      else if(!r.ab&&!r.bis)res={art:'aus',dauer:!r.datum};
    });
    return res;
  }
  function uhrK(t){var m=minAus(t),h=Math.floor(m/60),r=m%60;return SP!=='de'?h+':'+(r<10?'0':'')+r:(r?h+':'+(r<10?'0':'')+r:h)+' Uhr';}
  function sperrText(sp,heute){
    if(sp.art==='aus')return (heute===false||sp.dauer)?L('nicht verfügbar','not available'):L('heute nicht verfügbar','not available today');
    if(sp.art==='ab')return L('erst ab ','only from ')+uhrK(sp.zeit);
    return L('nur bis ','only until ')+uhrK(sp.zeit);
  }
  /* Abholzeitpunkt aus der Auswahl im Zettel */
  var ZINFO={};
  function abholung(){return abh.laden&&ZINFO[abh.zeit]?{laden:abh.laden,off:ZINFO[abh.zeit].off,min:ZINFO[abh.zeit].min}:null;}
  function sperreZettel(k){var a=abholung();return a?sperre(k,a.laden,a.off,a.min):null;}
  /* Speisekarte: Hinweis am Gericht, ausgegraut, wenn heute in keinem Laden zu haben */
  function verfZeigen(){
    var n=jetzt();
    document.querySelectorAll('li[data-k]').forEach(function(li){
      var k=li.dataset.k,sp={};Object.keys(LADEN_N).forEach(function(l){sp[l]=sperre(k,l,0,n.min);});
      var gesperrt=Object.keys(sp).filter(function(l){return sp[l];}),txt='',aus;
      if(abh.laden&&LADEN_N[abh.laden]){ /* Laden gewählt: Karte gilt für diesen Laden */
        var s1=sp[abh.laden];txt=s1?sperrText(s1)+L(' in ',' in ')+LADEN_N[abh.laden]:'';aus=!!s1&&s1.art==='aus';
      }else{
        if(gesperrt.length===2&&sperrText(sp.freital)===sperrText(sp.altenberg))txt=sperrText(sp.freital);
        else txt=gesperrt.map(function(l){return LADEN_N[l]+': '+sperrText(sp[l]);}).join(' · ');
        aus=gesperrt.length===2&&sp.freital.art==='aus'&&sp.altenberg.art==='aus';
      }
      li.classList.toggle('nicht-da',aus);
      var pk=li.querySelector('.plus');if(pk){pk.disabled=aus;}
      var m=li.querySelector('.marke-verf');
      if(!txt){if(m)m.remove();return;}
      if(!m){m=el('span','marke-verf');var ziel=li.querySelector('.name, .tipp-name');if(ziel)ziel.appendChild(m);else return;}
      m.textContent=txt;
    });
  }
  function regelnLaden(){
    if(!window.fetch)return;
    fetch('status.json',{cache:'no-store'}).then(function(r){return r.ok?r.json():{};}).then(function(d){
      REGELN=REGELN_FEST.concat(Array.isArray(d.regeln)?d.regeln:[]);verfZeigen();zeichnen();waAktualisieren();
    }).catch(function(){});
  }
  function wechseln(x,ziel){var li=gerichtLi(ziel);if(!li)return;x.k=li.dataset.k;x.n=li.dataset.n;x.d=li.dataset.d;x.c=+li.dataset.p;}
  function preisDiff(x,ziel){var li=gerichtLi(ziel);if(!li)return '';var d=(+li.dataset.p)-x.c;return d?' ('+(d<0?'−':'+')+euro(Math.abs(d))+')':'';}
  var W={'Knoblauch':'garlic','Thunfisch':'tuna','Mozzarella':'mozzarella','Ei':'egg','Kräuter':'herb','Chili':'chili','Zwiebeln':'onions','Tomaten':'tomatoes','Gurken':'cucumber','Rotkohl':'red cabbage',
    'Weißkohl':'white cabbage','Eisbergsalat':'iceberg lettuce','Paprika':'bell pepper','Zwiebel':'onion','Champignon':'mushrooms','Tomate':'tomato',
    'Gemüse':'vegetables','Peperoni':'hot peppers','Ananas':'pineapple','Oliven':'olives','Brokkoli':'broccoli','Mais':'corn','Schinken':'ham','Salami':'salami',
    'Dönerfleisch':'döner meat','Hähnchen-Dönerfleisch':'chicken döner meat','Käse':'cheese','Halloumikäse':'halloumi','Fetakäse':'feta'};
  function w(v){if(SP==='de'||!W[v])return v;var x=T(W[v]);return x.charAt(0).toUpperCase()+x.slice(1);}
  function gerichtLi(nr){return document.querySelector('li.gericht[data-k="'+nr+'"],li.paket[data-k="'+nr+'"]');}
  try{zettel=JSON.parse(localStorage.getItem(ZK)||'[]');if(!Array.isArray(zettel))zettel=[];}catch(e){zettel=[];}
  zettel.forEach(function(x){x.u=uidZ++;if(x.o&&!Array.isArray(x.o.s))x.o.s=x.o.s?[x.o.s]:[];});
  /* Bestellnummer: kurz, gut vorzulesen; neu, sobald nach dem Senden etwas geändert wird */
  function neueNr(){var b='ACDEFHKLMNPRTUVWXY';return b.charAt(Math.floor(Math.random()*b.length))+(10+Math.floor(Math.random()*90));}
  var BNR=neueNr(),bnrGesendet=false;
  function speichern(){if(bnrGesendet){BNR=neueNr();bnrGesendet=false;}try{localStorage.setItem(ZK,JSON.stringify(zettel.map(function(x){var y=Object.assign({},x);delete y.u;return y;})));}catch(e){}}
  function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  function grund(t){return {s:(t==='D'||t==='SA')?['Kräuter']:[],ohne:[],ex:[],wahl:[],va:''};}
  function exPreis(o){return (o.ex||[]).reduce(function(a,e){return a+(GEMUESE.indexOf(e)>-1?150:200);},0);}
  function aktionZ(x){var li=gerichtLi(x.k);if(!li)return null;var gs=li.dataset.g?li.dataset.g.split('|'):[''];
    var tag=abh.tag||isoTag(0),zi=ZINFO[abh.zeit],min=zi?zi.min:(tag===isoTag(0)?jetzt().min:null);
    return aktion(x.k,Math.max(0,gs.indexOf(x.g||'')),tag,abh.laden||null,min);}
  /* Beilage (Pommes/Reis) vom Laden ausgeschaltet: Gericht ohne diese Beilage, je 0,50 € weniger */
  var BEILAGEN={"35": ["Pommes"], "36": ["Pommes"], "37": ["Pommes"], "13": ["Pommes"], "14": ["Pommes"], "15": ["Pommes"], "16": ["Pommes"], "22": ["Pommes"], "23": ["Pommes"], "24": ["Pommes"], "25": ["Pommes"], "26": ["Pommes", "Reis"], "70": ["Pommes"], "71": ["Pommes"], "62": ["Pommes"], "64": ["Pommes"], "65": ["Pommes"], "17": ["Pommes"], "20": ["Pommes"]},BEILAGE_RABATT=50;
  function fehlend(x){return (BEILAGEN[x.k]||[]).filter(function(b){return zAus(b);});}
  function stueck(x){var ak=aktionZ(x);return (ak?ak.c:x.c)+exPreis(x.o)-fehlend(x).length*BEILAGE_RABATT;}
  function sig(x){var o=x.o;return [x.k,x.g,o.s.slice().sort().join(','),o.ohne.slice().sort().join(','),o.ex.slice().sort().join(','),o.wahl.slice().sort().join(','),o.va,x.notiz||'',x.fuer||''].join('|');}
  function liste(a,en){var u=en?' '+T('and')+' ':' und ';return a.length<2?a.join(''):a.slice(0,-1).join(', ')+u+a[a.length-1];}
  /* Wünsche als Text; en=true nur für die Anzeige, die Nachricht an den Laden ist immer deutsch */
  function wuensche(x,en){
    var o=x.o,t=[],tr=function(a){return en?a.map(function(v){return W[v]?T(W[v]):v;}):a;};
    if(x.t==='D'||x.t==='SA'){var so=SOSSEN.filter(function(n){return o.s.indexOf(n)>-1;});
      if(en)t.push(!so.length?T('no sauce'):fuell(T('{list} sauce'),{list:liste(tr(so),true)}));
      else t.push(!so.length?'ohne Soße':so.length===1?so[0]+'-Soße':so.slice(0,-1).join('-, ')+'- und '+so[so.length-1]+'-Soße');}
    if(o.ohne.length)t.push(en?fuell(T('no {list}'),{list:liste(tr(o.ohne),en)}):'ohne '+liste(o.ohne,en));
    var fe=fehlend(x);if(fe.length)t.push(en?fuell(T('no {list}'),{list:liste(fe.map(function(b){return T(b==='Pommes'?'fries':'rice');}),en)})+' ('+T('not available')+', −'+euro(fe.length*BEILAGE_RABATT)+')'
      :'ohne '+liste(fe,en)+' (heute aus, −'+euro(fe.length*BEILAGE_RABATT)+')');
    if(x.t==='S')t.push(o.wahl.length<3?(en?T('choose '+(3-o.wahl.length)+' more toppings'):'noch '+(3-o.wahl.length)+(3-o.wahl.length===1?' Zutat wählen':' Zutaten wählen')):(en?fuell(T('with {list}'),{list:liste(tr(o.wahl),en)}):'mit '+liste(o.wahl,en)));
    if(x.t==='R')t.push(o.va?(en?fuell(T('option {x}'),{x:o.va.charAt(0)}):'Variante '+o.va.charAt(0)):(en?T('choose option'):'Variante wählen'));
    if(x.t==='B')t.push(o.va?(en?fuell(T('with {list}'),{list:W[o.va]?T(W[o.va]):o.va}):'mit '+o.va):(en?T('choose topping'):'Belag wählen'));
    tr(o.ex).forEach(function(e){t.push(en?fuell(T('extra {x}'),{x:e}):'extra '+e);});
    return t.join(', ');
  }
  /* Anzeigename/Beschreibung in der gewählten Sprache */
  function nameFremd(li,fallback){if(!li)return fallback;var m=/^Nr\. (\S+) /.exec(li.dataset.n||'');return (m?T('No.')+' '+m[1]+' ':'')+T(li.dataset.nen||'');}
  function nameA(x){if(SP==='de')return x.n;return nameFremd(gerichtLi(x.k),x.n);}
  function beschrA(x){if(SP==='de')return x.d;var li=gerichtLi(x.k);return li&&li.dataset.dn!=null?T(li.dataset.dn):x.d;}
  function zusammenfassen(){
    var neu=[],idx={};
    zettel.forEach(function(x){var k=sig(x);if(idx[k]!=null&&x.u!==offen&&neu[idx[k]].u!==offen){neu[idx[k]].q+=x.q;}else{idx[k]=neu.length;neu.push(x);}});
    zettel=neu;
  }
  var zl=document.getElementById('zettel-leiste'),huelle=document.getElementById('zettel'),zliste=document.getElementById('zettel-liste'),
      zsumme=document.getElementById('zettel-summe'),zmeld=document.getElementById('zettel-meldung'),meldTimer=null,zuletzt=null;
  function anzahl(){return zettel.reduce(function(a,x){return a+x.q;},0);}
  function brutto(){return zettel.reduce(function(a,x){return a+x.q*stueck(x);},0);}
  /* Firmen-Code: Rabatt in Prozent auf alles ohne Aktionspreis; gilt je nach Code nur in einem Laden, zu bestimmten Uhrzeiten, bis zu einem Datum */
  var CODES=[];
  function codeAktiv(){var c=abh.code;if(!c)return null;var d=CODES.filter(function(x){return x.h===c.h;})[0];if(!d)return null;
    var zi=ZINFO[abh.zeit],tag=abh.tag||isoTag(0);
    if(d.bis&&tag>d.bis)return null;if(d.laden&&abh.laden&&d.laden!==abh.laden)return null;
    if(d.za!=null&&zi&&(zi.min<d.za||zi.min>=d.zb))return null;return d;}
  function rabatt(){var d=codeAktiv();if(!d)return 0;
    return Math.round(zettel.reduce(function(a,x){return a+(aktionZ(x)?0:x.q*stueck(x));},0)*d.prozent/100);}
  function summe(){return brutto()-rabatt();}
  function melden(t){zmeld.textContent=t;zmeld.hidden=false;clearTimeout(meldTimer);meldTimer=setTimeout(function(){zmeld.hidden=true;},2400);}
  function el(tag,cls,text){var x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;return x;}
  function knopf(text,attrs){var b=el('button',null,text);b.type='button';for(var a in attrs)b.setAttribute(a,attrs[a]);return b;}
  /* Zutat vom Laden ausgeschaltet (Chef-App „Zutaten“)? Gilt für die gewählte Abholung, sonst jetzt */
  var Z_NORM={'Zwiebeln':'Zwiebel','Tomaten':'Tomate'},Z_GRUPPE={'Hähnchen-Dönerfleisch':'huhn','Halloumikäse':'halloumi'};
  function zAus(v){
    var a=abholung()||{laden:abh.laden||null,off:0,min:jetzt().min};
    return sperre('z:'+(Z_NORM[v]||v),a.laden,a.off,a.min)||(Z_GRUPPE[v]?sperre(Z_GRUPPE[v],a.laden,a.off,a.min):null);
  }
  /* ausgeschaltete Zutaten aus Wünschen entfernen (Soße, Extras, Zutaten, Belag) */
  function bereinigen(x){var o=x.o;if(!o)return;
    ['s','ex','wahl'].forEach(function(a){if(Array.isArray(o[a]))o[a]=o[a].filter(function(v){return !zAus(v);});});
    /* „ohne Käse“ und gleichzeitig Käse als Zutat zur Wahl geht nicht */
    if(Array.isArray(o.ohne)&&Array.isArray(o.wahl))o.wahl=o.wahl.filter(function(v){return o.ohne.indexOf(v)<0;});
    if(x.t==='B'&&o.va&&zAus(o.va))o.va='';}
  function chips(titel,werte,gewaehlt,art,uid,extra){
    var g=el('div','z-gruppe');g.appendChild(el('span','z-gruppe-titel',titel));var wb=el('div','z-chips');
    werte.forEach(function(v){var an=gewaehlt.indexOf(v)>-1,sp=art==='va'&&/^[A-D]: /.test(v)?null:zAus(v);
      var b=knopf(w(v)+(extra||'')+(sp?' – '+sperrText(sp):''),{'class':'chip'+(sp?' chip-aus':''),'aria-pressed':String(an&&!sp),'data-o':art,'data-w':v,'data-u':uid});
      if(sp)b.disabled=true;
      if(art==='wahl'&&!an&&gewaehlt.length>=3)b.disabled=true;wb.appendChild(b);});
    g.appendChild(wb);return g;
  }
  function editor(x){
    var box=el('div','z-optionen'),o=x.o;
    if(x.t==='D'||x.t==='SA')box.appendChild(chips(L('Soße (mehrere möglich)','Sauce (choose any)'),SOSSEN,o.s,'s',x.u));
    var va=VAR[x.k];
    if((x.t==='D'||x.t==='SA')&&va){
      var fg=el('div','z-gruppe');fg.appendChild(el('span','z-gruppe-titel',va.form==='salat'?L('Belag','Topping'):L('Füllung','Filling')));var fw=el('div','z-chips');
      FUELL.forEach(function(f){
        if(f!==va.f&&!erlaubtF(f))return;
        var ziel=f===va.f?x.k:variante(x.k,{f:f});if(!ziel)return;
        var spF=f===va.f?null:(sperreZettel(ziel)||(function(){var nn=jetzt();var a=sperre(ziel,'freital',0,nn.min),b=sperre(ziel,'altenberg',0,nn.min);return a&&b&&a.art==='aus'&&b.art==='aus'?a:null;})());
        var fk=knopf(L(F_NAME[f][0],F_NAME[f][1])+(f===va.f?'':spF?' – '+sperrText(spF):preisDiff(x,ziel)),{'class':'chip','aria-pressed':String(f===va.f),'data-fuell':f,'data-u':x.u});
        if(spF)fk.disabled=true;fw.appendChild(fk);
      });
      if(fw.children.length>1){fg.appendChild(fw);box.appendChild(fg);}
      if(va.form==='teller'){ /* Beilage: Salat, Pommes oder beides – wechselt zum passenden Teller */
        var bopt=BEI.filter(function(b){if(b===va.bei)return true;var z=variante(x.k,{bei:b});return z&&VAR[z].bei===b;});
        if(bopt.length>1){var bg=el('div','z-gruppe');bg.appendChild(el('span','z-gruppe-titel',L('Beilage','Side')));var bw=el('div','z-chips');
          bopt.forEach(function(b){var zb=b===va.bei?null:variante(x.k,{bei:b});
            var spB=(b==='P'||b==='SP')&&zAus('Pommes')||(zb?(sperreZettel(zb)||sperre(zb,abh.laden||null,0,jetzt().min)):null);
            var kb2=knopf(L(BEI_NAME[b][0],BEI_NAME[b][1])+(spB?' – '+sperrText(spB):zb?preisDiff(x,zb):''),{'class':'chip'+(spB?' chip-aus':''),'aria-pressed':String(b===va.bei),'data-bei':b,'data-u':x.u});
            if(spB)kb2.disabled=true;bw.appendChild(kb2);});
          bg.appendChild(bw);box.appendChild(bg);}
      }
      var su=variante(x.k,{sup:va.sup?0:1},true);
      if(su){var sg=el('div','z-gruppe');sg.appendChild(el('span','z-gruppe-titel',L('Fleisch','Meat')));var sw=el('div','z-chips');
        sw.appendChild(knopf(L('extra Fleisch (Super)','extra meat (Super)')+(va.sup?'':preisDiff(x,su)),{'class':'chip','aria-pressed':String(!!va.sup),'data-super':x.u}));
        sg.appendChild(sw);box.appendChild(sg);}
    }
    var kp=(x.t==='D'||x.t==='SA')&&kaesePartner(x.k);
    if(kp){
      var mit=VAR[x.k]?!!VAR[x.k].kae:!!MIT_K[x.k];
      var kg=el('div','z-gruppe');kg.appendChild(el('span','z-gruppe-titel',L('Käse','Cheese')));var kw=el('div','z-chips');
      kw.appendChild(knopf(L('mit Käse','with cheese')+(mit?'':preisDiff(x,kp)),{'class':'chip','aria-pressed':String(mit),'data-kaese':x.u}));
      kg.appendChild(kw);box.appendChild(kg);
    }
    if(x.t==='D'||x.t==='SA'){
      /* Gemüse: alles drin, Abgewähltes geht als „ohne …“ an den Laden */
      var gg=chips(L('Gemüse – abwählen, was nicht rein soll','Vegetables – tap to leave out'),OHNE,[],'ohne',x.u);
      gg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(!c.disabled&&o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(gg);
    }
    if(x.t==='S'){var wg=chips(L('3 Zutaten Ihrer Wahl (','3 toppings of your choice (')+o.wahl.length+L(' von 3)',' of 3)'),GEMUESE.concat(ohneFleisch(FLEISCH),KAESE).concat(o.wahl.filter(function(v){return ohneFleisch([v]).length===0;})),o.wahl,'wahl',x.u);
      wg.querySelectorAll('.chip').forEach(function(c){if(o.ohne.indexOf(c.dataset.w)>-1){c.disabled=true;c.classList.add('chip-aus');c.setAttribute('aria-pressed','false');
        c.textContent=w(c.dataset.w)+L(' – abgewählt',' – left out');}});
      box.appendChild(wg);}
    if(x.t==='R')box.appendChild(chips(L('Variante','Option'),(x.v||'').split('|').filter(Boolean),[o.va],'va',x.u));
    if(x.t==='B')box.appendChild(chips(L('Belag (einer zur Wahl)','Topping (choose one)'),ohneFleisch(BELAG).concat(o.va&&ohneFleisch([o.va]).length===0?[o.va]:[]),[o.va],'va',x.u));
    if(x.t==='P'||x.t==='R'||x.t==='S'){
      var pz=x.t==='S'?['Käse']:pizzaZutaten(x);
      var pg=chips(L('Zutaten – abwählen, was nicht drauf soll','Toppings – tap to leave out'),pz,[],'ohne',x.u);
      pg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(!c.disabled&&o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(pg);
    }
    var nichtExtra=function(v){return o.ohne.indexOf(v)<0;};
    if(x.t==='P'||x.t==='S'||x.t==='R'){
      box.appendChild(chips(L('Extra je Zutat +1,50 €','Extra per topping +1,50 €'),GEMUESE.filter(nichtExtra),o.ex,'ex',x.u));
      box.appendChild(chips(L('Extra je Zutat +2,00 €','Extra per topping +2,00 €'),ohneFleisch(FLEISCH).concat(KAESE).concat(o.ex.filter(function(v){return FLEISCH.indexOf(v)>-1&&DIAET;})).filter(nichtExtra),o.ex,'ex',x.u));
    }
    return box;
  }
  function zeichnen(){
    zettel.forEach(bereinigen);
    var n=anzahl();
    zl.hidden=n===0;document.body.classList.toggle('mit-zettel',n>0);if(n===0)getraenkGefragt=false;
    zl.querySelector('.zl-anzahl').textContent=n;zl.querySelector('.zl-summe').textContent=euro(summe());
    zl.setAttribute('aria-label',L('Meine Bestellung ansehen: ','View my order: ')+n+(n===1?L(' Gericht, ',' dish, '):L(' Gerichte, ',' dishes, '))+euro(summe()));
    zliste.textContent='';
    zettel.forEach(function(x){
      var li=el('li','z-eintrag'),kopf=el('div');
      var na=nameA(x);
      kopf.appendChild(el('span','z-name',na+(x.g?' ('+x.g+')':'')));
      var wt=x.t?wuensche(x,SP!=='de'):(fehlend(x).length?beschrA(x)+(beschrA(x)?' · ':'')+wuensche(x,SP!=='de'):beschrA(x));if(wt&&SP!=='de')wt=wt.charAt(0).toUpperCase()+wt.slice(1);
      if(x.fuer)kopf.appendChild(el('span','z-fuer',L('für ','for ')+x.fuer));if(wt){var wi=el('span','z-info',wt);if(/wählen|choose/.test(wt))wi.classList.add('z-fehlt');kopf.appendChild(wi);}
      var spZ=sperreZettel(x.k);
      if(spZ){var a0=abholung();kopf.appendChild(el('span','z-info z-fehlt',
        spZ.art==='aus'?L((a0.off?'':'heute ')+'in '+LADEN_N[a0.laden]+' nicht verfügbar – bitte entfernen',(a0.off?'':'today ')+'not available in '+LADEN_N[a0.laden]+' – please remove')
        :sperrText(spZ)+L(' – bitte andere Abholzeit wählen',' – please choose another pickup time')));li.classList.add('z-gesperrt');}
      li.appendChild(kopf);li.appendChild(el('span','z-preis',euro(stueck(x)*x.q)));
      var st=el('div','z-steuer'),q=el('span','z-menge',String(x.q));
      var m=knopf('−',{'data-a':'minus','data-u':x.u,'aria-label':(x.q===1?L('Entfernen: ','Remove: '):L('Eins weniger: ','One less: '))+na});
      var pl=knopf('+',{'data-a':'plus','data-u':x.u,'aria-label':L('Eins mehr: ','One more: ')+na});
      st.appendChild(m);st.appendChild(q);st.appendChild(pl);
      /* „Fertig“ steht beim Anpassen dort, wo vorher „Anpassen“ war – rechts, gut mit dem Daumen erreichbar */
      if(x.t&&offen===x.u)st.appendChild(knopf(L('Fertig','Done'),{'class':'z-anpassen z-fertig','data-fertig':x.u}));
      if(x.t&&offen!==x.u)st.appendChild(knopf(x.q>1?L('Eins davon anpassen','Customize one of them'):L('Anpassen','Customize'),{'class':'z-anpassen','data-anpassen':x.u}));
      li.appendChild(st);
      if(offen===x.u)li.appendChild(editor(x));
      var no=document.createElement('input');no.className='z-notiz';no.type='text';no.value=x.notiz||'';no.dataset.u=x.u;no.id='notiz-'+x.u;
      no.placeholder=L('Weitere Wünsche','Other requests');no.setAttribute('aria-label',L('Weitere Wünsche zu ','Other requests for ')+na);li.appendChild(no);
      zliste.appendChild(li);
    });
    zsumme.textContent=euro(summe());codeZeigen();
    huelle.querySelector('.zettel-leer').hidden=n>0;huelle.querySelector('.zettel-voll').hidden=n===0;
    abgleichen();letzteZeigen();if(typeof sammelZeigen==='function'&&sTeil)sammelZeigen();
  }
  function finde(u){return zettel.find(function(x){return x.u===+u;});}
  function abgleichen(){
    document.querySelectorAll('li[data-k]').forEach(function(li){
      var k=li.dataset.k,mehr=!!li.dataset.g,alt=li.querySelector(':scope > .mengen'),proG={},reihe=[];
      zettel.forEach(function(x){if(x.k!==k)return;if(!(x.g in proG)){proG[x.g]=0;reihe.push(x.g);}proG[x.g]+=x.q;});
      li.classList.toggle('im-zettel',reihe.length>0&&!mehr);
      if(!reihe.length){if(alt)alt.remove();return;}
      var box=alt||el('div','mengen');box.textContent='';
      reihe.forEach(function(g){
        var z=el('span','stepper');if(g)z.appendChild(el('span','st-g',g));
        var nm=(SP!=='de'?nameFremd(li,li.dataset.n):li.dataset.n)+(g?' '+g:'');
        z.appendChild(knopf('−',{'data-st':'minus','data-k':k,'data-g':g,'aria-label':L('Eins weniger: ','One less: ')+nm}));
        z.appendChild(el('span','st-q',String(proG[g])));
        z.appendChild(knopf('+',{'data-st':'plus','data-k':k,'data-g':g,'aria-label':L('Eins mehr: ','One more: ')+nm}));
        box.appendChild(z);
      });
      if(!alt)li.appendChild(box);
    });
  }
  function hinzufuegen(li,g,c,btn){
    var neu={k:li.dataset.k,n:li.dataset.n,d:li.dataset.d,g:g,c:c,q:1,t:li.dataset.t||'',v:li.dataset.v||'',o:grund(li.dataset.t),notiz:'',u:uidZ++};
    var s1=sig(neu),x=zettel.find(function(y){return sig(y)===s1;});
    if(x)x.q++;else zettel.push(neu);
    speichern();zeichnen();
    var hinweis=neu.t==='S'?L(' Zutaten in der Bestellung wählen.',' Choose the toppings in your order.'):neu.t==='R'?L(' Variante in der Bestellung wählen.',' Choose the option in your order.'):neu.t==='B'?L(' Belag in der Bestellung wählen.',' Choose the topping in your order.'):'';
    var meldung=nameA(neu)+(g?' ('+g+')':'')+L(' ist in Ihrer Bestellung.',' added to your order.')+hinweis;
    melden(meldung);
    if(btn){btn.classList.add('ok');btn.textContent='✓';setTimeout(function(){btn.classList.remove('ok');btn.textContent='+';},1200);}
    getraenkFragen(li);
  }
  /* „Getränk dazu?“ – einmal pro Bestellung, beim ersten Essen ohne Getränk im Zettel */
  var GETRAENK_K='Cola, Fanta, Sprite oder Wasser',getraenkGefragt=false;
  function istGetraenk(k){var li=gerichtLi(k);return !!(li&&li.closest('#getraenke'));}
  function getraenkFragen(li){
    if(getraenkGefragt||sammel||li.closest('#getraenke')||zettel.some(function(x){return istGetraenk(x.k);}))return;
    var gl=gerichtLi(GETRAENK_K);if(!gl||gl.classList.contains('nicht-da'))return;
    getraenkGefragt=true;var pr=+gl.dataset.p.split('|')[0];
    function dazu(sorte){return function(){var x={k:gl.dataset.k,n:gl.dataset.n,d:gl.dataset.d,g:'',c:pr,q:1,t:'',v:'',o:grund(''),notiz:sorte,u:uidZ++};
      zettel.push(x);zusammenfassen();speichern();zeichnen();handTippZu();melden(L(sorte+' ist in Ihrer Bestellung.',sorte+' added to your order.'));};}
    setTimeout(function(){if(!huelle.hidden||zettel.some(function(x){return istGetraenk(x.k);})){getraenkGefragt=false;return;}handTippZeigen('<b>'+L('Getränk dazu?','Something to drink?')+'</b><br>'+L('0,5 l für ','0.5 l for ')+euro(pr)+L(' (zzgl. Pfand)',' (plus deposit)'),
      [['Cola',dazu('Cola')],['Fanta',dazu('Fanta')],[L('Wasser','Water'),dazu(L('Wasser','Wasser'))],[L('Nein danke','No thanks'),handTippZu]],15000);},1300);
  }
  document.addEventListener('click',function(ev){
    var b=ev.target.closest('.plus');
    if(b){
      var li=b.closest('li[data-k]'),preise=li.dataset.p.split('|').map(Number),gr=li.dataset.g?li.dataset.g.split('|'):[];
      if(preise.length===1){hinzufuegen(li,'',preise[0],b);return;}
      var alt=li.querySelector('.wahl');if(alt){alt.remove();return;}
      var w=el('div','wahl');
      gr.forEach(function(g,i){var k=knopf(g+': '+euro(preise[i]),{});k.addEventListener('click',function(){hinzufuegen(li,g,preise[i],b);w.remove();});w.appendChild(k);});
      li.appendChild(w);w.querySelector('button').focus();return;
    }
    var st=ev.target.closest('[data-st]');
    if(st){
      var li2=st.closest('li[data-k]'),k=st.dataset.k,g=st.dataset.g;
      if(st.dataset.st==='plus'){var pr=li2.dataset.p.split('|').map(Number),gs=li2.dataset.g?li2.dataset.g.split('|'):[''];hinzufuegen(li2,g,pr[Math.max(0,gs.indexOf(g))]);}
      else{for(var i=zettel.length-1;i>=0;i--){if(zettel[i].k===k&&zettel[i].g===g){zettel[i].q--;if(zettel[i].q<1)zettel.splice(i,1);break;}}speichern();zeichnen();}
      var neuB=li2.querySelector('.mengen [data-st="'+st.dataset.st+'"][data-g="'+g+'"]');if(neuB)neuB.focus();else{var pk=li2.querySelector('.plus');if(pk)pk.focus();}
      return;
    }
    if(!zliste.contains(ev.target))return;
    var a=ev.target.closest('[data-a]');
    if(a){var x=finde(a.dataset.u);if(!x)return;
      if(a.dataset.a==='plus')x.q++;else{x.q--;if(x.q<1){zettel.splice(zettel.indexOf(x),1);if(offen===x.u)offen=null;}}
      speichern();zeichnen();if(anzahl()===0)schliessen();return;}
    var an=ev.target.closest('[data-anpassen]');
    if(an){var y=finde(an.dataset.anpassen);if(!y)return;
      if(y.q>1){y.q--;var kopie=JSON.parse(JSON.stringify(y));kopie.q=1;kopie.u=uidZ++;zettel.splice(zettel.indexOf(y)+1,0,kopie);y=kopie;}
      offen=y.u;zeichnen();var erst=zliste.querySelector('.z-optionen .chip');if(erst)erst.focus();return;}
    var ch=ev.target.closest('[data-o]');
    if(ch){var z=finde(ch.dataset.u);if(!z)return;var o=z.o,art=ch.dataset.o,wert=ch.dataset.w;
      if(art==='va')o[art]=wert;
      else{var arr=o[art],i2=arr.indexOf(wert);if(i2>-1)arr.splice(i2,1);else if(!(art==='wahl'&&arr.length>=3))arr.push(wert);
        if(art==='ohne'&&o.ohne.indexOf(wert)>-1){o.ex=o.ex.filter(function(v){return v!==wert;});o.wahl=(o.wahl||[]).filter(function(v){return v!==wert;});}}
      speichern();zeichnen();var wieder=zliste.querySelector('[data-o="'+art+'"][data-w="'+wert+'"]');if(wieder)wieder.focus();return;}
    var fu=ev.target.closest('[data-fuell]');
    if(fu){var zf=finde(fu.dataset.u);if(!zf)return;var zielF=variante(zf.k,{f:fu.dataset.fuell});if(!zielF)return;
      wechseln(zf,zielF);speichern();zeichnen();var fw2=zliste.querySelector('[data-fuell="'+fu.dataset.fuell+'"]');if(fw2)fw2.focus();return;}
    var bb=ev.target.closest('[data-bei]');
    if(bb){var zb2=finde(bb.dataset.u);if(!zb2||!VAR[zb2.k]||VAR[zb2.k].bei===bb.dataset.bei)return;var zielB=variante(zb2.k,{bei:bb.dataset.bei});if(!zielB)return;
      wechseln(zb2,zielB);speichern();zeichnen();var bw2=zliste.querySelector('[data-bei="'+bb.dataset.bei+'"]');if(bw2)bw2.focus();return;}
    var sb=ev.target.closest('[data-super]');
    if(sb){var zs=finde(sb.dataset.super);if(!zs||!VAR[zs.k])return;var zielS=variante(zs.k,{sup:VAR[zs.k].sup?0:1},true);if(!zielS)return;
      wechseln(zs,zielS);speichern();zeichnen();var sw2=zliste.querySelector('[data-super]');if(sw2)sw2.focus();return;}
    var kb=ev.target.closest('[data-kaese]');
    if(kb){var zk=finde(kb.dataset.kaese);if(!zk)return;var zielK=kaesePartner(zk.k);if(!zielK)return;
      wechseln(zk,zielK);speichern();zeichnen();var kw2=zliste.querySelector('[data-kaese]');if(kw2)kw2.focus();return;}
    var f=ev.target.closest('[data-fertig]');
    if(f){offen=null;zusammenfassen();speichern();zeichnen();return;}
  });
  zliste.addEventListener('input',function(ev){var x=finde(ev.target.dataset.u);if(x){x.notiz=ev.target.value;speichern();}});
  zliste.addEventListener('change',function(ev){if(ev.target.classList.contains('z-notiz')){zusammenfassen();speichern();}});
  function oeffnen(){zuletzt=document.activeElement;zmeld.hidden=true;huelle.hidden=false;document.documentElement.style.overflow='hidden';document.getElementById('zettel-titel').focus();}
  function schliessen(){offen=null;zusammenfassen();speichern();zeichnen();huelle.hidden=true;document.documentElement.style.overflow='';if(zuletzt&&zuletzt.focus&&!zl.hidden)zuletzt.focus();}
  zl.addEventListener('click',oeffnen);
  huelle.addEventListener('click',function(ev){if(ev.target.closest('[data-zu]'))schliessen();});
  document.addEventListener('keydown',function(ev){
    if(huelle.hidden)return;
    if(ev.key==='Escape'){schliessen();return;}
    if(ev.key!=='Tab')return;
    /* Tastatur bleibt im offenen Bestellzettel (Dialog) */
    var f=[].filter.call(huelle.querySelectorAll('.zettel a[href],.zettel button,.zettel input,.zettel select,.zettel [tabindex]'),function(x){return !x.disabled&&x.offsetParent!==null;});
    if(!f.length)return;var erst=f[0],letzt=f[f.length-1];
    if(ev.shiftKey&&(document.activeElement===erst||!huelle.contains(document.activeElement))){ev.preventDefault();letzt.focus();}
    else if(!ev.shiftKey&&(document.activeElement===letzt||!huelle.contains(document.activeElement))){ev.preventDefault();erst.focus();}
  });
  /* Abholung: Laden, Uhrzeit, Name */
  var AK='saray-abholung',abh={laden:'',tag:'',zeit:'',name:''},VORBESTELL_TAGE=14;
  try{abh=Object.assign(abh,JSON.parse(localStorage.getItem(AK)||'{}'));}catch(e){}
  /* ?laden=freital (z. B. vom QR-Aufsteller an der Theke) wählt den Laden vor */
  (function(){var m=/[?&]laden=(freital|altenberg)/.exec(location.search);if(m&&abh.laden!==m[1]){abh.laden=m[1];abh.zeit='';}})();
  function abhSpeichern(){try{localStorage.setItem(AK,JSON.stringify(abh));}catch(e){}}
  var selTag=document.getElementById('abhol-tag'),selZeit=document.getElementById('abhol-zeit'),eName=document.getElementById('abhol-name'),hinweisZ=document.getElementById('abhol-hinweis');
  function zeitText(m,en){var h=Math.floor(m/60),r=m%60;return h+':'+(r<10?'0':'')+r+(en?'':' Uhr');}
  /* Datum eines Tages ab heute (deutsche Zeit): ISO-Schlüssel und Anzeige */
  function tagDatum(off,opt,loc){return new Intl.DateTimeFormat(loc||'de-DE',Object.assign({timeZone:'Europe/Berlin'},opt)).format(new Date(Date.now()+off*864e5));}
  function tagKurz(off,en){return tagDatum(off,{weekday:'short',day:'numeric',month:en?'short':'2-digit'},LOC[SP]||'en-GB');}
  function tagLang(off){var t=tagDatum(off,{weekday:'long',day:'2-digit',month:'2-digit'});return /\.$/.test(t)?t:t+'.';}   /* „Freitag, 24.10.“ */
  /* mögliche Abholzeiten eines Tages (Minuten), 15-Minuten-Raster, heute frühestens in 20 Minuten */
  function slots(off){
    var n=jetzt(),h=tagZeit(abh.laden,off),res=[];if(!h)return res;
    var start=h[0]+15;if(off===0)start=Math.max(start,Math.ceil((n.min+20+warte(abh.laden))/15)*15);
    for(var m=start;m<=h[1]-15;m+=15)res.push(m);
    return res;
  }
  /* Zug ab Altenberg: Abfahrten (Minuten) an einem Tag (ISO-Datum) */
  var ZUG={"laden": "altenberg", "gueltig_bis": "2026-12-12", "puffer": 15, "taeglich": ["06:18", "08:18", "10:18", "12:18", "18:18", "20:18"], "werktags": ["04:18", "05:18", "07:18", "09:18", "11:18", "13:18", "14:18", "15:18", "16:18", "17:18", "19:18", "21:18"], "werktags_nicht": ["2025-12-25", "2025-12-26", "2026-01-01", "2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25", "2026-11-18"], "extra": [{"zeit": "15:18", "wochenende": [["2025-12-14", "2026-02-22"], ["2026-11-07", "2026-12-12"]], "auch": ["2025-12-25", "2025-12-26", "2026-01-01", "2026-11-18"]}, {"zeit": "17:18", "wochenende": [["2026-02-28", "2026-11-01"]], "auch": ["2026-04-03", "2026-04-06", "2026-05-01", "2026-05-14", "2026-05-25"]}]};
  function zuege(iso){
    if(!ZUG||iso>ZUG.gueltig_bis)return [];
    var wt=new Date(iso+'T12:00:00Z').getUTCDay(),fei=ZUG.werktags_nicht.indexOf(iso)>-1,z=ZUG.taeglich.slice();
    if(wt>=1&&wt<=5&&!fei)z=z.concat(ZUG.werktags);
    ZUG.extra.forEach(function(x){var we=(wt===0||wt===6)&&x.wochenende.some(function(r){return iso>=r[0]&&iso<=r[1];});
      if(we||x.auch.indexOf(iso)>-1)z.push(x.zeit);});
    return z.map(minAus).sort(function(a,b){return a-b;}).filter(function(m,i,l){return l.indexOf(m)===i;});
  }
  var zugBox=document.getElementById('zug-wahl');
  function zugZeigen(off,sl){
    if(!zugBox)return;zugBox.textContent='';
    var vor=off===0?'heute':off===1?'morgen, '+tagLang(1):tagLang(off),en=SP!=='de';
    if(abh.laden!==ZUG.laden){zugBox.hidden=true;return;}
    var paare=[];zuege(isoTag(off)).forEach(function(d){var s=sl.filter(function(m){return m<=d-ZUG.puffer&&m>=d-45;});if(s.length)paare.push([d,s[s.length-1]]);});
    paare=paare.slice(0,6);zugBox.hidden=!paare.length;if(!paare.length)return;
    zugBox.appendChild(el('p','zug-titel',L('🚆 Mit dem Zug zurück? Abholung passend zur Abfahrt:','🚆 Taking the train? Pickup matched to your departure:')));
    var reihe=el('div','zug-chips');
    paare.forEach(function(p){var v=vor+', '+zeitText(p[1]),dz=zeitText(p[0],true),az=zeitText(p[1],true);
      var b=el('button','chip',L('Zug '+dz+' → abholen '+az,'Train '+dz+' → pickup '+az));b.type='button';
      b.setAttribute('aria-pressed',String(abh.zug===dz&&abh.zeit===v));
      b.addEventListener('click',function(){abh.zeit=v;abh.zug=dz;selZeit.value=v;abhSpeichern();zugZeigen(off,sl);zeichnen();waAktualisieren();});
      reihe.appendChild(b);});
    zugBox.appendChild(reihe);
    zugBox.appendChild(el('p','zug-quelle',L('Fahrplan ohne Gewähr, Richtung Heidenau/Dresden.','Timetable without guarantee, towards Heidenau/Dresden.')));
  }
  /* Wintersaison Altenberg: Kasten oben; automatisch nach Datum oder per Chef-App an/aus */
  var WINTER={"modus": "auto", "von": "12-01", "bis": "03-15"};
  function winterAktiv(){if(WINTER.modus==='an')return true;if(WINTER.modus==='aus')return false;var md=isoTag(0).slice(5);
    return WINTER.von<=WINTER.bis?(md>=WINTER.von&&md<=WINTER.bis):(md>=WINTER.von||md<=WINTER.bis);}
  setTimeout(function(){var w=document.getElementById('winter');if(!w)return;try{w.hidden=!winterAktiv();}catch(e){}
    var b=document.getElementById('winter-bestellen');if(b)b.addEventListener('click',function(){abh.laden='altenberg';abhSpeichern();ladenZeigen();oeffnen();});
    var g=document.getElementById('winter-gruppe');if(g)g.addEventListener('click',function(){abh.laden='altenberg';abhSpeichern();var s=document.querySelector('[data-sammel-start]');if(s)s.click();});},0);
  function zeitenFuellen(){
    selZeit.textContent='';selTag.textContent='';hinweisZ.hidden=true;ZINFO={};
    if(!abh.laden){[selTag,selZeit].forEach(function(s){var o=el('option',null,L('Bitte zuerst den Laden wählen','Please choose the shop first'));o.value='';s.appendChild(o);s.disabled=true;});return;}
    selTag.disabled=selZeit.disabled=false;
    var n=jetzt(),en=SP!=='de',tage=[];
    for(var i=0;i<=VORBESTELL_TAGE;i++){if(slots(i).length)tage.push(i);}
    tage.forEach(function(off){
      var t=off===0?L('Heute','Today'):off===1?L('Morgen, ','Tomorrow, ')+tagKurz(1,en):tagKurz(off,en);
      var o=el('option',null,t);o.value=tagDatum(off,{year:'numeric',month:'2-digit',day:'2-digit'},'en-CA');o.dataset.off=off;selTag.appendChild(o);
    });
    if(!tage.length)return;
    if(![].some.call(selTag.options,function(o){return o.value===abh.tag;}))abh.tag=selTag.options[0].value;
    selTag.value=abh.tag;
    var off=+selTag.selectedOptions[0].dataset.off,optionen=[];
    if(tage[0]>0){hinweisZ.textContent=L('Heute ist keine Abholung mehr möglich. Sie können vorbestellen.','Pickup is no longer possible today. You can pre-order.');hinweisZ.hidden=false;}
    /* Wert = Text für die Nachricht an den Laden (immer deutsch) */
    var vor=off===0?'heute':off===1?'morgen, '+tagLang(1):tagLang(off);
    var wz=warte(abh.laden),h0=tagZeit(abh.laden,0);
    var hz=tagZeit(abh.laden,0);
    var sl0=slots(0);
    if(off===0&&hz&&sl0.length&&n.min>=hz[1]-60){var lz=sl0[sl0.length-1];hinweisZ.textContent=L('Bald Feierabend: letzte Abholung heute um '+zeitText(lz)+'.','Closing soon: last pickup today at '+zeitText(lz,true)+'.');hinweisZ.hidden=false;}
    if(off===0&&wz){hinweisZ.textContent=L('Gerade viel los: Abholung frühestens in ca. '+(wz+20)+' Minuten.','Busy right now: earliest pickup in about '+(wz+20)+' minutes.');hinweisZ.hidden=false;}
    if(off===0&&h0&&n.min>=h0[0]){
      optionen.push({v:'heute, so schnell wie möglich',t:L('So schnell wie möglich','As soon as possible')});ZINFO['heute, so schnell wie möglich']={off:0,min:n.min+20+wz};}
    slots(off).forEach(function(m){var v=vor+', '+zeitText(m);optionen.push({v:v,t:zeitText(m,en)});ZINFO[v]={off:off,min:m};});
    optionen.forEach(function(x){var o=el('option',null,x.t);o.value=x.v;selZeit.appendChild(o);});
    if(optionen.some(function(x){return x.v===abh.zeit;}))selZeit.value=abh.zeit;else abh.zeit=selZeit.value;
    if(abh.zug&&!ZINFO[abh.zeit])abh.zug='';
    zugZeigen(off,slots(off));
    abhSpeichern();zeichnenSpaeter();
  }
  var zsp=false;function zeichnenSpaeter(){if(zsp)return;zsp=true;setTimeout(function(){zsp=false;zeichnen();waAktualisieren();},0);}
  var WA={"freital": "4915733729521", "altenberg": "491601836249"},waKnopf=document.getElementById('zettel-whatsapp'),waHinweis=document.getElementById('wa-hinweis');
  var verfHinweis=document.getElementById('verf-hinweis');
  function konflikte(){return zettel.filter(function(x){return sperreZettel(x.k);}).length;}
  function waAktualisieren(){
    var nr=abh.laden&&WA[abh.laden],kf=konflikte();
    verfHinweis.hidden=!kf;document.getElementById('zettel-kopieren').disabled=!!kf;
    verfHinweis.textContent=kf===1?L('Ein Gericht ist zur gewählten Zeit nicht zu haben. Bitte oben ändern.','One dish is not available at the chosen time. Please change it above.')
      :L(kf+' Gerichte sind zur gewählten Zeit nicht zu haben. Bitte oben ändern.',kf+' dishes are not available at the chosen time. Please change them above.');
    var pzz=abh.laden&&pause(abh.laden),heuteZ=ZINFO[abh.zeit]&&ZINFO[abh.zeit].off===0,ph=document.getElementById('pause-hinweis');
    if(ph){ph.hidden=!(pzz&&heuteZ);if(pzz&&heuteZ)ph.textContent=L('Gerade sehr viel los: Online-Bestellungen für heute sind bis '+uhr(pzz)+' pausiert. Bitte anrufen oder für einen anderen Tag vorbestellen.','Very busy right now: online orders for today are paused until '+zeitText(pzz,true)+'. Please call or pre-order for another day.');}
    if(pzz&&heuteZ)nr=null;
    if(kf||sammel)nr=null;
    waKnopf.hidden=!nr;waHinweis.hidden=!!nr||!!kf||!Object.keys(WA).length;
    if(nr)waKnopf.href='https://wa.me/'+nr+'?text='+encodeURIComponent(zettelText(true));
  }
  function ladenZeigen(){
    document.querySelectorAll('[data-laden]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.laden===abh.laden));});
    document.querySelectorAll('[data-anruf]').forEach(function(a){a.hidden=!!abh.laden&&a.dataset.anruf!==abh.laden;});
    zeitenFuellen();waAktualisieren();
  }
  document.querySelectorAll('[data-laden]').forEach(function(b){b.addEventListener('click',function(){abh.laden=b.dataset.laden;abhSpeichern();ladenZeigen();verfZeigen();});});
  selZeit.addEventListener('change',function(){abh.zeit=selZeit.value;abh.zug='';try{zeitenFuellen();}catch(e){}abhSpeichern();zeichnen();waAktualisieren();});
  selTag.addEventListener('change',function(){abh.tag=selTag.value;abh.zeit='';abhSpeichern();zeitenFuellen();waAktualisieren();});
  eName.value=abh.name||'';eName.addEventListener('input',function(){abh.name=eName.value;abhSpeichern();waAktualisieren();});
  ladenZeigen();
  zl.addEventListener('click',function(){zeitenFuellen();waAktualisieren();});
  var TEL={"freital": ["0351 27676660", "+4935127676660"], "altenberg": ["035056 23674", "+493505623674"]},waGesendet=document.getElementById('wa-gesendet');
  waKnopf.addEventListener('click',function(){waAktualisieren();letzteMerken();
    try{var bw=JSON.parse(localStorage.getItem('saray-bewertung')||'null');if(!bw||!bw.fertig)localStorage.setItem('saray-bewertung',JSON.stringify({l:abh.laden,t:Date.now(),nr:BNR}));}catch(e){}
    if(waKnopf.hidden)return;var tl=TEL[abh.laden];waGesendet.textContent='';bnrGesendet=true;
    var nrP=el('p','wa-nr');nrP.appendChild(document.createTextNode(L('Ihre Bestellnummer: ','Your order number: ')));nrP.appendChild(el('b',null,BNR));waGesendet.appendChild(nrP);
    waGesendet.appendChild(document.createTextNode(L('Gesendet? Der Laden bestätigt Ihre Bestellung per WhatsApp. Ohne Antwort bitte anrufen: ','Sent? The shop confirms your order via WhatsApp. No reply? Please call: ')));
    var a=el('a',null,tl[0]);a.href='tel:'+tl[1];waGesendet.appendChild(a);
    var zi=ZINFO[abh.zeit];
    if(zi){var kb=knopf(L('📅 Abholung in den Kalender','📅 Add pickup to calendar'),{'class':'knopf knopf-linie wa-kalender','id':'wa-kalender'});
      var ics=icsText(zi,BNR);kb.addEventListener('click',function(){icsLaden(ics,'saray-abholung-'+BNR+'.ics');});waGesendet.appendChild(kb);}
    waGesendet.hidden=false;});
  /* Kalendereintrag (.ics) für die Abholung, mit Erinnerung 15 Minuten vorher */
  var ADR={"freital": "Saray Döner, Dresdner Str. 87, 01705 Freital", "altenberg": "Saray Döner, Dresdner Str. 23, 01773 Altenberg"};
  function icsText(zi,nr){
    var d=tagDatum(zi.off,{year:'numeric',month:'2-digit',day:'2-digit'},'en-CA').replace(/-/g,''),
        z=function(m){return ('0'+Math.floor(m/60)).slice(-2)+('0'+m%60).slice(-2)+'00';},
        esc=function(t){return String(t).replace(/[\\;,]/g,function(c){return '\\'+c;}).replace(/\n/g,'\\n');},
        jetztZ=new Date().toISOString().replace(/[-:]/g,'').replace(/\.\d+/,'');
    return ['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Saray Doener//Bestellung//DE','BEGIN:VEVENT',
      'UID:'+nr+'-'+d+'-'+zi.min+'@saray-doener','DTSTAMP:'+jetztZ,
      'DTSTART;TZID=Europe/Berlin:'+d+'T'+z(zi.min),'DTEND;TZID=Europe/Berlin:'+d+'T'+z(zi.min+15),
      'SUMMARY:'+esc('Saray Döner abholen ('+nr+')'),'LOCATION:'+esc(ADR[abh.laden]||''),
      'DESCRIPTION:'+esc(zettel.map(function(x){return x.q+'× '+x.n;}).join('\n')+'\nSumme: '+euro(summe())+' (nur Barzahlung)'),
      'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+esc('Saray Döner abholen'),'TRIGGER:-PT15M','END:VALARM',
      'END:VEVENT','END:VCALENDAR'].join('\r\n');
  }
  function icsLaden(text,name){
    var url=URL.createObjectURL(new Blob([text],{type:'text/calendar;charset=utf-8'})),a=document.createElement('a');
    a.href=url;a.download=name;document.body.appendChild(a);a.click();a.remove();setTimeout(function(){URL.revokeObjectURL(url);},4000);
  }
  /* „Wie letztes Mal“: Zettel merken, sobald er abgeschickt, kopiert oder vorgelesen wird */
  /* Die letzten fünf Bestellungen (nur auf diesem Gerät); die neueste oben mit großem Knopf */
  var LK='saray-letzte',LLK='saray-letzte-liste',letzteListe=[],letzte=null,boxL=document.getElementById('letzte');
  try{letzteListe=JSON.parse(localStorage.getItem(LLK)||'[]');if(!Array.isArray(letzteListe))letzteListe=[];}catch(e){letzteListe=[];}
  if(!letzteListe.length){try{var alt1=JSON.parse(localStorage.getItem(LK)||'null');if(alt1&&Array.isArray(alt1.p))letzteListe=[alt1];}catch(e){}}
  letzte=letzteListe[0]||null;
  function letzteMerken(){
    if(!zettel.length)return;
    var neu={am:Date.now(),l:abh.laden||'',p:zettel.map(function(x){return {k:x.k,g:x.g,q:x.q,o:x.o,notiz:x.notiz||''};})},sg=JSON.stringify(neu.p);
    letzteListe=[neu].concat(letzteListe.filter(function(b2){return JSON.stringify(b2.p)!==sg;})).slice(0,5);letzte=neu;
    try{localStorage.setItem(LLK,JSON.stringify(letzteListe));localStorage.setItem(LK,JSON.stringify(neu));}catch(e){}
  }
  function gueltig(b2){
    if(!b2||!Array.isArray(b2.p))return [];
    return b2.p.filter(function(p){var li=gerichtLi(p.k);if(!li)return false;var gs=li.dataset.g?li.dataset.g.split('|'):[''];return gs.indexOf(p.g||'')>-1;});
  }
  function letzteGueltig(){return gueltig(letzte);}
  function kurz(g){var zus={};g.forEach(function(p){var li=gerichtLi(p.k),nm=(SP!=='de'?nameFremd(li,li.dataset.n):li.dataset.n)+(p.g?' ('+p.g+')':'');zus[nm]=(zus[nm]||0)+p.q;});
    return Object.keys(zus).map(function(k){return zus[k]+'× '+k;}).join(' · ');}
  function uebernehmen(g){g.forEach(function(p){var x=ausDaten(p);if(x)zettel.push(x);});zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();oeffnen();}
  function letzteZeigen(){
    if(!boxL)return;
    var g=letzteGueltig(),suche=document.getElementById('suche-feld');
    boxL.hidden=!g.length||zettel.length>0||!!(suche&&suche.value.trim());
    if(boxL.hidden)return;
    document.getElementById('letzte-liste').textContent=kurz(g);
    var wb=document.getElementById('letzte-weitere');wb.textContent='';
    letzteListe.slice(1).forEach(function(b2){var g2=gueltig(b2);if(!g2.length)return;var li=el('li');
      var d=new Date(b2.am),dt=('0'+d.getDate()).slice(-2)+'.'+('0'+(d.getMonth()+1)).slice(-2)+'.';
      li.appendChild(el('span',null,dt+' – '+kurz(g2)));var k=knopf(L('Nochmal','Again'),{'class':'knopf knopf-linie klein'});
      k.addEventListener('click',function(){uebernehmen(g2);});li.appendChild(k);wb.appendChild(li);});
    document.getElementById('letzte-mehr').hidden=!wb.children.length;
  }
  /* Eintrag aus gespeicherten/geteilten Daten mit aktuellem Preis; null, wenn es das Gericht nicht mehr gibt */
  function ausDaten(p,fuer){
    var li=p&&typeof p.k==='string'&&gerichtLi(p.k);if(!li)return null;
    var gs=li.dataset.g?li.dataset.g.split('|'):[''],i=gs.indexOf(p.g||'');if(i<0)return null;
    var pr=li.dataset.p.split('|').map(Number),o=Object.assign(grund(li.dataset.t),JSON.parse(JSON.stringify(p.o||{})));
    ['s','ohne','ex','wahl'].forEach(function(a){if(!Array.isArray(o[a]))o[a]=[];o[a]=o[a].filter(function(v){return typeof v==='string';}).slice(0,12);});
    if(typeof o.va!=='string')o.va='';
    return {k:p.k,n:li.dataset.n,d:li.dataset.d,g:p.g||'',c:pr[i],q:Math.min(50,Math.max(1,+p.q||1)),t:li.dataset.t||'',v:li.dataset.v||'',o:o,
      notiz:String(p.notiz||'').slice(0,200),fuer:fuer?String(fuer).slice(0,40):(p.fuer?String(p.fuer).slice(0,40):''),u:uidZ++};
  }
  document.getElementById('letzte-knopf').addEventListener('click',function(){uebernehmen(letzteGueltig());});
  document.querySelectorAll('[data-anruf]').forEach(function(a){a.addEventListener('click',letzteMerken);});
  var codeBox=document.getElementById('code-box'),codeFeld=document.getElementById('code-feld'),codeInfo=document.getElementById('code-info');
  function codeZeigen(){if(!codeBox)return;var d=codeAktiv(),rb=rabatt();codeBox.hidden=!CODES.length;
    if(abh.code){var ganz=CODES.filter(function(x){return x.h===abh.code.h;})[0];
      var en=SP!=='de';
      codeInfo.textContent=d?(en?fuell(T('{x}: {p} % off'),{x:d.name,p:d.prozent}):d.name+': '+d.prozent+' % Rabatt')+(rb?' (−'+euro(rb)+')':'')+(d.za!=null?' · '+zeitText(d.za,true)+'–'+zeitText(d.zb,en):'')
        :ganz?(en?fuell(T('Code {x} does not apply to this pickup.'),{x:abh.code.c}):'Code '+abh.code.c+' gilt nicht für diese Abholung.')+(ganz.za!=null?' ('+zeitText(ganz.za,true)+'–'+zeitText(ganz.zb,en)+')':''):L('Code abgelaufen.','Code expired.');
      codeInfo.hidden=false;document.getElementById('code-weg').hidden=false;}else{codeInfo.hidden=true;document.getElementById('code-weg').hidden=true;}}
  function codeHash(c){return crypto.subtle.digest('SHA-256',new TextEncoder().encode('saray|'+c)).then(function(b){return [].map.call(new Uint8Array(b),function(x){return ('0'+x.toString(16)).slice(-2);}).join('');});}
  if(codeBox){
    document.getElementById('code-form').addEventListener('submit',function(ev){ev.preventDefault();var c=codeFeld.value.toUpperCase().replace(/[^A-Z0-9]/g,'');if(!c)return;
      if(!window.crypto||!crypto.subtle){codeInfo.textContent=L('Code hier nicht prüfbar.','Code cannot be checked here.');codeInfo.hidden=false;return;}
      codeHash(c).then(function(h){var d=CODES.filter(function(x){return x.h===h;})[0];
        if(!d){codeInfo.textContent=L('Diesen Code kennen wir nicht.','Unknown code.');codeInfo.hidden=false;return;}
        abh.code={h:h,c:c};codeFeld.value='';abhSpeichern();zeichnen();waAktualisieren();});});
    document.getElementById('code-weg').addEventListener('click',function(){delete abh.code;abhSpeichern();zeichnen();waAktualisieren();});}
  /* Küchenansicht: Bestellung als Link (Daten stehen im Link selbst, kein Server) */
  function b64url(t){return btoa(unescape(encodeURIComponent(t))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function kuecheLink(){
    if(!/^https?:/.test(location.protocol)||!zettel.length)return '';
    var zi=ZINFO[abh.zeit],t='';
    if(zi){var hh=Math.floor(zi.min/60),mm=zi.min%60;t=isoTag(zi.off)+'T'+(hh<10?'0':'')+hh+':'+(mm<10?'0':'')+mm;}
    var o={v:1,nr:BNR,l:abh.laden||'',z:abh.zeit||'',t:t,m:(abh.name||'').slice(0,40),s:summe(),r:rabatt(),rc:(codeAktiv()||{}).name||'',zug:abh.zug||'',sp:SP,
      test:document.body.classList.contains('vorschau')?1:0,a:Date.now(),
      p:zettel.map(function(x){var w=x.t||fehlend(x).length?wuensche(x):'';return [x.q,x.n+(x.g?' ('+x.g+')':''),w,x.fuer||'',x.notiz||'',stueck(x)*x.q];}),
      w:zettel.map(function(x){var y={k:x.k,q:x.q};if(x.g)y.g=x.g;if(x.o&&Object.keys(x.o).some(function(k){return x.o[k]&&x.o[k].length;}))y.o=x.o;if(x.notiz)y.notiz=x.notiz;return y;})};
    return new URL('kueche/#b='+b64url(JSON.stringify(o)),location.href).href;
  }
  function zettelText(mitKueche){
    var test=document.body.classList.contains('vorschau')?['*TEST – Entwurf, keine echte Bestellung*','']:[];
    var vb=ZINFO[abh.zeit]&&ZINFO[abh.zeit].off>0;
    var z=[(vb?'Vorbestellung':'Bestellung')+' Saray Döner'+(abh.laden?' '+(abh.laden==='freital'?'Freital':'Altenberg'):'')];
    z.push('Bestellnummer: '+BNR);
    if(abh.zeit)z.push('Abholung: '+abh.zeit+(abh.zug&&abh.laden===ZUG.laden?' (Zug '+abh.zug+')':''));
    if(abh.name)z.push('Name: '+abh.name);
    z.push('');
    zettel.forEach(function(x){z.push(zeileText(x));});
    var rb=rabatt(),cd=codeAktiv();if(rb&&cd)z.push('Firmen-Code: '+abh.code.c+' ('+cd.name+') – '+cd.prozent+' % Rabatt: −'+euro(rb));
    z.push('Summe: '+euro(summe()));
    var kl=mitKueche?kuecheLink():'';if(kl){z.push('');z.push('Für die Küche: '+kl);}
    return test.concat(z).join('\n');
  }
  function zeileText(x){var w=x.t||fehlend(x).length?wuensche(x):'';
    return x.q+'× '+x.n+(x.g?' ('+x.g+')':'')+(w?', '+w:'')+(x.fuer?' (für '+x.fuer+')':'')+': '+euro(stueck(x)*x.q)+(aktionZ(x)?' (Aktion)':'')+(x.notiz?'\n   Wunsch: '+x.notiz:'');}
  /* Teilen: Teilen-Menü des Handys (WhatsApp, SMS, Mail, Teams …); sonst in die Zwischenablage kopieren */
  function teilen(t,titel){
    var kopiert=L('Bestellung kopiert – jetzt in WhatsApp, SMS, E-Mail oder Teams einfügen.','Order copied – now paste it into WhatsApp, a text message, e-mail or Teams.');
    function notfall(){var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
      document.body.appendChild(ta);ta.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}ta.remove();
      melden(ok?kopiert:L('Kopieren hat nicht geklappt. Bitte die Bestellung abschreiben.','Copying did not work. Please write the order down.'));}
    function kopieren(){if(navigator.clipboard&&navigator.clipboard.writeText)navigator.clipboard.writeText(t).then(function(){melden(kopiert);},notfall);else notfall();}
    if(navigator.share&&(window.matchMedia&&matchMedia('(pointer:coarse)').matches)){
      navigator.share({title:titel||'Bestellung Saray Döner',text:t}).catch(function(e){if(!e||e.name!=='AbortError')kopieren();});
    }else kopieren();
  }
  document.getElementById('zettel-kopieren').addEventListener('click',function(){letzteMerken();teilen(zettelText());});

  /* ---------- Sammelbestellung (ohne Server) ----------
     Einladung:  …/#sammel=<daten>  -> Teilnehmer wählen und schicken „ihren Teil“ zurück
     Teil:       …/#teil=<daten>    -> Sammler fügt ihn mit Namen („für Anna“) zur eigenen Bestellung hinzu */
  function kodieren(o){return btoa(unescape(encodeURIComponent(JSON.stringify(o)))).replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');}
  function dekodieren(t){t=t.replace(/-/g,'+').replace(/_/g,'/');while(t.length%4)t+='=';return JSON.parse(decodeURIComponent(escape(atob(t))));}
  function basisUrl(){return location.origin+location.pathname;}
  var SK='saray-sammel',SIK='saray-sammel-import',sammel=null;
  try{sammel=JSON.parse(localStorage.getItem(SK)||'null');}catch(e){sammel=null;}
  function sammelSpeichern(){try{if(sammel)localStorage.setItem(SK,JSON.stringify(sammel));else localStorage.removeItem(SK);}catch(e){}}
  var sDlg=document.getElementById('sammel-dialog'),sBand=document.getElementById('sammel-band'),sTeil=document.getElementById('sammel-teil');
  function dialog(titel,inhalt,knoepfe){
    document.getElementById('sammel-titel').textContent=titel;
    var box=document.getElementById('sammel-inhalt');box.textContent='';inhalt.forEach(function(x){box.appendChild(x);});
    var r=document.getElementById('sammel-knoepfe');r.textContent='';
    knoepfe.forEach(function(k,i){var b=knopf(k[0],{'class':i?'knopf knopf-linie':'knopf knopf-dunkel'});b.addEventListener('click',k[1]);r.appendChild(b);});
    sDlg.hidden=false;dlgAnpassen();
    /* Handy: Tastatur nicht sofort öffnen – erst wenn man ins Feld tippt */
    var beruehrung=window.matchMedia&&matchMedia('(pointer:coarse)').matches;
    var f=beruehrung?sDlg.querySelector('.sammel-box'):sDlg.querySelector('input,button');if(f)f.focus({preventScroll:true});
  }
  function dialogZu(){sDlg.hidden=true;if(huelle.hidden)document.documentElement.style.overflow='';}
  /* Fenster steht auf dem Handy oben (CSS) – kein Nachschieben beim Tippen; Seite dahinter festhalten */
  function dlgAnpassen(){document.documentElement.style.overflow='hidden';}
  sDlg.addEventListener('click',function(ev){if(ev.target===sDlg)dialogZu();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!sDlg.hidden)dialogZu();});
  function nameFeld(){var f=document.createElement('input');f.type='text';f.id='sammel-name';f.autocomplete='given-name';f.maxLength=40;f.value=abh.name||'';
    var lb=el('label',null,L('Ihr Name','Your name'));lb.htmlFor='sammel-name';return [lb,f];}
  function einladen(){
    var nf=nameFeld(),fehler=el('p','abhol-hinweis');fehler.hidden=true;
    dialog(L('Gemeinsam bestellen','Order as a group'),[el('p',null,L('Sie laden andere ein. Jeder sucht sich sein Essen aus und schickt Ihnen seinen Teil zurück. Sie bestellen dann alles zusammen.','You invite others. Everyone picks their food and sends their part back to you. You then order everything together.'))].concat(nf,[fehler]),
      [[L('Einladung teilen','Share invitation'),function(){var name=nf[1].value.trim();
          if(!name){fehler.textContent=L('Bitte Ihren Namen eintragen.','Please enter your name.');fehler.hidden=false;nf[1].focus();return;}
          abh.name=name;eName.value=name;abhSpeichern();dialogZu();
          var link=basisUrl()+'#sammel='+kodieren({an:name,l:abh.laden||''});
          teilen('Ich bestelle bei Saray Döner für mehrere. Such dir dein Essen aus und schick mir deinen Teil zurück:\n'+link,'Sammelbestellung Saray Döner');}],
       [L('Abbrechen','Cancel'),dialogZu]]);
  }
  document.querySelectorAll('[data-sammel-start]').forEach(function(b){b.addEventListener('click',einladen);});
  /* Fester Döner-Tag: wöchentliche Erinnerung (.ics) mit Link, der „Gemeinsam bestellen“ öffnet */
  function doenerTag(){
    var WT=[[1,'MO'],[2,'TU'],[3,'WE'],[4,'TH'],[5,'FR']],tag=5,zeit='11:00',wb=el('div','wahl-chips'),zb=el('div','wahl-chips');
    function z(){wb.textContent='';zb.textContent='';
      WT.forEach(function(w2){var b=knopf(SP==='de'?TAGE[w2[0]]:new Intl.DateTimeFormat(LOC[SP],{weekday:'long',timeZone:'UTC'}).format(new Date(Date.UTC(2026,0,4+w2[0]))),{'class':'chip','aria-pressed':String(tag===w2[0]),'data-tag':w2[0]});
        b.addEventListener('click',function(){tag=w2[0];z();});wb.appendChild(b);});
      ['10:30','11:00','11:30','17:00'].forEach(function(t){var b=knopf(t+(SP==='de'?' Uhr':''),{'class':'chip','aria-pressed':String(zeit===t),'data-zeit':t});b.addEventListener('click',function(){zeit=t;z();});zb.appendChild(b);});}
    z();
    dialog(L('Fester Döner-Tag','Weekly döner day'),[el('p',null,L('Eine Erinnerung jede Woche in Ihrem Kalender – mit Link, der die Sammelbestellung startet.','A weekly reminder in your calendar – with a link that starts the group order.')),
      el('p','z-gruppe-titel',L('Welcher Tag?','Which day?')),wb,el('p','z-gruppe-titel',L('Wann erinnern?','Remind at')),zb],
      [[L('📅 In den Kalender','📅 Add to calendar'),function(){
        var d=new Date(),diff=(tag-d.getDay()+7)%7,st=new Date(d.getFullYear(),d.getMonth(),d.getDate()+diff),hh=zeit.slice(0,2),mm=zeit.slice(3);
        var ds=st.getFullYear()+('0'+(st.getMonth()+1)).slice(-2)+('0'+st.getDate()).slice(-2),link=basisUrl()+'#gemeinsam';
        var ende=('0'+((+hh)+((+mm)+15>=60?1:0))).slice(-2)+('0'+(((+mm)+15)%60)).slice(-2);
        var esc=function(t){return String(t).replace(/[\\;,]/g,function(c){return '\\'+c;}).replace(/\n/g,'\\n');};
        var ics=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Saray Doener//Doener-Tag//DE','BEGIN:VEVENT','UID:doenertag-'+Date.now()+'@saray','DTSTAMP:'+new Date().toISOString().replace(/[-:]/g,'').slice(0,15)+'Z',
          'DTSTART:'+ds+'T'+hh+mm+'00','DTEND:'+ds+'T'+ende+'00','RRULE:FREQ=WEEKLY;BYDAY='+WT.filter(function(w2){return w2[0]===tag;})[0][1],
          'SUMMARY:'+esc(L('Döner-Tag: Bestellung bei Saray sammeln','Döner day: collect the order at Saray')),'URL:'+link,
          'DESCRIPTION:'+esc(L('Gemeinsam bestellen: ','Order as a group: ')+link),'BEGIN:VALARM','ACTION:DISPLAY','DESCRIPTION:'+esc(L('Döner-Tag','Döner day')),'TRIGGER:PT0M','END:VALARM','END:VEVENT','END:VCALENDAR'].join('\r\n');
        icsLaden(ics,'saray-doener-tag.ics');dialogZu();melden(L('Erinnerung gespeichert – im Kalender öffnen.','Reminder saved – open it in your calendar.'));}],
       [L('Abbrechen','Cancel'),dialogZu]]);
  }
  document.querySelectorAll('[data-doenertag]').forEach(function(b){b.addEventListener('click',doenerTag);});
  function teilSchicken(){
    var name=(eName.value||'').trim();
    if(!name){eName.focus();melden(L('Bitte zuerst Ihren Namen eintragen.','Please enter your name first.'));return;}
    if(!zettel.length)return;
    var link=basisUrl()+'#teil='+kodieren({von:name,p:zettel.map(function(x){return {k:x.k,g:x.g,q:x.q,o:x.o,notiz:x.notiz||''};})});
    var z=['Mein Teil für die Sammelbestellung bei Saray Döner ('+name+'):'];zettel.forEach(function(x){z.push(zeileText(x));});
    z.push('Summe: '+euro(summe()),'','Zum Hinzufügen öffnen:',link);
    teilen(z.join('\n'),'Mein Teil – Saray Döner');
  }
  sTeil.addEventListener('click',teilSchicken);
  function sammelZeigen(){
    sBand.hidden=!sammel;
    document.querySelectorAll('.sammel-start').forEach(function(x){x.hidden=!!sammel;});
    if(sammel)document.getElementById('sammel-band-text').textContent=L('👥 Sammelbestellung für ','👥 Group order for ')+sammel.an+
      L(': Essen mit „+“ wählen, dann in „Meine Bestellung“ Ihren Teil zurückschicken.',': pick your food with “+”, then send your part back from “My order”.');
    sTeil.hidden=!sammel||!zettel.length;
    if(sammel){var sp=sTeil.querySelector('span')||sTeil;sp.textContent=L('Meinen Teil an ','Send my part to ')+sammel.an+L(' schicken','');}
    document.getElementById('sammel-einladen').hidden=!!sammel;
    document.getElementById('zettel').classList.toggle('im-sammel',!!sammel);
  }
  document.getElementById('sammel-ende').addEventListener('click',function(){sammel=null;sammelSpeichern();sammelZeigen();waAktualisieren();});
  document.getElementById('sammel-einladen').addEventListener('click',einladen);
  function linkPruefen(){
    if(location.hash==='#gemeinsam'){history.replaceState(null,'',location.pathname+location.search);if(!sammel)einladen();return;}
    var m=/^#(sammel|teil|nochmal)=([A-Za-z0-9_-]+)/.exec(location.hash);if(!m)return;
    history.replaceState(null,'',location.pathname+location.search);
    var d;try{d=dekodieren(m[2]);}catch(e){melden(L('Der Link ist unvollständig. Bitte noch einmal schicken lassen.','The link is incomplete. Please ask for it again.'));return;}
    if(m[1]==='nochmal'){
      var nm=(d&&Array.isArray(d.p)?d.p:[]).slice(0,60).map(function(p){return ausDaten(p);}).filter(Boolean);
      if(!nm.length){dialog(L('Nochmal bestellen','Order again'),[el('p',null,L('Die Gerichte gibt es so nicht mehr auf der Karte.','These dishes are no longer on the menu.'))],[[L('OK','OK'),dialogZu]]);return;}
      if(d.l&&ZEITEN[d.l]){abh.laden=d.l;abhSpeichern();ladenZeigen();}
      var ul=el('ul','sammel-liste');nm.forEach(function(x){ul.appendChild(el('li',null,x.q+'× '+nameA(x)+(x.g?' ('+x.g+')':'')+': '+euro(stueck(x)*x.q)));});
      dialog(L('Nochmal bestellen','Order again'),[ul,el('p','sammel-summe',L('Summe: ','Total: ')+euro(nm.reduce(function(a,x){return a+x.q*stueck(x);},0)))],
        [[L('In meine Bestellung','Add to my order'),function(){nm.forEach(function(x){zettel.push(x);});zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();dialogZu();oeffnen();}],
         [L('Abbrechen','Cancel'),dialogZu]]);
      return;}
    if(m[1]==='sammel'){
      if(!d||!d.an)return;
      sammel={an:String(d.an).slice(0,40)};sammelSpeichern();
      if(d.l&&ZEITEN[d.l]&&!abh.laden){abh.laden=d.l;abhSpeichern();ladenZeigen();}
      sammelZeigen();waAktualisieren();
      dialog(L('Sammelbestellung von ','Group order from ')+sammel.an,[el('p',null,L(sammel.an+' sammelt die Bestellung. Wählen Sie Ihr Essen mit „+“, öffnen Sie „Meine Bestellung“ und tippen Sie auf „Meinen Teil an '+sammel.an+' schicken“.',
        sammel.an+' is collecting the order. Pick your food with “+”, open “My order” and tap “Send my part to '+sammel.an+'”.'))],[[L('Los geht’s','Let’s go'),dialogZu]]);
      return;
    }
    var von=String(d&&d.von||'?').slice(0,40),teile=(d&&Array.isArray(d.p)?d.p:[]).slice(0,60).map(function(p){return ausDaten(p,von);}).filter(Boolean);
    var schon=[];try{schon=JSON.parse(localStorage.getItem(SIK)||'[]');}catch(e){}
    var ist=schon.indexOf(m[2].slice(0,80))>-1,summeT=teile.reduce(function(a,x){return a+x.q*stueck(x);},0);
    var liste=el('ul','sammel-liste');teile.forEach(function(x){liste.appendChild(el('li',null,x.q+'× '+nameA(x)+(x.g?' ('+x.g+')':'')+': '+euro(stueck(x)*x.q)));});
    var inhalt=[liste,el('p','sammel-summe',L('Summe: ','Total: ')+euro(summeT))];
    if(ist)inhalt.push(el('p','abhol-hinweis',L('Diesen Teil haben Sie schon hinzugefügt.','You have already added this part.')));
    if(!teile.length){dialog(L('Teil von ','Part from ')+von,[el('p',null,L('Der Teil enthält keine Gerichte aus der aktuellen Karte.','This part contains no dishes from the current menu.'))],[[L('OK','OK'),dialogZu]]);return;}
    dialog(von+L(' schickt den eigenen Teil',' sent their part'),inhalt,[[L('Zur Bestellung hinzufügen','Add to my order'),function(){
        teile.forEach(function(x){zettel.push(x);});zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();
        schon.push(m[2].slice(0,80));try{localStorage.setItem(SIK,JSON.stringify(schon.slice(-50)));}catch(e){}
        dialogZu();oeffnen();melden(L('Teil von ','Part from ')+von+L(' hinzugefügt.',' added.'));}],
      [L('Verwerfen','Discard'),dialogZu]]);
  }
  var leeren=document.getElementById('zettel-leeren'),leerenTimer=null;
  leeren.addEventListener('click',function(){
    if(leeren.dataset.sicher){zettel=[];offen=null;speichern();zeichnen();schliessen();melden(L('Bestellung geleert.','Order cleared.'));delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');return;}
    leeren.dataset.sicher='1';leeren.textContent=L('Wirklich alles löschen? Nochmal tippen.','Really delete everything? Tap again.');
    clearTimeout(leerenTimer);leerenTimer=setTimeout(function(){delete leeren.dataset.sicher;leeren.textContent=L('Bestellung leeren','Clear order');},4000);
  });
  zeichnen();verfZeigen();regelnLaden();sammelZeigen();linkPruefen();
  window.addEventListener('hashchange',linkPruefen);
  setInterval(function(){try{verfZeigen();zeitenFuellen();}catch(e){}},60000);

  if(feld){
    feld.addEventListener('input',suchen);
    nichts.querySelector('button').addEventListener('click',function(){feld.value='';suchen();feld.focus();});
  }

  /* „Nach oben“-Knopf: erscheint, wenn man etwa eine Bildschirmhöhe gescrollt hat */
  var obenK=document.getElementById('nach-oben'),obenGeplant=false;
  function obenPruefen(){obenK.hidden=window.scrollY<window.innerHeight*0.9;}
  window.addEventListener('scroll',function(){if(obenGeplant)return;obenGeplant=true;requestAnimationFrame(function(){obenGeplant=false;obenPruefen();});},{passive:true});
  obenK.addEventListener('click',function(){
    window.scrollTo({top:0,behavior:weniger?'auto':'smooth'});
    var ziel=document.querySelector('#oben a');if(ziel)ziel.focus({preventScroll:true});
  });
  obenPruefen();

  /* Hinweis-Band nach deutschem Datum */
  function hinweiseZeigen(){
    var d=new Intl.DateTimeFormat('en-CA',{timeZone:'Europe/Berlin',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    document.querySelectorAll('.hinweis-band').forEach(function(b){b.hidden=!(d>=b.dataset.von&&d<=b.dataset.bis);});
  }
  try{hinweiseZeigen();}catch(e){}

  /* Sprachumschalter Deutsch/Englisch */
  var spKnopf=document.getElementById('sprache'),spMenue=document.getElementById('sprachen-menu');
  function textFuer(l,de,en){return l==='de'?de:(l==='en'?en:T(en));}
  function sprache(l,merken){
    if(l!=='de'&&l!=='en'&&!DICT[l]){ /* Wörterbuch erst laden, dann umschalten */
      fetch('lang/'+l+'.json').then(function(r){return r.ok?r.json():{};}).then(function(d){DICT[l]=d||{};sprache(l,merken);},function(){DICT[l]={};sprache(l,merken);});return;}
    SP=l;document.documentElement.lang=l;document.documentElement.dir=l==='ar'?'rtl':'ltr';
    document.querySelectorAll('[data-en]').forEach(function(x){if(x._de==null)x._de=x.textContent;x.textContent=textFuer(l,x._de,x.dataset.en);});
    document.querySelectorAll('[data-en-html]').forEach(function(x){if(x._de==null)x._de=x.innerHTML;x.innerHTML=textFuer(l,x._de,x.dataset.enHtml);});
    document.querySelectorAll('[data-en-ph]').forEach(function(x){if(x._de==null)x._de=x.placeholder;x.placeholder=textFuer(l,x._de,x.dataset.enPh);});
    document.querySelectorAll('[data-en-aria]').forEach(function(x){if(x._dea==null)x._dea=x.getAttribute('aria-label');
      var en=x.dataset.enAria,m=/^Add (.+) to my order$/.exec(en),v=m&&l!=='de'&&l!=='en'?fuell(T('Add {x} to my order'),{x:T(m[1])}):textFuer(l,x._dea,en);x.setAttribute('aria-label',v);});
    document.querySelectorAll('[data-en-title]').forEach(function(x){if(x._det==null)x._det=x.getAttribute('title');x.setAttribute('title',textFuer(l,x._det,x.dataset.enTitle));});
    spKnopf.textContent=l.toUpperCase();
    spKnopf.setAttribute('aria-label','Sprache / Language: '+(SPRACHEN.filter(function(x){return x[0]===l;})[0]||['',''])[1]);
    spMenue.querySelectorAll('[data-sp]').forEach(function(b){b.setAttribute('aria-current',b.dataset.sp===l?'true':'false');});
    if(merken){try{localStorage.setItem(SPK,l);}catch(e){}}
    try{aktualisieren();}catch(e){}
    if(feld&&feld.value.trim())suchen();
    zeichnen();zeitenFuellen();waAktualisieren();handZeigen();try{aktionenZeigen();}catch(e){}
    try{verfZeigen();}catch(e){}
  }
  /* Sprachwahl: Knopf mit Kürzel, darunter die Liste in der jeweiligen Sprache */
  SPRACHEN.forEach(function(x){var b=document.createElement('button');b.type='button';b.dataset.sp=x[0];b.lang=x[0];b.textContent=x[1];
    if(x[0]==='ar')b.dir='rtl';b.addEventListener('click',function(){menueZu();sprache(x[0],true);spKnopf.focus();});var li=document.createElement('li');li.appendChild(b);spMenue.appendChild(li);});
  function menueZu(){spMenue.hidden=true;spKnopf.setAttribute('aria-expanded','false');}
  spKnopf.addEventListener('click',function(ev){ev.stopPropagation();var auf=spMenue.hidden;spMenue.hidden=!auf;spKnopf.setAttribute('aria-expanded',String(auf));
    if(auf){var akt=spMenue.querySelector('[aria-current="true"]')||spMenue.querySelector('button');if(akt)akt.focus();}});
  document.addEventListener('click',function(ev){if(!spMenue.hidden&&!spMenue.contains(ev.target))menueZu();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!spMenue.hidden){menueZu();spKnopf.focus();}});
  if(SP!=='de')sprache(SP,false);
  else spMenue.querySelectorAll('[data-sp]').forEach(function(b){b.setAttribute('aria-current',b.dataset.sp==='de'?'true':'false');});

  /* Impressum/Datenschutz per Link öffnen */
  function oeffne(){var d=document.getElementById(location.hash.slice(1));if(d&&d.tagName==='DETAILS')d.open=true;}
  window.addEventListener('hashchange',oeffne);oeffne();
})();
