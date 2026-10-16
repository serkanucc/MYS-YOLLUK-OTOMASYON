(async()=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const norm=s=>String(s||"").normalize("NFD").replace(/[\u0300-\u036f]/g,"").toLowerCase().replace(/[^a-z0-9]/g,"");
let lab=null,inp=null,b=null;
for(let i=0;i<40;i++){
  lab=null;inp=null;b=null;
  const labels=[...document.querySelectorAll("label.yte-form-label")];
  const wanted=["kimlikno","tckimlikno","tckimliknumarasi","kimliknumarasi","tckn"];
  lab=labels.find(x=>wanted.includes(norm(x.title))||wanted.includes(norm(x.innerText)));
  if(lab)inp=document.getElementById(lab.htmlFor)||lab.parentElement?.querySelector("input");
  if(!inp){
    inp=[...document.querySelectorAll("input")].find(x=>/kimlik|tckn|tcno/i.test([x.id,x.name,x.placeholder,x.getAttribute("aria-label"),x.getAttribute("data-testid")].join(" ")));
  }
  b=[...document.querySelectorAll("button")].find(x=>norm(x.innerText)==="sorgula");
  if(inp&&b)break;
  await sleep(250);
}
if(!inp){
  const labels=[...document.querySelectorAll("label.yte-form-label")].map(x=>({title:x.title,text:x.innerText.trim()})).slice(0,40);
  const inputs=[...document.querySelectorAll("input")].map(x=>({id:x.id,name:x.name,placeholder:x.placeholder,aria:x.getAttribute("aria-label"),testid:x.getAttribute("data-testid")})).slice(0,40);
  throw Error("Sorgu Kimlik No alanı 10 saniye içinde bulunamadı; URL="+location.href+"; labels="+JSON.stringify(labels)+"; inputs="+JSON.stringify(inputs));
}
if(!b)throw Error("Sorgula butonu 10 saniye içinde bulunamadı; URL="+location.href);
const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;
s.call(inp,String("{{TCKN}}"));inp.dispatchEvent(new Event("input",{bubbles:true}));
inp.dispatchEvent(new Event("change",{bubbles:true}));
b.click();
let table=null;
for(let i=0;i<40;i++){
  table=document.querySelector("#yollukSorgulaDataTable");
  if(table)break;
  await sleep(250);
}
if(!table){
  const tables=[...document.querySelectorAll("table")].map(t=>({id:t.id,head:t.innerText.slice(0,180)})).slice(0,20);
  throw Error("Sorgula sonrası yolluk sonuç tablosu 10 saniye içinde bulunamadı; URL="+location.href+"; tables="+JSON.stringify(tables));
}
let rows=[],lastSig=null,stable=0,emptyStable=0;
const isVisible=e=>{const r=e.getBoundingClientRect();return r.width>0&&r.height>0;};
for(let i=0;i<40;i++){
  await sleep(250);
  table=document.querySelector("#yollukSorgulaDataTable");
  if(!table)continue;
  rows=[...table.querySelectorAll("tbody tr")].filter(r=>!r.querySelector(".dataTables_empty")&&!/^(no data available in table|no matching records|no records found|kayit bulunamadi|kayit bulunmamaktadir|veri bulunamadi|gosterilecek veri bulunamadi|eslesen kayit yok)$/i.test(norm(r.innerText)));
  const sig=rows.map(r=>r.innerText.trim()).join("\n");
  const tableText=norm(table.innerText);
  const explicitEmpty=!!table.querySelector(".dataTables_empty,td.dataTables_empty,[data-empty-state='true']")||/(no data available in table|no matching records|no records found|kayit bulunamadi|kayit bulunmamaktadir|veri bulunamadi|gosterilecek veri bulunamadi|eslesen kayit yok)/i.test(tableText);
  const loading=[...document.querySelectorAll(".dataTables_processing,[aria-busy='true'],.loading,.spinner")].some(isVisible);
  if(rows.length){
    if(sig===lastSig)stable++;else stable=0;
    emptyStable=0;
    if(stable>=2)break;
  }else{
    stable=0;
    // Boş sonuç ilk render’da geçici olabilir. Açık boş-durum işareti 7.5 sn
    // boyunca görünür ve yükleme göstergesi yoksa ancak o zaman sıfır kayıt kabul edilir.
    if(explicitEmpty&&!loading)emptyStable++;else emptyStable=0;
    if(emptyStable>=30)break;
  }
  lastSig=sig;
}
const rows2=[...document.querySelectorAll("#yollukSorgulaDataTable tbody tr")].filter(r=>!r.querySelector(".dataTables_empty")&&!/^(no data available in table|no matching records|no records found|kayit bulunamadi|kayit bulunmamaktadir|veri bulunamadi|gosterilecek veri bulunamadi|eslesen kayit yok)$/i.test(norm(r.innerText)));
if(!rows2.length&&emptyStable<30){
  const tableText=document.querySelector("#yollukSorgulaDataTable")?.innerText||"";
  throw Error("Sorgu sonucu boş olduğu güvenle doğrulanamadı; olası yükleme/gecikme nedeniyle devam edilmiyor. URL="+location.href+"; table="+tableText.slice(0,500));
}
return {count:rows2.length,candidates:rows2.map(r=>({text:r.innerText.trim(),
links:[...r.querySelectorAll("a")].map(a=>a.href).filter(Boolean)}))};
})()
