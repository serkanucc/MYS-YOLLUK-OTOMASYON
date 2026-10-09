(async()=>{
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
const field=t=>{const l=[...document.querySelectorAll("label.yte-form-label")].find(x=>x.title===t);if(!l)throw Error("Alan yok: "+t);return document.getElementById(l.htmlFor)};
const inputOf=e=>e.matches("input")?e:e.querySelector("input")||e;
const setInput=(e,v)=>{e=inputOf(e);const s=Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,"value").set;s.call(e,String(v));e.dispatchEvent(new Event("input",{bubbles:true}));e.dispatchEvent(new Event("change",{bubbles:true}));};
const button=t=>{const b=[...document.querySelectorAll("button")].find(x=>x.innerText.trim()===t);if(!b)throw Error("Buton yok: "+t);b.click()};
const norm=s=>String(s||"").toLocaleUpperCase("tr-TR").replace(/\s+/g," ").trim();
const visible=r=>{const b=r.getBoundingClientRect();return b.width>0&&b.height>0};
const optionText=x=>norm(x?.innerText||x?.textContent);
const select=async(label,text)=>{
 const e=field(label),p=e.querySelector(".yte-power-select");if(!p)throw Error("Seçim alanı yok: "+label);
 p.click();
 let inp=e.querySelector(".yte-power-select-trigger-input");
 for(let i=0;i<30;i++){await sleep(150);inp=e.querySelector(".yte-power-select-trigger-input");if(inp)break;}
 const wanted=norm(text);
 if(inp){setInput(inp,text);inp.dispatchEvent(new KeyboardEvent("keyup",{bubbles:true,key:"e"}));}
 let o=null;
 for(let i=0;i<40;i++){
   await sleep(200);
   const panels=[...document.querySelectorAll(".yte-power-select-options,[role=listbox]")].filter(visible);
   const local=(panels.length?panels[panels.length-1]:document).querySelectorAll?.(".yte-power-select-option,[role=option],li")||[];
   const opts=[...local].filter(visible);
   o=opts.find(x=>optionText(x)===wanted)||opts.find(x=>optionText(x).includes(wanted));
   if(o)break;
 }
 if(!o)throw Error("Seçenek yüklenmedi: "+label+" / "+text);
 o.click();
 for(let i=0;i<20;i++){
   await sleep(150);
   const selected=[...e.querySelectorAll(".yte-power-select-multiple-selected-option-label,.yte-power-select-selected-option")].map(x=>norm(x.innerText));
   const trigger=e.querySelector(".yte-power-select-trigger")?.innerText||"";
   if(selected.includes(wanted)||norm(trigger).includes(wanted))return;
 }
 throw Error("Seçim doğrulanamadı: "+label+" / "+text);
};
const retrySelect=async(label,text)=>{
 let last;
 for(let attempt=1;attempt<=2;attempt++){try{return await select(label,text)}catch(e){last=e;await sleep(800);}}
 throw last;
};
const daily="{{DAILY}}",amirTckn="{{AMIR_TCKN}}";await retrySelect("Yolluk Tipi","Yurtiçi Geçici Görev Yolluğu - Talimatlı");
setInput(field("Başlangıç Tarihi"),"{{START}}");field("Başlangıç Tarihi").blur();
setInput(field("Bitiş Tarihi"),"{{END}}");field("Bitiş Tarihi").blur();await sleep(700);
await retrySelect("Ödeme Kaynak Türü","MERKEZİ YÖNETİM");await sleep(700);
await retrySelect("Ödeme Kaynak Alt Türü","SAĞLIK BAKANLIĞI");await sleep(900);
await retrySelect("Program Türü","54 - TEDAVİ EDİCİ SAĞLIK");await sleep(800);await retrySelect("Alt Program Türü","167 - TEDAVİ HİZMETLERİ");await sleep(800);
await retrySelect("Faaliyet Türü","480 - Devlet Hastanesi Hizmetleri");await sleep(900);
await retrySelect("Alt Faaliyet Türü","17695 - Teşhis ve Tedavi Hizmetleri");await sleep(900);
await retrySelect("Gündelik Tipi",daily);
const add=[...document.querySelectorAll("button")].find(x=>x.innerText.trim()==="Ekle");if(add){add.click();await sleep(600);}
const be=document.querySelector("[data-testid=tertip_0]");if(!be)throw Error("Bütçe tertip satırı açılmadı");
const budgetWanted=norm("{{BUDGET}}");
const budgetSelected=()=>norm(be.innerText||"").includes(budgetWanted);
if(!budgetSelected()){
 const bp=be.querySelector(".yte-power-select");if(!bp)throw Error("Bütçe tertip seçim alanı yok");
 bp.click();
 let bi=null;
 for(let i=0;i<20;i++){await sleep(100);bi=be.querySelector(".yte-power-select-trigger-input");if(bi)break;}
 if(!bi)throw Error("Bütçe tertip arama alanı açılamadı");
 setInput(bi,"{{BUDGET}}");bi.dispatchEvent(new KeyboardEvent("keyup",{bubbles:true,key:"e"}));
 let bop=null;
 for(let i=0;i<50;i++){
   await sleep(150);
   const panels=[...document.querySelectorAll(".yte-power-select-options,[role=listbox]")].filter(visible);
   const panel=panels.length?panels[panels.length-1]:null;
   const opts=panel?[...panel.querySelectorAll(".yte-power-select-option,[role=option],li")].filter(visible):[];
   bop=opts.find(x=>optionText(x)===budgetWanted)||opts.find(x=>optionText(x).includes(budgetWanted));
   if(bop)break;
 }
 if(!bop)throw Error("Bütçe tertibi seçeneği yüklenmedi");
 bop.click();
 for(let i=0;i<20;i++){await sleep(100);if(budgetSelected())break;}
}
if(!budgetSelected())throw Error("Bütçe tertibi seçim doğrulaması başarısız");
const ai=document.querySelector("[data-testid=birimAmiriTcknInput]");if(!ai)throw Error("Birim Amiri TCKN alanı bulunamadı");
setInput(ai,amirTckn);await sleep(250);const aq=document.querySelector("[data-testid=birimAmiriAraButton]");if(!aq||aq.disabled)throw Error("Birim Amiri sorgu butonu aktif değil");aq.click();
let amirName="",amirTitle="";
for(let i=0;i<30;i++){await sleep(250);const al=document.querySelector('[title="Birim Amiri Ad Soyad"]');const au=document.querySelector('[title="Birim Amiri Unvan"]');const an=al?.parentElement?.querySelector("input");const av=au?.parentElement?.querySelector("input");amirName=an?.value?.trim()||"";amirTitle=av?.value?.trim()||"";if(amirName)break;}
if(!amirName)throw Error("Birim Amiri sorgusu sonucunda ad soyad gelmedi");
const sb=[...document.querySelectorAll("button")].find(x=>x.innerText.includes("Yolluk Süreç Hazırlama"));
return {selected:[...document.querySelectorAll(".yte-power-select-multiple-selected-option-label")].map(x=>x.innerText.trim()),dates:[...document.querySelectorAll("input")].filter(x=>x.placeholder==="Tarih Seçiniz").map(x=>x.value),unitManager:{tckn:amirTckn,name:amirName,title:amirTitle},submitDisabled:sb?sb.disabled:null};
})()