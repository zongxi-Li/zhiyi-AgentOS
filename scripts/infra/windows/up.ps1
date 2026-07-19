param(
    [string]$EnvFile = ".env.windows",
    [switch]$DebugPorts,
    [switch]$Build
)

. (Join-Path $PSScriptRoot "_common.ps1")
$context = Get-KinlinWindowsContext $EnvFile
& (Join-Path $PSScriptRoot "preflight.ps1") -EnvFile $context.EnvFile
if ($LASTEXITCODE -ne 0) { throw "Windows preflight failed" }
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"
Write-KinlinContext $context
$arguments = @("up", "-d", "--wait")
if ($Build) { $arguments += "--build" }
if ($DebugPorts) { $arguments = @("--profile", "debug-ports") + $arguments }
Invoke-KinlinCompose $context @arguments
Write-Host "Windows development environment is ready at http://127.0.0.1:$($context.HttpPort)"
