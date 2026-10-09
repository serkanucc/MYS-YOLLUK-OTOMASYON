
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$cfg = Get-Content "$root\config\runner-settings.json" -Raw | ConvertFrom-Json
& playwright-cli ("-s=" + [string]$cfg.browserSession) goto $($cfg.formUrl) | Out-Null
Start-Sleep -Milliseconds 900
$js = @'
(()=> {
  const labels=[...document.querySelectorAll("label.yte-form-label")].map(x=>x.title);
  const buttons=[...document.querySelectorAll("button")].map(x=>({text:x.innerText.trim(),disabled:x.disabled}));
  const ids=[...document.querySelectorAll("[id^=yte-form-element-id]")].map(x=>x.id);
  const submit=buttons.find(x=>x.text.includes("Yolluk Süreç Hazırlama"));
  return {labels,buttonCount:buttons.length,submitDisabled:submit?.disabled??null,idCount:ids.length};
})()
'@
$out = & playwright-cli ("-s=" + [string]$cfg.browserSession) eval $js 2>&1
if ($LASTEXITCODE -ne 0) { throw ($out | Out-String) }
$out | Select-String "### Result|labels|buttonCount|submitDisabled|idCount"
