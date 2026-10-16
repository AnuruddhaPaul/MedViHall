<#
Watchdog for the second (parallel) Pillar D calibration instance.

Polls system RAM usage and GPU VRAM free% every $IntervalSec seconds. If either
threshold is breached, kills ONLY the second instance (matched by CommandLine
containing $MatchPattern, e.g. "llava16") via Stop-Process / taskkill -- the
first instance (qwen25vl, running in the user's own terminal) is never touched
since it won't match the pattern.

Exits on its own once the target process is no longer found (either because
it finished naturally, or because this script killed it).
#>
param(
    [double]$RamLimitGB = 30,
    [double]$VramWarnPctLimit = 4,
    [double]$VramFreePctLimit = 1,
    [double]$IntervalSec = 2.5,
    [string]$MatchPattern = 'llava16'
)

$logFile = "medvihall_outputs/watchdog_log.txt"

function Log($msg) {
    $line = "$(Get-Date -Format o) $msg"
    Add-Content -Path $logFile -Value $line
    Write-Output $line
}

Log "Watchdog started. RAM limit=${RamLimitGB}GB, VRAM warn<${VramWarnPctLimit}%, VRAM kill<${VramFreePctLimit}%, poll=${IntervalSec}s, matching '$MatchPattern'"
$warned = $false

while ($true) {
    $procs = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
        Where-Object { $_.CommandLine -match [regex]::Escape($MatchPattern) }

    if (-not $procs) {
        Log "Target process (matching '$MatchPattern') not found -- waiting for it to start (or it already ended)..."
        Start-Sleep -Seconds $IntervalSec
        continue
    }

    $targetPid = ($procs | Select-Object -First 1).ProcessId
    $alive = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
    if (-not $alive) {
        Log "Target process PID $targetPid no longer running. Watchdog exiting."
        break
    }

    $os = Get-CimInstance Win32_OperatingSystem
    $usedGB = ($os.TotalVisibleMemorySize - $os.FreePhysicalMemory) / 1MB

    $nvOut = & nvidia-smi --query-gpu=memory.total,memory.free --format=csv,noheader,nounits
    $parts = $nvOut -split ',\s*'
    $vramTotal = [double]$parts[0]
    $vramFree = [double]$parts[1]
    $vramFreePct = ($vramFree / $vramTotal) * 100

    Log ("Check: targetPID=$targetPid RAM_used={0:N1}GB VRAM_free={1:N1}% ({2:N0}MiB/{3:N0}MiB)" -f $usedGB, $vramFreePct, $vramFree, $vramTotal)

    if ($usedGB -gt $RamLimitGB -or $vramFreePct -lt $VramFreePctLimit) {
        Log "KILL THRESHOLD BREACHED (RAM_used=${usedGB}GB limit=$RamLimitGB | VRAM_free=${vramFreePct}% kill-floor=$VramFreePctLimit). Killing target PID $targetPid ..."
        Stop-Process -Id $targetPid -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 3
        $stillAlive = Get-Process -Id $targetPid -ErrorAction SilentlyContinue
        if ($stillAlive) {
            Log "PID $targetPid still alive after Stop-Process, retrying with taskkill /F"
            taskkill /PID $targetPid /F | Out-Null
        }
        Log "Second instance (PID $targetPid) killed. First instance is untouched. Watchdog exiting."
        break
    }
    elseif ($vramFreePct -lt $VramWarnPctLimit) {
        if (-not $warned) {
            Log "WARNING: VRAM_free=${vramFreePct}% below warn-floor=$VramWarnPctLimit% (kill-floor is $VramFreePctLimit%) -- watching closely."
            $warned = $true
        }
    }
    else {
        $warned = $false
    }

    Start-Sleep -Seconds $IntervalSec
}

Log "Watchdog stopped."
