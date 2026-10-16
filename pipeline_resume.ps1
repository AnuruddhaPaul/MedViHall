# Auto-resume launcher for the MediViHall GPU pipeline.
# Run by the "MedViHall_Resume" scheduled task at logon and every 10 minutes. Safe to run any time:
# it exits at once if a pipeline job is already running or another launcher instance is active.
# Jobs are listed in pipeline_jobs.txt (one "python-path script [args]" per line, run in order, one at a time
# because two GPU models together collapse VRAM on this card). Every job script is resume-safe.
# A job that exits 0 gets a .done marker and is skipped later (delete the marker to rerun it).

$root   = 'C:\Users\PC\Desktop\Programs\MediViHall'
$logDir = Join-Path $root 'medvihall_outputs\pipeline_logs'
New-Item -ItemType Directory -Force $logDir | Out-Null
Set-Location $root
$status = Join-Path $logDir 'resume_status.log'
function Log($m) { Add-Content -Path $status -Value ('{0} {1}' -f (Get-Date -Format 's'), $m) }

# one launcher at a time
$lock = Join-Path $logDir 'resume.lock'
if (Test-Path $lock) {
    $old = (Get-Content $lock -ErrorAction SilentlyContinue | Select-Object -First 1)
    if ($old -and (Get-Process -Id ([int]$old) -ErrorAction SilentlyContinue)) { exit 0 }
}
Set-Content -Path $lock -Value $PID

$jobs = @(Get-Content (Join-Path $root 'pipeline_jobs.txt') | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') })
$scripts = @($jobs | ForEach-Object { ($_ -split '\s+')[1] })

# a job script already running (launched by hand, by Claude, or by an earlier launcher)? then do nothing
$cmds = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object { $_.CommandLine })
foreach ($s in $scripts) {
    if ($cmds -match [regex]::Escape($s)) { Log "skip: $s already running"; Remove-Item $lock -ErrorAction SilentlyContinue; exit 0 }
}

# wait for the GPU driver (after a reboot it can take a minute)
$gpuOk = $false
for ($i = 0; $i -lt 40; $i++) {
    & nvidia-smi --query-gpu=name --format=csv,noheader *> $null
    if ($LASTEXITCODE -eq 0) { $gpuOk = $true; break }
    Start-Sleep -Seconds 15
}
if (-not $gpuOk) { Log 'GPU not available after 10 min; giving up this round'; Remove-Item $lock -ErrorAction SilentlyContinue; exit 1 }

foreach ($j in $jobs) {
    $parts = $j.Trim() -split '\s+'
    $exe = $parts[0]; $script = $parts[1]; $jobArgs = @($parts | Select-Object -Skip 1)
    $name = [IO.Path]::GetFileNameWithoutExtension($script)
    $done = Join-Path $logDir "$name.done"
    if (Test-Path $done) { continue }
    $ok = $false
    for ($try = 1; $try -le 5; $try++) {
        Log "start $name (attempt $try)"
        $env:PYTHONUNBUFFERED = '1'
        $p = Start-Process -FilePath $exe -ArgumentList $jobArgs -WorkingDirectory $root -WindowStyle Hidden -PassThru -Wait `
             -RedirectStandardOutput (Join-Path $logDir "$name.out.log") -RedirectStandardError (Join-Path $logDir "$name.err.log")
        Log "$name exited with code $($p.ExitCode)"
        if ($p.ExitCode -eq 0) { $ok = $true; break }
        Start-Sleep -Seconds 60
    }
    if ($ok) { Set-Content -Path $done -Value (Get-Date -Format 's') } else { Log "$name FAILED 5 times; stopping chain"; break }
}
Remove-Item $lock -ErrorAction SilentlyContinue
