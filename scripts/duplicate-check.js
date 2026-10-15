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
let rows=[],lastSig="",stable=0;
for(let i=0;i<40;i++){
  await sleep(250);
  rows=[...table.querySelectorAll("tbody tr")];
  const sig=rows.map(r=>r.innerText.trim()).join("\n");
  if(sig===lastSig) stable++; else stable=0;
  lastSig=sig;
  if(stable>=2) break;
}
const rows2=[...document.querySelectorAll("#yollukSorgulaDataTable tbody tr")];
return {count:rows2.length,candidates:rows2.map(r=>({text:r.innerText.trim(),
links:[...r.querySelectorAll("a")].map(a=>a.href).filter(Boolean)}))};
})()
