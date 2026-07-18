param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("frontend", "backend", "ai-service", "postgres", "redis")]
    [string]$Service,
    [string]$EnvFile = ".env.windows"
)

. (Join-Path $PSScriptRoot "_common.ps1")
$context = Get-KinlinWindowsContext $EnvFile
Write-KinlinContext $context
Invoke-KinlinCompose $context restart $Service
Invoke-KinlinCompose $context ps $Service
