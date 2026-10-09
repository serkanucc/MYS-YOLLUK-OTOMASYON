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
const forceIbanReset="{{FORCE_IBAN}}"==="true";const tckn="{{TCKN}}",iban="{{IBAN}}",daily="{{DAILY}}",amirTckn="{{AMIR_TCKN}}";
setInput(field("Kimlik No"),tckn);await sleep(250);document.querySelector("[data-testid=kisiAraButton]").click();await sleep(1000);
button("Mernis'ten Güncelle");await sleep(700);button("Maaş Güncelle");await sleep(900);
const ib=field("IBAN"),ibanNorm=norm(iban);
const vals=()=>[...ib.querySelectorAll(".yte-power-select-multiple-selected-option-label")].map(x=>norm(x.innerText));
if(forceIbanReset||!vals().includes(ibanNorm)){
 for(const x of [...ib.querySelectorAll(".yte-power-select-multiple-selected-option")]){
  const rm=x.querySelector(".yte-power-select-multiple-selected-option-close");if(rm){rm.click();await sleep(250);}
 }
 ib.querySelector(".yte-power-select").click();await sleep(200);
 const ii=ib.querySelector(".yte-power-select-trigger-input");if(!ii)throw Error("IBAN arama alanı açılmadı");
 setInput(ii,iban);ii.dispatchEvent(new KeyboardEvent("keyup",{bubbles:true,key:"e"}));
 let io=null;
 for(let i=0;i<40&&!io;i++){await sleep(150);const ps=[...document.querySelectorAll(".yte-power-select-options,[role=listbox]")].filter(visible),p=ps[ps.length-1];const os=p?[...p.querySelectorAll(".yte-power-select-option,[role=option],li")].filter(visible):[];io=os.find(x=>optionText(x)===ibanNorm)||os.find(x=>optionText(x).includes(ibanNorm));}
 if(io){io.click();await sleep(500);}
}
const ibanInput=ib.querySelector(".yte-power-select-trigger-input");
if(!vals().includes(ibanNorm)&&norm(ibanInput?.value)!==ibanNorm)throw Error("Excel IBAN'ı MYS formunda doğrulanamadı");
return {needsIbanCommit:forceIbanReset||!vals().includes(ibanNorm)};})()