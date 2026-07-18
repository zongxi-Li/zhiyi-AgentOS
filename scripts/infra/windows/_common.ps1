Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$script:KinlinProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..\..\..")).Path
$script:KinlinComposeFiles = @(
    (Join-Path $script:KinlinProjectRoot "compose.yaml"),
    (Join-Path $script:KinlinProjectRoot "compose.dev.yaml"),
    (Join-Path $script:KinlinProjectRoot "compose.windows.yaml")
)

function Resolve-KinlinEnvFile {
    param([string]$EnvFile = ".env.windows")
    $candidate = if ([System.IO.Path]::IsPathRooted($EnvFile)) { $EnvFile } else { Join-Path $script:KinlinProjectRoot $EnvFile }
    if (-not (Test-Path -LiteralPath $candidate -PathType Leaf)) {
        throw "Windows environment file does not exist: $candidate"
    }
    return (Resolve-Path -LiteralPath $candidate).Path
}

function Read-KinlinWindowsEnv {
    param([string]$EnvFile = ".env.windows")
    $path = Resolve-KinlinEnvFile $EnvFile
    $values = @{}
    foreach ($line in Get-Content -LiteralPath $path -Encoding UTF8) {
        $trimmed = $line.Trim()
        if (-not $trimmed -or $trimmed.StartsWith("#")) { continue }
        $parts = $trimmed.Split("=", 2)
        if ($parts.Count -ne 2 -or $parts[0] -notmatch '^[A-Z][A-Z0-9_]*$') {
            throw "Invalid line in $path; only KEY=value entries are allowed"
        }
        $key = $parts[0]
        if ($key -ne "KINLIN_SECRETS_DIR" -and $key -match '(PASSWORD|TOKEN|SECRET|API_?KEY|JWT)') {
            throw "Sensitive key $key is forbidden in .env.windows"
        }
        $values[$key] = $parts[1]
    }
    return [PSCustomObject]@{ Path = $path; Values = $values }
}

function Get-KinlinWindowsContext {
    param([string]$EnvFile = ".env.windows")
    $envData = Read-KinlinWindowsEnv $EnvFile
    if (-not $envData.Values.ContainsKey("KINLIN_DEPLOYMENT_ID")) { throw "KINLIN_DEPLOYMENT_ID is required in $($envData.Path)" }
    if (-not $envData.Values.ContainsKey("KINLIN_SECRETS_DIR")) { throw "KINLIN_SECRETS_DIR is required in $($envData.Path)" }
    $deploymentId = $envData.Values["KINLIN_DEPLOYMENT_ID"]
    if ($deploymentId -notmatch '^[a-z0-9][a-z0-9-]{2,31}$') { throw "Invalid KINLIN_DEPLOYMENT_ID: $deploymentId" }
    $secretValue = $envData.Values["KINLIN_SECRETS_DIR"]
    $secretPath = if ([System.IO.Path]::IsPathRooted($secretValue)) { $secretValue } else { Join-Path $script:KinlinProjectRoot $secretValue }
    $httpPort = if ($envData.Values.ContainsKey("KINLIN_HTTP_PORT")) { [int]$envData.Values["KINLIN_HTTP_PORT"] } else { 8080 }
    return [PSCustomObject]@{
        ProjectRoot = $script:KinlinProjectRoot
        EnvFile = $envData.Path
        DeploymentId = $deploymentId
        SecretsDir = [System.IO.Path]::GetFullPath($secretPath)
        HttpPort = $httpPort
        ComposeFiles = $script:KinlinComposeFiles
    }
}

function Get-KinlinComposeArguments {
    param($Context)
    $arguments = @()
    foreach ($file in $Context.ComposeFiles) { $arguments += @("-f", $file) }
    $arguments += @("--env-file", $Context.EnvFile)
    return $arguments
}

function Write-KinlinContext {
    param($Context)
    $dockerContext = (& docker context show).Trim()
    if ($LASTEXITCODE -ne 0) { throw "Unable to read Docker context" }
    Write-Host "KINLIN_DEPLOYMENT_ID=$($Context.DeploymentId)"
    Write-Host "Docker context=$dockerContext"
    Write-Host "Compose files:"
    foreach ($file in $Context.ComposeFiles) { Write-Host "  $file" }
}

function Invoke-KinlinCompose {
    param(
        $Context,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$ComposeArgs
    )
    $baseArgs = Get-KinlinComposeArguments $Context
    Push-Location $Context.ProjectRoot
    try {
        & docker compose @baseArgs @ComposeArgs
        if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed with exit code $LASTEXITCODE" }
    } finally {
        Pop-Location
    }
}

function Get-KinlinServiceContainerId {
    param($Context, [string]$Service)
    $baseArgs = Get-KinlinComposeArguments $Context
    Push-Location $Context.ProjectRoot
    try {
        $containerId = (& docker compose @baseArgs ps -q $Service).Trim()
        if ($LASTEXITCODE -ne 0 -or -not $containerId) { throw "Service is not running: $Service" }
        return $containerId
    } finally {
        Pop-Location
    }
}

function Get-KinlinWslOutput {
    param([Parameter(Mandatory = $true)][string]$Arguments)
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new()
    $startInfo.FileName = "wsl.exe"
    $startInfo.Arguments = $Arguments
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.RedirectStandardOutput = $true
    $startInfo.RedirectStandardError = $true
    $startInfo.StandardOutputEncoding = [System.Text.Encoding]::Unicode
    $startInfo.StandardErrorEncoding = [System.Text.Encoding]::Unicode
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $stdout = $process.StandardOutput.ReadToEnd()
    $stderr = $process.StandardError.ReadToEnd()
    $process.WaitForExit()
    if ($process.ExitCode -ne 0) { throw "wsl.exe $Arguments failed: $stderr" }
    return $stdout.Trim()
}
