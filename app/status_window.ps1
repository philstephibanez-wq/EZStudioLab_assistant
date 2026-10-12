param(
    [string]$Root = "C:\EZStudioLab_assistant"
)

$ErrorActionPreference = "Stop"
Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$statusPath = Join-Path $Root "logs\assistant.status.json"
$commitPath = Join-Path $Root "DEPLOYED_COMMIT.txt"

$form = New-Object System.Windows.Forms.Form
$form.Text = "EZStudioLab Assistant"
$form.Size = New-Object System.Drawing.Size(420, 245)
$form.MinimumSize = $form.Size
$form.MaximumSize = $form.Size
$form.StartPosition = "CenterScreen"
$form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::FixedDialog
$form.MaximizeBox = $false

$title = New-Object System.Windows.Forms.Label
$title.Text = "EZStudioLab Assistant"
$title.Font = New-Object System.Drawing.Font("Segoe UI", 14, [System.Drawing.FontStyle]::Bold)
$title.Location = New-Object System.Drawing.Point(18, 15)
$title.AutoSize = $true
$form.Controls.Add($title)

$stateLabel = New-Object System.Windows.Forms.Label
$stateLabel.Text = "ARRÊTÉ"
$stateLabel.Font = New-Object System.Drawing.Font("Segoe UI", 12, [System.Drawing.FontStyle]::Bold)
$stateLabel.Location = New-Object System.Drawing.Point(18, 55)
$stateLabel.AutoSize = $true
$form.Controls.Add($stateLabel)

$activityLabel = New-Object System.Windows.Forms.Label
$activityLabel.Text = "Assistant arrêté"
$activityLabel.Font = New-Object System.Drawing.Font("Segoe UI", 10)
$activityLabel.Location = New-Object System.Drawing.Point(18, 86)
$activityLabel.Size = New-Object System.Drawing.Size(370, 45)
$form.Controls.Add($activityLabel)

$versionLabel = New-Object System.Windows.Forms.Label
$versionLabel.Text = "Version : -"
$versionLabel.Location = New-Object System.Drawing.Point(18, 139)
$versionLabel.AutoSize = $true
$form.Controls.Add($versionLabel)

$contactLabel = New-Object System.Windows.Forms.Label
$contactLabel.Text = "Dernier contact : -"
$contactLabel.Location = New-Object System.Drawing.Point(18, 164)
$contactLabel.AutoSize = $true
$form.Controls.Add($contactLabel)

$noteLabel = New-Object System.Windows.Forms.Label
$noteLabel.Text = "Le bouton [X] masque cette fenêtre ; le worker continue."
$noteLabel.ForeColor = [System.Drawing.Color]::DimGray
$noteLabel.Location = New-Object System.Drawing.Point(18, 190)
$noteLabel.AutoSize = $true
$form.Controls.Add($noteLabel)

$notify = New-Object System.Windows.Forms.NotifyIcon
$notify.Icon = [System.Drawing.SystemIcons]::Information
$notify.Text = "EZStudioLab Assistant"
$notify.Visible = $true

$menu = New-Object System.Windows.Forms.ContextMenuStrip
$showItem = New-Object System.Windows.Forms.ToolStripMenuItem
$showItem.Text = "Afficher EZStudioLab Assistant"
[void]$menu.Items.Add($showItem)
$notify.ContextMenuStrip = $menu

$showWindow = {
    $form.Show()
    $form.WindowState = [System.Windows.Forms.FormWindowState]::Normal
    $form.ShowInTaskbar = $true
    $form.Activate()
}
$showItem.Add_Click($showWindow)
$notify.Add_DoubleClick($showWindow)

$form.Add_FormClosing({
    param($sender, $e)
    if ($e.CloseReason -eq [System.Windows.Forms.CloseReason]::UserClosing) {
        $e.Cancel = $true
        $form.Hide()
        $form.ShowInTaskbar = $false
        $notify.ShowBalloonTip(
            1200,
            "EZStudioLab Assistant",
            "Fenêtre masquée. Le worker continue de fonctionner.",
            [System.Windows.Forms.ToolTipIcon]::Info
        )
    }
})

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = 1000
$timer.Add_Tick({
    $payload = $null
    try {
        if (Test-Path -LiteralPath $statusPath -PathType Leaf) {
            $payload = Get-Content -LiteralPath $statusPath -Raw -Encoding UTF8 | ConvertFrom-Json
        }
    } catch {
        $payload = $null
    }

    $commit = "-"
    if (Test-Path -LiteralPath $commitPath -PathType Leaf) {
        $rawCommit = (Get-Content -LiteralPath $commitPath -Raw -Encoding UTF8).Trim()
        if ($rawCommit.Length -gt 12) { $commit = $rawCommit.Substring(0, 12) }
        elseif ($rawCommit) { $commit = $rawCommit }
    }
    $versionLabel.Text = "Version : $commit"

    if ($null -eq $payload) {
        $stateLabel.Text = "ARRÊTÉ"
        $activityLabel.Text = "Assistant arrêté"
        $contactLabel.Text = "Dernier contact : -"
        $notify.Text = "EZStudioLab Assistant - ARRÊTÉ"
        return
    }

    $state = [string]$payload.state
    $activity = [string]$payload.activity
    try { $epoch = [double]$payload.at_epoch } catch { $epoch = 0.0 }
    $now = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds() / 1000.0
    $age = [math]::Max(0, $now - $epoch)

    if ($state -eq "STOPPED") {
        $displayState = "ARRÊTÉ"
    } elseif ($state -eq "ERROR") {
        $displayState = "ERREUR"
    } elseif ($age -gt 15) {
        $displayState = "PÉRIMÉ"
        $activity = "Aucun heartbeat récent"
    } elseif ($state -in @("BUSY", "CLAIMED", "PROCESSING")) {
        $displayState = "OCCUPÉ"
    } else {
        $displayState = "EN LIGNE"
    }

    if ([string]::IsNullOrWhiteSpace($activity)) { $activity = "En veille" }

    $stateLabel.Text = $displayState
    $activityLabel.Text = $activity
    $contactLabel.Text = "Dernier contact : $([math]::Floor($age)) s"
    $notify.Text = "EZStudioLab Assistant - $displayState"
})
$timer.Start()

try {
    [void]$form.ShowDialog()
} finally {
    $timer.Stop()
    $notify.Visible = $false
    $notify.Dispose()
    $menu.Dispose()
    $form.Dispose()
}
