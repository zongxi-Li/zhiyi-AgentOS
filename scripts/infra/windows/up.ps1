param(
    [string]$EnvFile = ".env.windows",
    [switch]$DebugPorts
)

. (Join-Path $PSScriptRoot "_common.ps1")
$context = Get-KinlinWindowsContext $EnvFile
& (Join-Path $PSScriptRoot "preflight.ps1") -EnvFile $context.EnvFile
if ($LASTEXITCODE -ne 0) { throw "Windows preflight failed" }
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"
Write-KinlinContext $context
$arguments = @("up", "-d", "--build", "--wait")
if ($DebugPorts) { $arguments = @("--profile", "debug-ports") + $arguments }
Invoke-KinlinCompose $context @arguments
