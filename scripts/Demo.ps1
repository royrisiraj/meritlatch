param(
    [ValidateSet('Preflight','Start','Status','Stop','Backup')][string]$Action = 'Start',
    [string]$RunRoot,
    [ValidateRange(0,65535)][int]$Port = 8018,
    [switch]$AcknowledgeCanned,
    [switch]$Resume,
    [switch]$OpenBrowser,
    [string]$PythonPath
)
$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
if (-not $PythonPath) { $PythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe' }
if (-not (Test-Path -LiteralPath $PythonPath -PathType Leaf)) {
    Write-Output 'PYTHON_ENVIRONMENT_REQUIRED: select an existing environment; nothing was installed.'
    exit 1
}
$taskArguments = @('-m','backend.tools.local_ops',$Action.ToLowerInvariant(),'--port',[string]$Port)
if ($RunRoot) { $taskArguments += @('--root',$RunRoot) }
if ($AcknowledgeCanned) { $taskArguments += @('--fixture','unsafe-then-valid','--acknowledge-canned') }
if ($Resume) { $taskArguments += '--resume' }
Push-Location -LiteralPath $projectRoot
try {
    $output = & $PythonPath @taskArguments
    $operationExit = $LASTEXITCODE
    $output | Write-Output
    if ($operationExit -eq 0 -and $OpenBrowser -and $Action -eq 'Start') {
        $result = $output | ConvertFrom-Json
        # Visible browser is explicitly requested by the operator's switch.
        Start-Process -FilePath $result.url -WindowStyle Normal | Out-Null
    }
    exit $operationExit
} finally { Pop-Location }
