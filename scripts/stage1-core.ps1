# MYS Yolluk Aşama 1 çekirdek güvenlik yardımcıları
$ErrorActionPreference = 'Stop'

function Normalize-Number($v) {
  if ($null -eq $v) { return $null }
  $s = ([string]$v).Trim()
  if ($s -eq '' -or $s -eq '0') { return $null }
  $n = 0
  if ([int]::TryParse($s, [ref]$n)) { return $n }
  return $null
}

function Resolve-FallbackValue($mysValue, $excelValue) {
  $m = Normalize-Number $mysValue
  if ($null -ne $m) { return @{ Value=$m; Source='MYS' } }
  $e = Normalize-Number $excelValue
  if ($null -ne $e) { return @{ Value=$e; Source='EXCEL_FALLBACK' } }
  return @{ Value=$null; Source='MISSING' }
}

function Resolve-PersonnelReference($mysDegree,$mysStep,$mysIndicator,$excelDegree,$excelStep,$excelIndicator) {
  $d = Resolve-FallbackValue $mysDegree $excelDegree
  $k = Resolve-FallbackValue $mysStep $excelStep
  $e = Resolve-FallbackValue $mysIndicator $excelIndicator
  if ($null -eq $d.Value -or $null -eq $k.Value -or $null -eq $e.Value) {
    throw 'Gündelik Tipi için Derece/Kademe/Ek Gösterge verisi eksik.'
  }
  return [pscustomobject]@{ Degree=$d.Value; Step=$k.Value; Indicator=$e.Value; DegreeSource=$d.Source; StepSource=$k.Source; IndicatorSource=$e.Source }
}

# Canlı gönderim burada yapılmaz. Bu dosya veri güvenliği ve karar kurallarını taşır.
