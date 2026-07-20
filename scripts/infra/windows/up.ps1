param(
    [string]$EnvFile = ".env.windows",
    [switch]$DebugPorts,
    [switch]$Build,
    [ValidateSet("frontend", "backend", "ai-service", "postgres", "redis")]
    [string]$BuildService,
    [switch]$FullPreflight
)

. (Join-Path $PSScriptRoot "_common.ps1")
$context = Get-KinlinWindowsContext $EnvFile
if ($Build -and $BuildService) { throw "Use either -Build or -BuildService, not both" }
if ($FullPreflight) {
    & (Join-Path $PSScriptRoot "preflight.ps1") -EnvFile $context.EnvFile -Full
} else {
    & (Join-Path $PSScriptRoot "preflight.ps1") -EnvFile $context.EnvFile
}
$env:DOCKER_BUILDKIT = "1"
$env:COMPOSE_DOCKER_CLI_BUILD = "1"
Write-KinlinContext $context
if ($BuildService) {
    Write-Host "Building only $BuildService before starting the full development stack"
    Invoke-KinlinCompose $context build $BuildService
}
$arguments = @("up", "-d", "--wait")
if ($Build) { $arguments += "--build" }
if ($DebugPorts) { $arguments = @("--profile", "debug-ports") + $arguments }
Invoke-KinlinCompose $context @arguments
Write-Host "Windows development environment is ready at $($context.PublicOrigin)"
