$ErrorActionPreference = "Stop"

# CLI yolu boşluk içerse bile Node'a doğru argüman olarak iletip Allow & select'i aç.
$cli = $env:PLAYWRIGHT_CLI_JS
if([string]::IsNullOrWhiteSpace($cli) -or -not (Test-Path -LiteralPath $cli)) {
    throw "playwright-cli.js bulunamadı."
}
$arguments = '"' + $cli + '" attach --extension=chrome -s=chrome-main'
Start-Process -WindowStyle Hidden -FilePath "node" -ArgumentList $arguments
