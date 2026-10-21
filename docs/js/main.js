(function(){
  var ZEITEN={"freital": {"1": [600, 1320], "2": [600, 1320], "3": [600, 1320], "4": [600, 1320], "5": [600, 1320], "6": [660, 1320], "0": [660, 1320]}, "altenberg": {"1": [600, 1260], "2": [600, 1260], "3": [600, 1260], "4": [600, 1260], "5": [600, 1260], "6": [600, 1260], "0": [660, 1260]}};
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
  var KURZ={Sun:0,Mon:1,Tue:2,Wed:3,Thu:4,Fri:5,Sat:6};
  var weniger=window.matchMedia&&matchMedia('(prefers-reduced-motion: reduce)').matches;

  function jetzt(){
    var o={};
    new Intl.DateTimeFormat('en-GB',{timeZone:'Europe/Berlin',weekday:'short',hour:'2-digit',minute:'2-digit',hourCycle:'h23'})
      .formatToParts(new Date()).forEach(function(p){o[p.type]=p.value;});
    return {tag:KURZ[o.weekday],min:(+o.hour)*60+(+o.minute)};
  }
  function uhr(m){var h=Math.floor(m/60),r=m%60;if(SP==='en')return h+':'+(r<10?'0':'')+r;return r?h+':'+(r<10?'0':'')+r+' Uhr':h+' Uhr';}
  function lage(ort){
    var z=ZEITEN[ort],n=jetzt(),h=z[n.tag];
    if(h&&n.min>=h[0]&&n.min<h[1])return{offen:true,text:L('Jetzt geöffnet, bis ','Open now, until ')+uhr(h[1])};
    if(h&&n.min<h[0])return{offen:false,text:L('Geschlossen, öffnet heute um ','Closed, opens today at ')+uhr(h[0])};
    for(var i=1;i<=7;i++){var t=(n.tag+i)%7;if(z[t])return{offen:false,text:SP==='en'?'Closed, opens '+(i===1?'tomorrow':'on '+TAGE_E[t])+' at '+uhr(z[t][0]):'Geschlossen, öffnet '+(i===1?'morgen':'am '+TAGE[t])+' um '+uhr(z[t][0])};}
    return{offen:false,text:''};
  }
  function aktualisieren(){
    document.querySelectorAll('[data-status]').forEach(function(el){
      var s=lage(el.getAttribute('data-status'));el.setAttribute('data-offen',s.offen?'ja':'nein');
      el.querySelector('.status-text').textContent=s.text;
    });
    var tag=jetzt().tag;
    document.querySelectorAll('tr[data-tage]').forEach(function(tr){
      tr.classList.toggle('heute',tr.getAttribute('data-tage').split(',').indexOf(String(tag))>-1);
    });
  }
  try{aktualisieren();setInterval(aktualisieren,60000);}catch(e){}

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
  function verfolgen(){if(!fest)markiere(imBlick());}
  function loesen(){fest=null;}
  window.addEventListener('scroll',function(){
    if(geplant)return;geplant=true;
    requestAnimationFrame(function(){geplant=false;verfolgen();});
  },{passive:true});
  window.addEventListener('resize',verfolgen);
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
  var feld=document.getElementById('suche-feld'),gerichte=[].slice.call(document.querySelectorAll('.gericht'));
  var treffer=document.querySelector('.treffer'),nichts=document.querySelector('.nichts'),wort=nichts&&nichts.querySelector('q');
  gerichte.forEach(function(g){g._s=norm(g.getAttribute('data-s'));});
  function suchen(){
    var roh=feld.value.trim(),q=norm(roh),teile=q.split(/\s+/).filter(Boolean),n=0;
    gerichte.forEach(function(g){var ok=teile.every(function(w){return g._s.indexOf(w)>-1;});g.hidden=!ok;if(ok)n++;});
    document.querySelectorAll('.liste').forEach(function(l){
      var v=l.querySelectorAll('.gericht:not([hidden])').length;l.style.setProperty('--zeilen',Math.max(1,Math.ceil(v/2)));
      l.closest('.abschnitt').hidden=v===0;
    });
    document.querySelectorAll('.gruppe').forEach(function(g){
      var leer=!g.querySelector('.gericht:not([hidden])');g.hidden=leer;if(links[g.id])links[g.id].classList.toggle('leer',leer);
    });
    treffer.hidden=!teile.length||n===0;
    treffer.textContent=n===1?L('1 Gericht gefunden','1 dish found'):n+L(' Gerichte gefunden',' dishes found');
    nichts.hidden=!(teile.length&&n===0);if(wort)wort.textContent=roh;
    var bl=document.querySelector('.beliebt');if(bl)bl.hidden=teile.length>0;
    if(typeof letzteZeigen==='function')letzteZeigen();
    fest=null;verfolgen();
  }

  /* Bestellzettel mit Wünschen je Gericht */
  var ZK='saray-bestellzettel-2',zettel=[],uidZ=1,offen=null;
  var SOSSEN=['Knoblauch','Kräuter','Chili'],OHNE=['Zwiebeln','Tomaten','Gurken','Rotkohl','Weißkohl','Eisbergsalat'];
  var GEMUESE=['Paprika','Zwiebel','Champignon','Tomate','Peperoni','Ananas','Oliven','Brokkoli','Mais'];
  var FLEISCH=['Schinken','Salami','Dönerfleisch','Hähnchen-Dönerfleisch'],KAESE=['Käse','Halloumikäse','Fetakäse'];
  var PAARE=[['1','2'],['3','4'],['6','7'],['9','10'],['11','12'],['13','14'],['15','16'],['23','25'],['30','31'],['32','33'],['36','37'],
    ['40','41'],['42','43'],['50','51'],['52','53'],['54','55'],['60','61'],['123','124']],OHNE_K={},MIT_K={};
  PAARE.forEach(function(pq){OHNE_K[pq[0]]=pq[1];MIT_K[pq[1]]=pq[0];});
  var W={'Knoblauch':'garlic','Kräuter':'herb','Chili':'chili','Zwiebeln':'onions','Tomaten':'tomatoes','Gurken':'cucumber','Rotkohl':'red cabbage',
    'Weißkohl':'white cabbage','Eisbergsalat':'iceberg lettuce','Paprika':'bell pepper','Zwiebel':'onion','Champignon':'mushrooms','Tomate':'tomato',
    'Peperoni':'hot peppers','Ananas':'pineapple','Oliven':'olives','Brokkoli':'broccoli','Mais':'corn','Schinken':'ham','Salami':'salami',
    'Dönerfleisch':'döner meat','Hähnchen-Dönerfleisch':'chicken döner meat','Käse':'cheese','Halloumikäse':'halloumi','Fetakäse':'feta'};
  function w(v){if(SP!=='en'||!W[v])return v;return W[v].charAt(0).toUpperCase()+W[v].slice(1);}
  function gerichtLi(nr){return document.querySelector('li.gericht[data-k="'+nr+'"]');}
  try{zettel=JSON.parse(localStorage.getItem(ZK)||'[]');if(!Array.isArray(zettel))zettel=[];}catch(e){zettel=[];}
  zettel.forEach(function(x){x.u=uidZ++;if(x.o&&!Array.isArray(x.o.s))x.o.s=x.o.s?[x.o.s]:[];});
  function speichern(){try{localStorage.setItem(ZK,JSON.stringify(zettel.map(function(x){var y=Object.assign({},x);delete y.u;return y;})));}catch(e){}}
  function euro(c){return (c/100).toFixed(2).replace('.',',')+' €';}
  function grund(t){return {s:(t==='D'||t==='SA')?['Kräuter']:[],ohne:[],ex:[],wahl:[],va:''};}
  function exPreis(o){return (o.ex||[]).reduce(function(a,e){return a+(GEMUESE.indexOf(e)>-1?150:200);},0);}
  function stueck(x){return x.c+exPreis(x.o);}
  function sig(x){var o=x.o;return [x.k,x.g,o.s.slice().sort().join(','),o.ohne.slice().sort().join(','),o.ex.slice().sort().join(','),o.wahl.slice().sort().join(','),o.va,x.notiz||''].join('|');}
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
    if(x.t==='D'&&(OHNE_K[x.k]||MIT_K[x.k])){
      var partner=gerichtLi(OHNE_K[x.k]||MIT_K[x.k]),diff=partner?(+partner.dataset.p)-x.c:0,mit=!!MIT_K[x.k];
      var kg=el('div','z-gruppe');kg.appendChild(el('span','z-gruppe-titel',L('Käse','Cheese')));var kw=el('div','z-chips');
      kw.appendChild(knopf(L('mit Käse','with cheese')+(mit?'':' (+'+euro(Math.abs(diff))+')'),{'class':'chip','aria-pressed':String(mit),'data-kaese':x.u}));
      kg.appendChild(kw);box.appendChild(kg);
    }
    if(x.t==='D')box.appendChild(chips(L('Ohne','Without'),OHNE,o.ohne,'ohne',x.u));
    if(x.t==='S')box.appendChild(chips(L('3 Zutaten Ihrer Wahl (','3 toppings of your choice (')+o.wahl.length+L(' von 3)',' of 3)'),GEMUESE.concat(FLEISCH,KAESE),o.wahl,'wahl',x.u));
    if(x.t==='R')box.appendChild(chips(L('Variante','Option'),(x.v||'').split('|').filter(Boolean),[o.va],'va',x.u));
    if(x.t==='P'||x.t==='S'||x.t==='R'){
      box.appendChild(chips(L('Extra je Zutat +1,50 €','Extra per topping +1,50 €'),GEMUESE,o.ex,'ex',x.u));
      box.appendChild(chips(L('Extra je Zutat +2,00 €','Extra per topping +2,00 €'),FLEISCH.concat(KAESE),o.ex,'ex',x.u));
    }
    box.appendChild(knopf(L('Fertig','Done'),{'class':'knopf knopf-dunkel z-fertig','data-fertig':x.u}));
    return box;
  }
  function zeichnen(){
    var n=anzahl();
    zl.hidden=n===0;document.body.classList.toggle('mit-zettel',n>0);
    zl.querySelector('.zl-anzahl').textContent=n;zl.querySelector('.zl-summe').textContent=euro(summe());
    zl.setAttribute('aria-label',L('Bestellzettel ansehen: ','View order list: ')+n+(n===1?L(' Gericht, ',' dish, '):L(' Gerichte, ',' dishes, '))+euro(summe()));
    zliste.textContent='';
    zettel.forEach(function(x){
      var li=el('li','z-eintrag'),kopf=el('div');
      var na=nameA(x);
      kopf.appendChild(el('span','z-name',na+(x.g?' ('+x.g+')':'')));
      var wt=x.t?wuensche(x,SP==='en'):beschrA(x);if(wt&&SP==='en')wt=wt.charAt(0).toUpperCase()+wt.slice(1);if(wt){var wi=el('span','z-info',wt);if(/wählen|choose/.test(wt))wi.classList.add('z-fehlt');kopf.appendChild(wi);}
      li.appendChild(kopf);li.appendChild(el('span','z-preis',euro(stueck(x)*x.q)));
      var st=el('div','z-steuer'),q=el('span','z-menge',String(x.q));
      var m=knopf('−',{'data-a':'minus','data-u':x.u,'aria-label':(x.q===1?L('Entfernen: ','Remove: '):L('Eins weniger: ','One less: '))+na});
      var pl=knopf('+',{'data-a':'plus','data-u':x.u,'aria-label':L('Eins mehr: ','One more: ')+na});
      st.appendChild(m);st.appendChild(q);st.appendChild(pl);
      if(x.t&&offen!==x.u)st.appendChild(knopf(x.q>1?L('Eins davon anpassen','Customize one of them'):L('Anpassen','Customize'),{'class':'z-anpassen','data-anpassen':x.u}));
      li.appendChild(st);
      if(offen===x.u)li.appendChild(editor(x));
      var no=document.createElement('input');no.className='z-notiz';no.type='text';no.value=x.notiz||'';no.dataset.u=x.u;no.id='notiz-'+x.u;
      no.placeholder=L('Weitere Wünsche','Other requests');no.setAttribute('aria-label',L('Weitere Wünsche zu ','Other requests for ')+na);li.appendChild(no);
      zliste.appendChild(li);
    });
    zsumme.textContent=euro(summe());
    huelle.querySelector('.zettel-leer').hidden=n>0;huelle.querySelector('.zettel-voll').hidden=n===0;
    abgleichen();letzteZeigen();
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
    var hinweis=neu.t==='S'?L(' Zutaten auf dem Zettel wählen.',' Choose the toppings on your list.'):neu.t==='R'?L(' Variante auf dem Zettel wählen.',' Choose the option on your list.'):'';
    melden(nameA(neu)+(g?' ('+g+')':'')+L(' liegt auf dem Bestellzettel.',' added to your order list.')+hinweis);
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
    var kb=ev.target.closest('[data-kaese]');
    if(kb){var zk=finde(kb.dataset.kaese);if(!zk)return;var ziel=gerichtLi(OHNE_K[zk.k]||MIT_K[zk.k]);if(!ziel)return;
      zk.k=ziel.dataset.k;zk.n=ziel.dataset.n;zk.d=ziel.dataset.d;zk.c=+ziel.dataset.p;
      speichern();zeichnen();var kw2=zliste.querySelector('[data-kaese]');if(kw2)kw2.focus();return;}
    var f=ev.target.closest('[data-fertig]');
    if(f){offen=null;zusammenfassen();speichern();zeichnen();return;}
  });
  zliste.addEventListener('input',function(ev){var x=finde(ev.target.dataset.u);if(x){x.notiz=ev.target.value;speichern();}});
  zliste.addEventListener('change',function(ev){if(ev.target.classList.contains('z-notiz')){zusammenfassen();speichern();}});
  function oeffnen(){zuletzt=document.activeElement;zmeld.hidden=true;huelle.hidden=false;document.documentElement.style.overflow='hidden';document.getElementById('zettel-titel').focus();}
  function schliessen(){offen=null;zusammenfassen();speichern();zeichnen();huelle.hidden=true;document.documentElement.style.overflow='';if(zuletzt&&zuletzt.focus&&!zl.hidden)zuletzt.focus();}
  zl.addEventListener('click',oeffnen);
  huelle.addEventListener('click',function(ev){if(ev.target.closest('[data-zu]'))schliessen();});
  document.addEventListener('keydown',function(ev){if(ev.key==='Escape'&&!huelle.hidden)schliessen();});
  /* Abholung: Laden, Uhrzeit, Name */
  var AK='saray-abholung',abh={laden:'',zeit:'',name:''};
  try{abh=Object.assign(abh,JSON.parse(localStorage.getItem(AK)||'{}'));}catch(e){}
  function abhSpeichern(){try{localStorage.setItem(AK,JSON.stringify(abh));}catch(e){}}
  var selZeit=document.getElementById('abhol-zeit'),eName=document.getElementById('abhol-name'),hinweisZ=document.getElementById('abhol-hinweis');
  function zeitText(m,en){var h=Math.floor(m/60),r=m%60;return h+':'+(r<10?'0':'')+r+(en?'':' Uhr');}
  function zeitenFuellen(){
    selZeit.textContent='';hinweisZ.hidden=true;
    if(!abh.laden){var o=el('option',null,L('Bitte zuerst den Laden wählen','Please choose the shop first'));o.value='';selZeit.appendChild(o);selZeit.disabled=true;return;}
    selZeit.disabled=false;
    var z=ZEITEN[abh.laden],n=jetzt(),optionen=[];
    for(var i=0;i<7&&!optionen.length;i++){
      var tag=(n.tag+i)%7,h=z[tag];if(!h)continue;
      var start=h[0]+15;if(i===0)start=Math.max(start,Math.ceil((n.min+20)/15)*15);
      var ende=h[1]-15;if(start>ende)continue;
      var vor=i===0?'heute':i===1?'morgen':TAGE[tag],en=SP==='en',vorA=en?(i===0?'today':i===1?'tomorrow':TAGE_E[tag]):vor;
      if(i===0&&n.min>=h[0]&&n.min<h[1])optionen.push({v:'heute, so schnell wie möglich',t:L('So schnell wie möglich','As soon as possible')});
      for(var m=start;m<=ende;m+=15)optionen.push({v:vor+', '+zeitText(m),t:(i===0?'':vorA.charAt(0).toUpperCase()+vorA.slice(1)+', ')+zeitText(m,en)});
      if(i>0){hinweisZ.textContent=L('Heute ist keine Abholung mehr möglich. Sie können für '+vor+' vorbestellen.','Pickup is no longer possible today. You can pre-order for '+vorA+'.');hinweisZ.hidden=false;}
    }
    optionen.forEach(function(x){var o=el('option',null,x.t);o.value=x.v;selZeit.appendChild(o);});
    if(optionen.some(function(x){return x.v===abh.zeit;}))selZeit.value=abh.zeit;else abh.zeit=selZeit.value;
    abhSpeichern();
  }
  var WA={},waKnopf=document.getElementById('zettel-whatsapp'),waHinweis=document.getElementById('wa-hinweis');
  function waAktualisieren(){
    var nr=abh.laden&&WA[abh.laden];
    waKnopf.hidden=!nr;waHinweis.hidden=!!nr||!Object.keys(WA).length;
    if(nr)waKnopf.href='https://wa.me/'+nr+'?text='+encodeURIComponent(zettelText());
  }
  function ladenZeigen(){
    document.querySelectorAll('[data-laden]').forEach(function(b){b.setAttribute('aria-pressed',String(b.dataset.laden===abh.laden));});
    document.querySelectorAll('[data-anruf]').forEach(function(a){a.hidden=!!abh.laden&&a.dataset.anruf!==abh.laden;});
    zeitenFuellen();waAktualisieren();
  }
  document.querySelectorAll('[data-laden]').forEach(function(b){b.addEventListener('click',function(){abh.laden=b.dataset.laden;abhSpeichern();ladenZeigen();});});
  selZeit.addEventListener('change',function(){abh.zeit=selZeit.value;abhSpeichern();waAktualisieren();});
  eName.value=abh.name||'';eName.addEventListener('input',function(){abh.name=eName.value;abhSpeichern();waAktualisieren();});
  ladenZeigen();
  zl.addEventListener('click',function(){zeitenFuellen();waAktualisieren();});
  waKnopf.addEventListener('click',function(){waAktualisieren();letzteMerken();});
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
  document.getElementById('letzte-knopf').addEventListener('click',function(){
    letzteGueltig().forEach(function(p){
      var li=gerichtLi(p.k),gs=li.dataset.g?li.dataset.g.split('|'):[''],pr=li.dataset.p.split('|').map(Number);
      var o=Object.assign(grund(li.dataset.t),JSON.parse(JSON.stringify(p.o||{})));
      ['s','ohne','ex','wahl'].forEach(function(a){if(!Array.isArray(o[a]))o[a]=[];});
      zettel.push({k:p.k,n:li.dataset.n,d:li.dataset.d,g:p.g||'',c:pr[Math.max(0,gs.indexOf(p.g||''))],q:Math.max(1,+p.q||1),
        t:li.dataset.t||'',v:li.dataset.v||'',o:o,notiz:p.notiz||'',u:uidZ++});
    });
    zusammenfassen();speichern();zeichnen();zeitenFuellen();waAktualisieren();oeffnen();
  });
  document.querySelectorAll('[data-anruf]').forEach(function(a){a.addEventListener('click',letzteMerken);});
  function zettelText(){
    var z=['Bestellung Saray Döner'+(abh.laden?' '+(abh.laden==='freital'?'Freital':'Altenberg'):'')];
    if(abh.zeit)z.push('Abholung: '+abh.zeit);
    if(abh.name)z.push('Name: '+abh.name);
    z.push('');
    zettel.forEach(function(x){var w=x.t?wuensche(x):'';
      z.push(x.q+'× '+x.n+(x.g?' ('+x.g+')':'')+(w?', '+w:'')+': '+euro(stueck(x)*x.q)+(x.notiz?'\n   Wunsch: '+x.notiz:''));});
    z.push('Summe: '+euro(summe()));return z.join('\n');
  }
  document.getElementById('zettel-kopieren').addEventListener('click',function(){
    var t=zettelText();
    function notfall(){var ta=document.createElement('textarea');ta.value=t;ta.setAttribute('readonly','');ta.style.position='fixed';ta.style.opacity='0';
      document.body.appendChild(ta);ta.select();var ok=false;try{ok=document.execCommand('copy');}catch(e){}ta.remove();
      melden(ok?L('Zettel kopiert. Jetzt in WhatsApp oder SMS einfügen.','List copied. Now paste it into WhatsApp or a text message.'):L('Kopieren hat nicht geklappt. Bitte den Zettel abschreiben.','Copying did not work. Please write the list down.'));}
    letzteMerken();
    if(navigator.clipboard&&navigator.clipboard.writeText){navigator.clipboard.writeText(t).then(function(){melden(L('Zettel kopiert. Jetzt in WhatsApp oder SMS einfügen.','List copied. Now paste it into WhatsApp or a text message.'));},notfall);}else notfall();
  });
  var leeren=document.getElementById('zettel-leeren'),leerenTimer=null;
  leeren.addEventListener('click',function(){
    if(leeren.dataset.sicher){zettel=[];offen=null;speichern();zeichnen();schliessen();melden(L('Bestellzettel geleert.','Order list cleared.'));delete leeren.dataset.sicher;leeren.textContent=L('Zettel leeren','Clear list');return;}
    leeren.dataset.sicher='1';leeren.textContent=L('Wirklich alles löschen? Nochmal tippen.','Really delete everything? Tap again.');
    clearTimeout(leerenTimer);leerenTimer=setTimeout(function(){delete leeren.dataset.sicher;leeren.textContent=L('Zettel leeren','Clear list');},4000);
  });
  zeichnen();

  if(feld){
    feld.addEventListener('input',suchen);
    nichts.querySelector('button').addEventListener('click',function(){feld.value='';suchen();feld.focus();});
  }

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
    spKnopf.textContent=l==='en'?'DE':'EN';spKnopf.lang=l==='en'?'de':'en';
    spKnopf.setAttribute('aria-label',l==='en'?'Auf Deutsch umschalten':'Switch to English');
    if(merken){try{localStorage.setItem(SPK,l);}catch(e){}}
    try{aktualisieren();}catch(e){}
    if(feld&&feld.value.trim())suchen();
    zeichnen();zeitenFuellen();waAktualisieren();
  }
  spKnopf.addEventListener('click',function(){sprache(SP==='en'?'de':'en',true);});
  if(SP==='en')sprache('en',false);

  /* Impressum/Datenschutz per Link öffnen */
  function oeffne(){var d=document.getElementById(location.hash.slice(1));if(d&&d.tagName==='DETAILS')d.open=true;}
  window.addEventListener('hashchange',oeffne);oeffne();
})();
