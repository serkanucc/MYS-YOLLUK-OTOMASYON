Add-Type -AssemblyName UIAutomationClient
Add-Type -AssemblyName UIAutomationTypes

$root = [System.Windows.Automation.AutomationElement]::RootElement
$wc = New-Object System.Windows.Automation.PropertyCondition(
    [System.Windows.Automation.AutomationElement]::ControlTypeProperty,
    [System.Windows.Automation.ControlType]::Window
)
$windows = $root.FindAll([System.Windows.Automation.TreeScope]::Children, $wc)
$found = $false

foreach($w in $windows) {
    if($w.Current.Name -match 'Google Chrome') {
        $all = $w.FindAll(
            [System.Windows.Automation.TreeScope]::Descendants,
            [System.Windows.Automation.Condition]::TrueCondition
        )
        foreach($x in $all) {
            if($x.Current.ControlType -eq [System.Windows.Automation.ControlType]::TabItem -and
               $x.Current.Name -match 'Playwright.*playwright-cli grubu') {
                $found = $true
                break
            }
        }
        if($found) { break }
    }
}

# Chrome'daki yeşil grup, kullanıcı Allow & select adımını tamamlayınca görünür.
if($found) { '1' } else { '0' }
