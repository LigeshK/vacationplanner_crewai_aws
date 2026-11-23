# Build the vacation-planner image (arm64, for Bedrock AgentCore) and push it to ECR.
# Usage: .\deploy.ps1

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# --- Hardcoded deployment target ---
$ACCOUNT  = "248317805748"
$REGION   = "ap-southeast-2"
$REPO     = "vacation-planner"
$PLATFORM = "linux/arm64"
$REGISTRY = "$ACCOUNT.dkr.ecr.$REGION.amazonaws.com"
$IMAGE    = "$REGISTRY/${REPO}:latest"

function Invoke-Step([string]$Name, [scriptblock]$Cmd) {
    Write-Host "`n==> $Name" -ForegroundColor Cyan
    & $Cmd
    if ($LASTEXITCODE -ne 0) { throw "Step failed: $Name (exit $LASTEXITCODE)" }
}

# Run a native command only to see if it succeeds. Windows PowerShell 5.1 turns redirected
# stderr into a terminating error under "Stop", so relax it for the probe.
function Test-Native([scriptblock]$Cmd) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $Cmd *> $null } catch {}
    $ok = ($LASTEXITCODE -eq 0)
    $ErrorActionPreference = $prev
    return $ok
}

if (-not (Test-Path "models\qwen2.5-0.5b-instruct-q4_k_m.gguf")) {
    throw "Missing models\qwen2.5-0.5b-instruct-q4_k_m.gguf"
}

if (-not (Test-Native { docker info })) {
    throw "Docker daemon is not reachable. Start Docker Desktop (wait until it says 'Engine running') and re-run."
}

Write-Host "Pushing $IMAGE ($PLATFORM)"

# Create the ECR repository if it doesn't exist yet
if (-not (Test-Native { aws ecr describe-repositories --repository-names $REPO --region $REGION })) {
    Invoke-Step "Creating ECR repository $REPO" {
        aws ecr create-repository --repository-name $REPO --region $REGION `
            --image-scanning-configuration scanOnPush=true --output text --query repository.repositoryUri
    }
}

Invoke-Step "Logging in to ECR" {
    aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $REGISTRY
}

# buildx builder that can cross-build arm64 on an x86 PC
if (-not (Test-Native { docker buildx inspect multi })) {
    Invoke-Step "Creating buildx builder 'multi'" { docker buildx create --name multi --driver docker-container }
}

Invoke-Step "Building and pushing" {
    docker buildx build --builder multi --platform $PLATFORM -t $IMAGE --provenance=false --push .
}

Invoke-Step "Verifying image in ECR" {
    aws ecr describe-images --repository-name $REPO --region $REGION --image-ids imageTag=latest `
        --query "imageDetails[0].{pushed:imagePushedAt,digest:imageDigest}" --output table
}

Write-Host "`nPushed: $IMAGE" -ForegroundColor Green
