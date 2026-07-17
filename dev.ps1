param(
    [ValidateSet("up", "down", "build", "restart", "logs")]
    [string]$Action = "up"
)

$ErrorActionPreference = "Stop"
$composeFiles = @("-f", "compose.yaml", "-f", "compose.dev.yaml")

function Invoke-Compose {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$ComposeArgs)
    & docker compose @composeFiles @ComposeArgs
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed with exit code $LASTEXITCODE" }
}

if (-not $env:KINLIN_DEPLOYMENT_ID -or -not $env:KINLIN_SECRETS_DIR) {
    throw "Set KINLIN_DEPLOYMENT_ID and KINLIN_SECRETS_DIR before using dev.ps1"
}

if ($Action -in @("up", "build", "restart")) {
    python -m scripts.infra.preflight --deployment-id $env:KINLIN_DEPLOYMENT_ID --secrets-dir $env:KINLIN_SECRETS_DIR --bind-address 127.0.0.1
    if ($LASTEXITCODE -ne 0) { throw "Infrastructure preflight failed" }
}

switch ($Action) {
    "up"      { Invoke-Compose up -d --build --wait }
    "down"    { Invoke-Compose down }
    "build"   { Invoke-Compose build }
    "restart" { Invoke-Compose down; Invoke-Compose up -d --build --wait }
    "logs"    { Invoke-Compose logs -f --tail=100 }
}
