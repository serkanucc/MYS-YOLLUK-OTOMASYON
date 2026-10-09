(async()=>{const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const lab=[...document.querySelectorAll("label.yte-form-label")].find(x=>x.title==="Kimlik No");
const inp=lab?document.getElementById(lab.htmlFor):null;
if(!inp)throw Error("Sorgu Kimlik No alanı yok");
const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;
s.call(inp,String("{{TCKN}}"));inp.dispatchEvent(new Event("input",{bubbles:true}));
inp.dispatchEvent(new Event("change",{bubbles:true}));
const b=[...document.querySelectorAll("button")].find(x=>x.innerText.trim()==="Sorgula");
if(!b)throw Error("Sorgula yok");
b.click();
let rows=[],lastSig="",stable=0;
for(let i=0;i<40;i++){
  await sleep(250);
  rows=[...document.querySelectorAll("#yollukSorgulaDataTable tbody tr")];
  const sig=rows.map(r=>r.innerText.trim()).join("\n");
  if(sig===lastSig) stable++; else stable=0;
  lastSig=sig;
  if(stable>=2) break;
}
const rows2=[...document.querySelectorAll("#yollukSorgulaDataTable tbody tr")];
return {count:rows2.length,candidates:rows2.map(r=>({text:r.innerText.trim(),
links:[...r.querySelectorAll("a")].map(a=>a.href).filter(Boolean)}))};
})()
