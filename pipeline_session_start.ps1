# Claude Code SessionStart hook for MediViHall.
# 1. If a pipeline job is unfinished and not running (interrupted by a VS Code close, crash or reboot),
#    start pipeline_resume.ps1 detached (the hook returns at once; the job resumes from its output file).
# 2. Tell Claude, as session context, what was interrupted/resumed and how far along it is.
# Nothing is installed on the machine: this only runs when a Claude session starts.
$ErrorActionPreference = 'SilentlyContinue'
$root   = 'C:\Users\PC\Desktop\Programs\MediViHall'
$logDir = "$root\medvihall_outputs\pipeline_logs"
Set-Location $root

$jobs = @(Get-Content "$root\pipeline_jobs.txt" | Where-Object { $_.Trim() -and -not $_.Trim().StartsWith('#') })
$pending = @()
foreach ($j in $jobs) {
    $name = [IO.Path]::GetFileNameWithoutExtension(($j -split '\s+')[1])
    if (-not (Test-Path "$logDir\$name.done")) { $pending += $name }
}

if ($pending.Count -eq 0) {
    $ctx = 'PIPELINE: every job in pipeline_jobs.txt is complete. Nothing to resume.'
    @{ systemMessage = $ctx; hookSpecificOutput = @{ hookEventName = 'SessionStart'; additionalContext = $ctx } } | ConvertTo-Json -Compress -Depth 4
    exit 0
}

$cmds = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" | ForEach-Object { $_.CommandLine })
$running = $false
foreach ($j in $jobs) { if ($cmds -match [regex]::Escape(($j -split '\s+')[1])) { $running = $true } }

$state = 'already running'
if (-not $running) {
    Start-Process -FilePath 'powershell.exe' -WindowStyle Hidden -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden', '-File', "$root\pipeline_resume.ps1"
    $state = 'was NOT running (interrupted); the resume launcher was just started'
}

$prog = @()
foreach ($row in @(Get-Content "$root\pipeline_progress.txt" | Where-Object { $_.Trim() -and -not $_.StartsWith('#') })) {
    $p = $row -split '\|'
    if ($pending -notcontains $p[0]) { continue }
    $f = Join-Path $root $p[1]
    if (-not (Test-Path $f)) { $prog += "$($p[0]): no output yet"; continue }
    $n = 0
    $fs = New-Object IO.FileStream($f, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
    $sr = New-Object IO.StreamReader($fs)
    while ($null -ne $sr.ReadLine()) { $n++ }
    $sr.Close(); $fs.Close()
    $last = (Get-Content $f -Tail 1 | ConvertFrom-Json).timestamp
    $ago = ''
    if ($last) { $d = (Get-Date).ToUniversalTime() - ([datetime]$last).ToUniversalTime(); $ago = ", last record {0:N1} h ago" -f $d.TotalHours }
    $prog += ("{0}: {1:N0}/{2:N0} ({3:P1}){4}" -f $p[0], $n, [int]$p[2], ($n / [int]$p[2]), $ago)
}

$ctx = "PIPELINE RESUME (automatic at every session start). Unfinished jobs: $($pending -join ', '). The job $state. Progress: $($prog -join '; '). " +
       "INSTRUCTION TO CLAUDE: in your first reply tell the user in two lines what was interrupted, whether it was resumed, and the progress. " +
       "Do not relaunch it yourself (the launcher does that and the job resumes from its output file); confirm with tasklist and the record count about two minutes later. " +
       "When a new stage is approved, add it to pipeline_jobs.txt and pipeline_progress.txt."
@{ systemMessage = "MediViHall pipeline: $($pending -join ', ') $state. $($prog -join '; ')"; hookSpecificOutput = @{ hookEventName = 'SessionStart'; additionalContext = $ctx } } | ConvertTo-Json -Compress -Depth 4
exit 0
