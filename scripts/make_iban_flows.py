from pathlib import Path
p=Path("scripts/stage1-flow.js")
s=p.read_text(encoding="utf-8")
m='await retrySelect("Yolluk Tipi"'
i=s.index(m)
pre=s[:i]+'return {needsIbanCommit:true};})()'
Path("scripts/stage1-flow-pre.js").write_text(pre,encoding="utf-8")
k=s.index("const forceIbanReset")
helpers=s[:k].replace("const forceIbanReset={{FORCE_IBAN}};","")
body=s[i:]
post=helpers+'const daily="{{DAILY}}",amirTckn="{{AMIR_TCKN}}";'+body
Path("scripts/stage1-flow-post.js").write_text(post,encoding="utf-8")
print(len(pre),len(post))
