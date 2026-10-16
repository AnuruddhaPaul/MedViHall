# Bridges the launcher that is already running (it loaded an older, shorter jobs list at start): once the
# contrastive job is finished and that launcher has exited, start a fresh launcher so it reads the full
# pipeline_jobs.txt (llava_med baseline rerun -> annotation list -> labeling -> Stage 4). Session-scoped helper;
# the SessionStart hook does the same thing after any restart.
$root = 'C:\Users\PC\Desktop\Programs\MediViHall'
$logDir = "$root\medvihall_outputs\pipeline_logs"
while ($true) {
    $lock = "$logDir\resume.lock"
    $held = $false
    if (Test-Path $lock) { $pid0 = Get-Content $lock -ErrorAction SilentlyContinue | Select-Object -First 1; if ($pid0 -and (Get-Process -Id ([int]$pid0) -ErrorAction SilentlyContinue)) { $held = $true } }
    if ((Test-Path "$logDir\pillar_b_contrastive.done") -and -not $held) { break }
    Start-Sleep -Seconds 60
}
Add-Content "$logDir\resume_status.log" ("{0} chain_watcher: contrastive finished, starting launcher for remaining jobs" -f (Get-Date -Format 's'))
Start-Process -FilePath powershell.exe -WindowStyle Hidden -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-WindowStyle','Hidden','-File',"$root\pipeline_resume.ps1"
