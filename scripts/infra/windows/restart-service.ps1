param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("frontend", "backend", "ai-service", "postgres", "redis")]
    [string]$Service,
    [string]$EnvFile = ".env.windows",
    [switch]$FullRestart
)

. (Join-Path $PSScriptRoot "_common.ps1")
$context = Get-KinlinWindowsContext $EnvFile
Write-KinlinContext $context
if ($Service -eq "backend" -and -not $FullRestart) {
    $stopwatch = [System.Diagnostics.Stopwatch]::StartNew()
    Write-Host "Compiling Backend without tests; Spring Boot DevTools will restart the application"
    Invoke-KinlinCompose $context exec -T backend mvn -B -ntp -DskipTests compile
    Start-Sleep -Seconds 2
    Wait-KinlinServiceHealthy $context backend -TimeoutSeconds 120
    $stopwatch.Stop()
    Write-Host ("Backend feedback completed in {0:N2}s" -f $stopwatch.Elapsed.TotalSeconds)
} else {
    Invoke-KinlinCompose $context restart $Service
    Wait-KinlinServiceHealthy $context $Service
}
Invoke-KinlinCompose $context ps $Service
