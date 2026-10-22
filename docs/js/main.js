(function(){
  var ZEITEN={"freital": {"1": [600, 1320], "2": [600, 1320], "3": [600, 1320], "4": [600, 1320], "5": [600, 1320], "6": [660, 1320], "0": [660, 1320]}, "altenberg": {"1": [600, 1260], "2": [600, 1260], "3": [600, 1260], "4": [600, 1260], "5": [600, 1260], "6": [600, 1260], "0": [660, 1260]}},SONDER={"freital": {}, "altenberg": {}},WARTE={},AKTIONEN=[];
  var TAGE=['Sonntag','Montag','Dienstag','Mittwoch','Donnerstag','Freitag','Samstag'];
  var TAGE_E=['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'];
  /* Sprache: gespeicherte Wahl, sonst Browsersprache (Suchmaschinen bekommen immer Deutsch) */
  var SPK='saray-sprache',SP='de';
  try{SP=localStorage.getItem(SPK)||'';}catch(e){SP='';}
  if(SP!=='de'&&SP!=='en'){
    var langs=(navigator.languages&&navigator.languages.length?navigator.languages:[navigator.language||'de']);
    SP=(/bot|crawl|spider|lighthouse/i.test(navigator.userAgent)||langs.some(function(l){return /^de/i.test(l);}))?'de':'en';
  }
  function L(de,en){return SP==='en'?en:de;}
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
    var iso=isoTag(0),wt=new Date(iso+'T12:00:00Z').getUTCDay();
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
          m.textContent=L('Aktion ','Offer ')+a.p[k].map(euroK).join(' / ')+uz+(ort?L(' (nur'+ort+')',' ('+ort.trim()+' only)'):'');
          ziel.appendChild(document.createTextNode(' '));ziel.appendChild(m);
          li.querySelectorAll('.preis, .tipp-preis').forEach(function(p){p.classList.add('preis-alt');});
        });
      });
    });
  }
  function warte(ort){var w=WARTE[ort];return w&&w.datum===isoTag(0)?w.min:0;}
  function uhr(m){var h=Math.floor(m/60),r=m%60;if(SP==='en')return h+':'+(r<10?'0':'')+r;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
  function lage(ort){
    var n=jetzt(),h=tagZeit(ort,0),w=warte(ort);
    if(h&&n.min>=h[0]&&n.min<h[1])return{offen:true,text:L('Jetzt geöffnet, bis ','Open now, until ')+uhr(h[1])+(w?L(' · Wartezeit ca. '+w+' Min.',' · waiting time approx. '+w+' min'):'')};
    if(h&&n.min<h[0])return{offen:false,text:L('Geschlossen, öffnet heute um ','Closed, opens today at ')+uhr(h[0])};
    for(var i=1;i<=14;i++){var t=(n.tag+i)%7,zi=tagZeit(ort,i);if(zi)return{offen:false,text:SP==='en'?'Closed, opens '+(i===1?'tomorrow':i<7?'on '+TAGE_E[t]:'on '+TAGE_E[t]+' '+isoTag(i).slice(8)+'/'+isoTag(i).slice(5,7))+' at '+uhr(zi[0]):'Geschlossen, öffnet '+(i===1?'morgen':i<7?'am '+TAGE[t]:'am '+TAGE[t]+', '+isoTag(i).slice(8)+'.'+isoTag(i).slice(5,7)+'.')+' um '+uhr(zi[0])};}
    return{offen:false,text:''};
  }
  function aktualisieren(){
    document.querySelectorAll('[data-status]').forEach(function(el){
      var s=lage(el.getAttribute('data-status'));el.setAttribute('data-offen',s.offen?'ja':'nein');
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
    try{(new Image()).src='https://'+GC+'.goatcounter.com/count?p='+encodeURIComponent(pfad)+(ereignis?'&e=true&t='+encodeURIComponent(pfad):'&t='+encodeURIComponent(document.title)+'&r='+encodeURIComponent(document.referrer))+'&s='+screen.width+'&rnd='+Math.random().toString(36).slice(2);}catch(e){}
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
    handTippZeigen('<b>'+L('Hat’s geschmeckt?','Did you enjoy it?')+'</b><br>'+L('Über eine Google-Bewertung für Saray Döner '+ort+' freuen wir uns sehr.','We would love a Google review for Saray Döner '+ort+'.'),
      [[L('⭐ Bewerten','⭐ Review'),function(){zaehlen('bewertung-'+bw.l);window.open('https://search.google.com/local/writereview?placeid='+GOOGLE[bw.l],'_blank','noopener');handTippZu();}],
       [L('Nein danke','No thanks'),handTippZu]],25000);
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
    var k=getComputedStyle(nav).position==='sticky'&&nav.getBoundingClientRect().top-marke.getBoundingClientRect().bottom>1;
    if(k!==nav.classList.contains('klebt'))nav.classList.toggle('klebt',k);
    if(k&&glas){glas.remove();glas=null;}
    if(!k&&!glas){glas=document.createElement('div');glas.className='glas-oben';glas.setAttribute('aria-hidden','true');document.body.appendChild(glas);}
    if(k&&!deckel){deckel=document.createElement('div');deckel.className='deckel-oben';deckel.setAttribute('aria-hidden','true');document.body.appendChild(deckel);}
    if(deckel)deckel.style.height=nav.offsetHeight+'px';
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
  var vegK=document.getElementById('veg-schalter');
  if(vegK)vegK.addEventListener('click',function(){vegK.setAttribute('aria-pressed',String(vegK.getAttribute('aria-pressed')!=='true'));suchen();});
  var feld=document.getElementById('suche-feld'),gerichte=[].slice.call(document.querySelectorAll('.gericht'));
  var treffer=document.querySelector('.treffer'),nichts=document.querySelector('.nichts'),wort=nichts&&nichts.querySelector('q');
  gerichte.forEach(function(g){g._s=norm(g.getAttribute('data-s'));});
  function suchen(){
    var roh=feld.value.trim(),q=norm(roh),teile=q.split(/\s+/).filter(Boolean),n=0,veg=vegK&&vegK.getAttribute('aria-pressed')==='true';
    gerichte.forEach(function(g){var ok=teile.every(function(w){return g._s.indexOf(w)>-1;})&&(!veg||g.hasAttribute('data-veg'));g.hidden=!ok;if(ok)n++;});
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
    var bl=document.querySelector('.beliebt');if(bl)bl.hidden=teile.length>0||veg;
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
  var SPERR={"doener": {"de": "Döner", "en": "Döner", "nr": ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "30", "31", "32", "33", "34", "35", "36", "37", "38"]}, "duerum": {"de": "Dürüm", "en": "Dürüm", "nr": ["50", "51", "52", "53", "54", "55", "56", "57", "58", "40", "41", "42", "43"]}, "teller": {"de": "Box & Teller", "en": "Boxes & plates", "nr": ["13", "14", "15", "16", "21", "22", "23", "24", "25", "26", "28"]}, "pizza": {"de": "Pizza", "en": "Pizza", "nr": ["80", "81", "82", "83", "84", "85", "86", "87", "88", "89", "90", "91", "92", "93", "94", "95", "96", "97", "98", "99", "100", "101", "102", "103", "104", "105", "125"]}, "lahmacun": {"de": "Lahmacun", "en": "Lahmacun", "nr": ["120", "121", "122", "123", "124"]}, "baguette": {"de": "Baguette", "en": "Baguette", "nr": ["150", "151", "152", "153", "154", "156", "157", "158", "159", "160"]}, "salate": {"de": "Salate", "en": "Salads", "nr": ["130", "131", "132", "133", "134", "135", "136", "137", "138", "139", "140", "141", "142", "143"]}, "schnitzel": {"de": "Schnitzel & Nuggets", "en": "Schnitzel & nuggets", "nr": ["70", "71", "72", "73", "60", "61", "62", "63", "64", "65"]}, "kinder": {"de": "Für Kinder", "en": "For kids", "nr": ["17", "18", "19", "20"]}, "getraenke": {"de": "Getränke", "en": "Drinks", "nr": []}, "huhn": {"de": "Hähnchen", "en": "Chicken", "nr": ["30", "31", "32", "33", "34", "35", "36", "37", "38", "40", "41", "42", "43", "15", "16", "26", "102", "105", "134", "135", "19"]}, "nuggets": {"de": "Nuggets", "en": "Nuggets", "nr": ["60", "61", "62", "63", "64", "65", "20"]}, "falafel": {"de": "Falafel", "en": "Falafel", "nr": ["11", "12", "58", "24", "142"]}, "halloumi": {"de": "Halloumi", "en": "Halloumi", "nr": ["5", "57", "24", "26", "98", "99", "158", "141"]}, "schnitzel-fleisch": {"de": "Schnitzel", "en": "Schnitzel", "nr": ["9", "10", "159", "70"]}, "fisch": {"de": "Fisch", "en": "Fish", "nr": ["71"]}},REGELN_FEST=[],REGELN=REGELN_FEST.slice(),LADEN_N={freital:'Freital',altenberg:'Altenberg'};
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
  function uhrK(t){var m=minAus(t),h=Math.floor(m/60),r=m%60;return SP==='en'?h+':'+(r<10?'0':'')+r:(r?h+':'+(r<10?'0':'')+r:h)+' Uhr';}
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
  var W={'Knoblauch':'garlic','Kräuter':'herb','Chili':'chili','Zwiebeln':'onions','Tomaten':'tomatoes','Gurken':'cucumber','Rotkohl':'red cabbage',
    'Weißkohl':'white cabbage','Eisbergsalat':'iceberg lettuce','Paprika':'bell pepper','Zwiebel':'onion','Champignon':'mushrooms','Tomate':'tomato',
    'Gemüse':'vegetables','Peperoni':'hot peppers','Ananas':'pineapple','Oliven':'olives','Brokkoli':'broccoli','Mais':'corn','Schinken':'ham','Salami':'salami',
    'Dönerfleisch':'döner meat','Hähnchen-Dönerfleisch':'chicken döner meat','Käse':'cheese','Halloumikäse':'halloumi','Fetakäse':'feta'};
  function w(v){if(SP!=='en'||!W[v])return v;return W[v].charAt(0).toUpperCase()+W[v].slice(1);}
  function gerichtLi(nr){return document.querySelector('li.gericht[data-k="'+nr+'"]');}
  try{zettel=JSON.parse(localStorage.getItem(ZK)||'[]');if(!Array.isArray(zettel))zettel=[];}catch(e){zettel=[];}
  zettel.forEach(function(x){x.u=uidZ++;if(x.o&&!Array.isArray(x.o.s))x.o.s=x.o.s?[x.o.s]:[];});
  function speichern(){try{localStorage.setItem(ZK,JSON.stringify(zettel.map(function(x){var y=Object.assign({},x);delete y.u;return y;})));}catch(e){}}
  function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  function grund(t){return {s:(t==='D'||t==='SA')?['Kräuter']:[],ohne:[],ex:[],wahl:[],va:''};}
  function exPreis(o){return (o.ex||[]).reduce(function(a,e){return a+(GEMUESE.indexOf(e)>-1?150:200);},0);}
  function aktionZ(x){var li=gerichtLi(x.k);if(!li)return null;var gs=li.dataset.g?li.dataset.g.split('|'):[''];
    var tag=abh.tag||isoTag(0),zi=ZINFO[abh.zeit],min=zi?zi.min:(tag===isoTag(0)?jetzt().min:null);
    return aktion(x.k,Math.max(0,gs.indexOf(x.g||'')),tag,abh.laden||null,min);}
  function stueck(x){var ak=aktionZ(x);return (ak?ak.c:x.c)+exPreis(x.o);}
  function sig(x){var o=x.o;return [x.k,x.g,o.s.slice().sort().join(','),o.ohne.slice().sort().join(','),o.ex.slice().sort().join(','),o.wahl.slice().sort().join(','),o.va,x.notiz||'',x.fuer||''].join('|');}
  function liste(a,en){var u=en?' and ':' und ';return a.length<2?a.join(''):a.slice(0,-1).join(', ')+u+a[a.length-1];}
  /* Wünsche als Text; en=true nur für die Anzeige, die Nachricht an den Laden ist immer deutsch */
  function wuensche(x,en){
    var o=x.o,t=[],tr=function(a){return en?a.map(function(v){return (W[v]||v);}):a;};
    if(x.t==='D'||x.t==='SA'){var so=SOSSEN.filter(function(n){return o.s.indexOf(n)>-1;});
      if(en)t.push(!so.length?'no sauce':liste(tr(so),true)+' sauce');
      else t.push(!so.length?'ohne Soße':so.length===1?so[0]+'-Soße':so.slice(0,-1).join('-, ')+'- und '+so[so.length-1]+'-Soße');}
    if(o.ohne.length)t.push((en?'no ':'ohne ')+liste(tr(o.ohne),en));
    if(x.t==='S')t.push(o.wahl.length<3?(en?'choose '+(3-o.wahl.length)+' more toppings':'noch '+(3-o.wahl.length)+' Zutaten wählen'):(en?'with ':'mit ')+liste(tr(o.wahl),en));
    if(x.t==='R')t.push(o.va?(en?'option ':'Variante ')+o.va.charAt(0):(en?'choose option':'Variante wählen'));
    if(x.t==='B')t.push(o.va?(en?'with ':'mit ')+(en?(W[o.va]||o.va):o.va):(en?'choose topping':'Belag wählen'));
    tr(o.ex).forEach(function(e){t.push('extra '+e);});
    return t.join(', ');
  }
  /* Anzeigename/Beschreibung in der gewählten Sprache */
  function nameA(x){if(SP!=='en')return x.n;var li=gerichtLi(x.k);return li&&li.dataset.ne||x.n;}
  function beschrA(x){if(SP!=='en')return x.d;var li=gerichtLi(x.k);return li&&li.dataset.dn||x.d;}
  function zusammenfassen(){
    var neu=[],idx={};
    zettel.forEach(function(x){var k=sig(x);if(idx[k]!=null&&x.u!==offen&&neu[idx[k]].u!==offen){neu[idx[k]].q+=x.q;}else{idx[k]=neu.length;neu.push(x);}});
    zettel=neu;
  }
  var zl=document.getElementById('zettel-leiste'),huelle=document.getElementById('zettel'),zliste=document.getElementById('zettel-liste'),
      zsumme=document.getElementById('zettel-summe'),zmeld=document.getElementById('zettel-meldung'),meldTimer=null,zuletzt=null;
  function anzahl(){return zettel.reduce(function(a,x){return a+x.q;},0);}
  function summe(){return zettel.reduce(function(a,x){return a+x.q*stueck(x);},0);}
  function melden(t){zmeld.textContent=t;zmeld.hidden=false;clearTimeout(meldTimer);meldTimer=setTimeout(function(){zmeld.hidden=true;},2400);}
  function el(tag,cls,text){var x=document.createElement(tag);if(cls)x.className=cls;if(text!=null)x.textContent=text;return x;}
  function knopf(text,attrs){var b=el('button',null,text);b.type='button';for(var a in attrs)b.setAttribute(a,attrs[a]);return b;}
  function chips(titel,werte,gewaehlt,art,uid,extra){
    var g=el('div','z-gruppe');g.appendChild(el('span','z-gruppe-titel',titel));var wb=el('div','z-chips');
    werte.forEach(function(v){var an=gewaehlt.indexOf(v)>-1;var b=knopf(w(v)+(extra||''),{'class':'chip','aria-pressed':String(an),'data-o':art,'data-w':v,'data-u':uid});
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
            bw.appendChild(knopf(L(BEI_NAME[b][0],BEI_NAME[b][1])+(zb?preisDiff(x,zb):''),{'class':'chip','aria-pressed':String(b===va.bei),'data-bei':b,'data-u':x.u}));});
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
      gg.querySelectorAll('.chip').forEach(function(c){c.setAttribute('aria-pressed',String(o.ohne.indexOf(c.dataset.w)<0));});
      box.appendChild(gg);
    }
    if(x.t==='S')box.appendChild(chips(L('3 Zutaten Ihrer Wahl (','3 toppings of your choice (')+o.wahl.length+L(' von 3)',' of 3)'),GEMUESE.concat(FLEISCH,KAESE),o.wahl,'wahl',x.u));
    if(x.t==='R')box.appendChild(chips(L('Variante','Option'),(x.v||'').split('|').filter(Boolean),[o.va],'va',x.u));
    if(x.t==='B')box.appendChild(chips(L('Belag (einer zur Wahl)','Topping (choose one)'),BELAG,[o.va],'va',x.u));
    if(x.t==='P'||x.t==='S'||x.t==='R'){
      box.appendChild(chips(L('Extra je Zutat +1,50 €','Extra per topping +1,50 €'),GEMUESE,o.ex,'ex',x.u));
      box.appendChild(chips(L('Extra je Zutat +2,00 €','Extra per topping +2,00 €'),FLEISCH.concat(KAESE),o.ex,'ex',x.u));
    }
    return box;
  }
  function zeichnen(){
    var n=anzahl();
    zl.hidden=n===0;document.body.classList.toggle('mit-zettel',n>0);
    zl.querySelector('.zl-anzahl').textContent=n;zl.querySelector('.zl-summe').textContent=euro(summe());
    zl.setAttribute('aria-label',L('Meine Bestellung ansehen: ','View my order: ')+n+(n===1?L(' Gericht, ',' dish, '):L(' Gerichte, ',' dishes, '))+euro(summe()));
    zliste.textContent='';
    zettel.forEach(function(x){
      var li=el('li','z-eintrag'),kopf=el('div');
      var na=nameA(x);
      kopf.appendChild(el('span','z-name',na+(x.g?' ('+x.g+')':'')));
      var wt=x.t?wuensche(x,SP==='en'):beschrA(x);if(wt&&SP==='en')wt=wt.charAt(0).toUpperCase()+wt.slice(1);
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
    zsumme.textContent=euro(summe());
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
        var nm=(SP==='en'&&li.dataset.ne||li.dataset.n)+(g?' '+g:'');
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
      else{var arr=o[art],i2=arr.indexOf(wert);if(i2>-1)arr.splice(i2,1);else if(!(art==='wahl'&&arr.length>=3))arr.push(wert);}
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
  function tagKurz(off,en){return tagDatum(off,{weekday:'short',day:'numeric',month:en?'short':'2-digit'},en?'en-GB':'de-DE');}
  function tagLang(off){var t=tagDatum(off,{weekday:'long',day:'2-digit',month:'2-digit'});return /\.$/.test(t)?t:t+'.';}   /* „Freitag, 24.10.“ */
  /* mögliche Abholzeiten eines Tages (Minuten), 15-Minuten-Raster, heute frühestens in 20 Minuten */
  function slots(off){
    var n=jetzt(),h=tagZeit(abh.laden,off),res=[];if(!h)return res;
    var start=h[0]+15;if(off===0)start=Math.max(start,Math.ceil((n.min+20+warte(abh.laden))/15)*15);
    for(var m=start;m<=h[1]-15;m+=15)res.push(m);
    return res;
  }
  function zeitenFuellen(){
    selZeit.textContent='';selTag.textContent='';hinweisZ.hidden=true;ZINFO={};
    if(!abh.laden){[selTag,selZeit].forEach(function(s){var o=el('option',null,L('Bitte zuerst den Laden wählen','Please choose the shop first'));o.value='';s.appendChild(o);s.disabled=true;});return;}
    selTag.disabled=selZeit.disabled=false;
    var n=jetzt(),en=SP==='en',tage=[];
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
    if(off===0&&wz){hinweisZ.textContent=L('Gerade viel los: Abholung frühestens in ca. '+(wz+20)+' Minuten.','Busy right now: earliest pickup in about '+(wz+20)+' minutes.');hinweisZ.hidden=false;}
    if(off===0&&h0&&n.min>=h0[0]){
      optionen.push({v:'heute, so schnell wie möglich',t:L('So schnell wie möglich','As soon as possible')});ZINFO['heute, so schnell wie möglich']={off:0,min:n.min+20+wz};}
    slots(off).forEach(function(m){var v=vor+', '+zeitText(m);optionen.push({v:v,t:zeitText(m,en)});ZINFO[v]={off:off,min:m};});
    optionen.forEach(function(x){var o=el('option',null,x.t);o.value=x.v;selZeit.appendChild(o);});
    if(optionen.some(function(x){return x.v===abh.zeit;}))selZeit.value=abh.zeit;else abh.zeit=selZeit.value;
    abhSpeichern();zeichnenSpaeter();
  }
  var zsp=false;function zeichnenSpaeter(){if(zsp)return;zsp=true;setTimeout(function(){zsp=false;zeichnen();waAktualisieren();},0);}
  var WA={"freital": "491601836249", "altenberg": "491601836249"},waKnopf=document.getElementById('zettel-whatsapp'),waHinweis=document.getElementById('wa-hinweis');
  var verfHinweis=document.getElementById('verf-hinweis');
  function konflikte(){return zettel.filter(function(x){return sperreZettel(x.k);}).length;}
  function waAktualisieren(){
    var nr=abh.laden&&WA[abh.laden],kf=konflikte();
    verfHinweis.hidden=!kf;document.getElementById('zettel-kopieren').disabled=!!kf;
    verfHinweis.textContent=kf===1?L('Ein Gericht ist zur gewählten Zeit nicht zu haben. Bitte oben ändern.','One dish is not available at the chosen time. Please change it above.')
      :L(kf+' Gerichte sind zur gewählten Zeit nicht zu haben. Bitte oben ändern.',kf+' dishes are not available at the chosen time. Please change them above.');
    if(kf||sammel)nr=null;
    waKnopf.hidden=!nr;waHinweis.hidden=!!nr||!!kf||!Object.keys(WA).length;
    if(nr)waKnopf.href='https://wa.me/'+nr+'?text='+encodeURIComponent(zettelText());
  }
  function ladenZeigen(){
    document.querySelectorAll('[data-laden]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.laden===abh.laden));});
    document.querySelectorAll('[data-anruf]').forEach(function(a){a.hidden=!!abh.laden&&a.dataset.anruf!==abh.laden;});
    zeitenFuellen();waAktualisieren();
  }
  document.querySelectorAll('[data-laden]').forEach(function(b){b.addEventListener('click',function(){abh.laden=b.dataset.laden;abhSpeichern();ladenZeigen();verfZeigen();});});
  selZeit.addEventListener('change',function(){abh.zeit=selZeit.value;abhSpeichern();zeichnen();waAktualisieren();});
  selTag.addEventListener('change',function(){abh.tag=selTag.value;abh.zeit='';abhSpeichern();zeitenFuellen();waAktualisieren();});
  eName.value=abh.name||'';eName.addEventListener('input',function(){abh.name=eName.value;abhSpeichern();waAktualisieren();});
  ladenZeigen();
  zl.addEventListener('click',function(){zeitenFuellen();waAktualisieren();});
  var TEL={"freital": ["0351 27676660", "+4935127676660"], "altenberg": ["035056 23674", "+493505623674"]},waGesendet=document.getElementById('wa-gesendet');
  waKnopf.addEventListener('click',function(){waAktualisieren();letzteMerken();
    try{var bw=JSON.parse(localStorage.getItem('saray-bewertung')||'null');if(!bw||!bw.fertig)localStorage.setItem('saray-bewertung',JSON.stringify({l:abh.laden,t:Date.now()}));}catch(e){}
    if(waKnopf.hidden)return;var tl=TEL[abh.laden];waGesendet.textContent='';
    waGesendet.appendChild(document.createTextNode(L('Gesendet? Der Laden bestätigt Ihre Bestellung per WhatsApp. Ohne Antwort bitte anrufen: ','Sent? The shop confirms your order via WhatsApp. No reply? Please call: ')));
    var a=el('a',null,tl[0]);a.href='tel:'+tl[1];waGesendet.appendChild(a);waGesendet.hidden=false;});
  /* „Wie letztes Mal“: Zettel merken, sobald er abgeschickt, kopiert oder vorgelesen wird */
  var LK='saray-letzte',letzte=null,boxL=document.getElementById('letzte');
  try{letzte=JSON.parse(localStorage.getItem(LK)||'null');}catch(e){letzte=null;}
  function letzteMerken(){
    if(!zettel.length)return;
    letzte={am:Date.now(),p:zettel.map(function(x){return {k:x.k,g:x.g,q:x.q,o:x.o,notiz:x.notiz||''};})};
    try{localStorage.setItem(LK,JSON.stringify(letzte));}catch(e){}
  }
  function letzteGueltig(){
    if(!letzte||!Array.isArray(letzte.p))return [];
    return letzte.p.filter(function(p){var li=gerichtLi(p.k);if(!li)return false;var gs=li.dataset.g?li.dataset.g.split('|'):[''];return gs.indexOf(p.g||'')>-1;});
  }
  function letzteZeigen(){
    if(!boxL)return;
    var g=letzteGueltig(),suche=document.getElementById('suche-feld');
    boxL.hidden=!g.length||zettel.length>0||!!(suche&&suche.value.trim());
    if(boxL.hidden)return;
    var zus={};g.forEach(function(p){var li=gerichtLi(p.k),nm=(SP==='en'&&li.dataset.ne||li.dataset.n)+(p.g?' ('+p.g+')':'');zus[nm]=(zus[nm]||0)+p.q;});
    document.getElementById('letzte-liste').textContent=Object.keys(zus).map(function(k){return zus[k]+'× '+k;}).join(' · ');
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
  document.getElementById('letzte-knopf').addEventListener('click',function(){
    letzteGueltig().forEach(function(p){var x=ausDaten(p);if(x)zettel.push(x);});
    zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();oeffnen();
  });
  document.querySelectorAll('[data-anruf]').forEach(function(a){a.addEventListener('click',letzteMerken);});
  function zettelText(){
    var test=document.body.classList.contains('vorschau')?['*TEST – Seite nicht freigeschaltet, keine echte Bestellung*','']:[];
    var vb=ZINFO[abh.zeit]&&ZINFO[abh.zeit].off>0;
    var z=[(vb?'Vorbestellung':'Bestellung')+' Saray Döner'+(abh.laden?' '+(abh.laden==='freital'?'Freital':'Altenberg'):'')];
    if(abh.zeit)z.push('Abholung: '+abh.zeit);
    if(abh.name)z.push('Name: '+abh.name);
    z.push('');
    zettel.forEach(function(x){z.push(zeileText(x));});
    z.push('Summe: '+euro(summe()));return test.concat(z).join('\n');
  }
  function zeileText(x){var w=x.t?wuensche(x):'';
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
  function dialogZu(){sDlg.hidden=true;}
  /* Fenster immer über der Bildschirmtastatur: an den sichtbaren Bereich anpassen (iOS verkleinert ihn) */
  function dlgAnpassen(){
    if(sDlg.hidden||!window.visualViewport)return;var v=window.visualViewport;
    sDlg.style.top=v.offsetTop+'px';sDlg.style.height=v.height+'px';sDlg.style.bottom='auto';
  }
  if(window.visualViewport){window.visualViewport.addEventListener('resize',dlgAnpassen);window.visualViewport.addEventListener('scroll',dlgAnpassen);}
  sDlg.addEventListener('focusin',function(ev){if(ev.target.tagName==='INPUT')setTimeout(function(){dlgAnpassen();ev.target.scrollIntoView({block:'nearest'});},300);});
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
    var m=/^#(sammel|teil)=([A-Za-z0-9_-]+)/.exec(location.hash);if(!m)return;
    history.replaceState(null,'',location.pathname+location.search);
    var d;try{d=dekodieren(m[2]);}catch(e){melden(L('Der Link ist unvollständig. Bitte noch einmal schicken lassen.','The link is incomplete. Please ask for it again.'));return;}
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
  var spKnopf=document.getElementById('sprache');
  function sprache(l,merken){
    SP=l;document.documentElement.lang=l;
    document.querySelectorAll('[data-en]').forEach(function(x){if(x._de==null)x._de=x.textContent;x.textContent=l==='en'?x.dataset.en:x._de;});
    document.querySelectorAll('[data-en-html]').forEach(function(x){if(x._de==null)x._de=x.innerHTML;x.innerHTML=l==='en'?x.dataset.enHtml:x._de;});
    document.querySelectorAll('[data-en-ph]').forEach(function(x){if(x._de==null)x._de=x.placeholder;x.placeholder=l==='en'?x.dataset.enPh:x._de;});
    document.querySelectorAll('[data-en-aria]').forEach(function(x){if(x._dea==null)x._dea=x.getAttribute('aria-label');x.setAttribute('aria-label',l==='en'?x.dataset.enAria:x._dea);});
    document.querySelectorAll('[data-en-title]').forEach(function(x){if(x._det==null)x._det=x.getAttribute('title');x.setAttribute('title',l==='en'?x.dataset.enTitle:x._det);});
    spKnopf.textContent=l==='en'?'DE':'EN';spKnopf.lang=l==='en'?'de':'en';
    spKnopf.setAttribute('aria-label',l==='en'?'Auf Deutsch umschalten':'Switch to English');
    if(merken){try{localStorage.setItem(SPK,l);}catch(e){}}
    try{aktualisieren();}catch(e){}
    if(feld&&feld.value.trim())suchen();
    zeichnen();zeitenFuellen();waAktualisieren();handZeigen();try{aktionenZeigen();}catch(e){}
  }
  spKnopf.addEventListener('click',function(){sprache(SP==='en'?'de':'en',true);});
  if(SP==='en')sprache('en',false);

  /* Impressum/Datenschutz per Link öffnen */
  function oeffne(){var d=document.getElementById(location.hash.slice(1));if(d&&d.tagName==='DETAILS')d.open=true;}
  window.addEventListener('hashchange',oeffne);oeffne();
})();
