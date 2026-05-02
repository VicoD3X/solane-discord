param(
  [string]$HostName = "root@178.104.165.186",
  [string]$RemoteBase = "/srv/solane-run",
  [string]$EnvPath = ".env",
  [switch]$AllowDirty,
  [switch]$SkipChecks
)

$ErrorActionPreference = "Stop"

function Invoke-Step {
  param([string]$Title, [scriptblock]$Command)
  Write-Host ""
  Write-Host "== $Title ==" -ForegroundColor Cyan
  & $Command
}

function Invoke-External {
  param(
    [string]$FilePath,
    [string[]]$Arguments,
    [string]$WorkingDirectory = (Get-Location).Path
  )
  Push-Location $WorkingDirectory
  try {
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
      throw "$FilePath exited with code $LASTEXITCODE"
    }
  }
  finally {
    Pop-Location
  }
}

function Assert-CleanGit {
  param([string]$RepoPath)
  if ($AllowDirty) {
    Write-Host "AllowDirty enabled for $RepoPath" -ForegroundColor Yellow
    return
  }
  $status = git -C $RepoPath status --porcelain
  if ($status) {
    Write-Host $status
    throw "Refusing to deploy dirty repository: $RepoPath"
  }
}

function Read-DotEnv {
  param([string]$Path)
  $values = @{}
  foreach ($line in Get-Content -LiteralPath $Path) {
    $trimmed = $line.Trim()
    if ($trimmed.Length -eq 0 -or $trimmed.StartsWith("#")) {
      continue
    }
    $index = $trimmed.IndexOf("=")
    if ($index -lt 1) {
      continue
    }
    $key = $trimmed.Substring(0, $index).Trim()
    $value = $trimmed.Substring($index + 1).Trim()
    $values[$key] = $value
  }
  return $values
}

$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$envFile = Resolve-Path (Join-Path $repo $EnvPath)
$envValues = Read-DotEnv -Path $envFile.Path
if (-not $envValues["DISCORD_TOKEN"]) {
  throw "DISCORD_TOKEN is missing from $($envFile.Path)."
}

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$commit = (git -C $repo rev-parse --short HEAD).Trim()
$tempRoot = Join-Path ([System.IO.Path]::GetTempPath()) "solane-bot-deploy-$timestamp"
$archive = Join-Path $tempRoot "solane-bot-$timestamp.tar.gz"
$remoteEnv = Join-Path $tempRoot "solane-bot.env"
$remoteScriptPath = Join-Path $tempRoot "remote-bot-deploy.sh"
$remoteArchive = "/tmp/solane-bot-$timestamp.tar.gz"
$remoteEnvPath = "/tmp/solane-bot-$timestamp.env"
$remoteScript = "/tmp/solane-bot-deploy-$timestamp.sh"

New-Item -ItemType Directory -Force -Path $tempRoot | Out-Null

$remoteEnvLines = @(
  "DISCORD_TOKEN=$($envValues["DISCORD_TOKEN"])",
  "DISCORD_APPLICATION_ID=$($envValues["DISCORD_APPLICATION_ID"])",
  "DISCORD_PUBLIC_KEY=$($envValues["DISCORD_PUBLIC_KEY"])",
  "SOLANE_API_BASE_URL=http://solane-api:8000",
  "SOLANE_BOT_API_KEY=$($envValues["SOLANE_BOT_API_KEY"])",
  "DISCORD_RISK_CHANNEL_ID=$($envValues["DISCORD_RISK_CHANNEL_ID"])",
  "DISCORD_CORRUPTION_CHANNEL_ID=$($envValues["DISCORD_CORRUPTION_CHANNEL_ID"])",
  "DISCORD_SERVICE_CHANNEL_ID=$($envValues["DISCORD_SERVICE_CHANNEL_ID"])",
  "BOT_POLL_SECONDS=$($envValues["BOT_POLL_SECONDS"])",
  "BOT_STATE_PATH=$($envValues["BOT_STATE_PATH"])",
  "BOT_LOG_LEVEL=$($envValues["BOT_LOG_LEVEL"])"
)
[System.IO.File]::WriteAllLines($remoteEnv, $remoteEnvLines, [System.Text.UTF8Encoding]::new($false))

try {
  Invoke-Step "Preflight" {
    Assert-CleanGit $repo
    Write-Host "Bot commit: $commit"
    Invoke-External "ssh" @("-o", "BatchMode=yes", "-o", "ConnectTimeout=10", $HostName, "whoami >/dev/null && docker --version >/dev/null && docker compose version >/dev/null")
  }

  if (-not $SkipChecks) {
    Invoke-Step "Bot checks" {
      Invoke-External ".venv\Scripts\python.exe" @("-m", "ruff", "check", ".") $repo
      Invoke-External ".venv\Scripts\python.exe" @("-m", "pytest") $repo
      Invoke-External ".venv\Scripts\python.exe" @("-m", "compileall", "-q", "solane_ai", "tests") $repo
      Invoke-External "docker" @("compose", "config", "--quiet") $repo
    }
  } else {
    Write-Host "SkipChecks enabled; local verification skipped." -ForegroundColor Yellow
  }

  Invoke-Step "Create archive" {
    Invoke-External "git" @("-C", $repo, "archive", "--format=tar.gz", "-o", $archive, "HEAD")
  }

  $remoteDeploy = @'
set -euo pipefail

BASE="$1"
ARCHIVE="$2"
ENV_UPLOAD="$3"
TS="$4"
COMMIT="$5"
LOCK="$BASE/bot-deploy.lock"
BOT_ENV="$BASE/shared/solane-bot.env"

cleanup() {
  rm -rf "$LOCK"
}

rollback() {
  echo "Bot deployment failed; attempting rollback..." >&2
  set +e
  if [ -d "$BASE/repo/bot.previous" ]; then
    rm -rf "$BASE/repo/bot.failed-$TS"
    [ -d "$BASE/repo/bot" ] && mv "$BASE/repo/bot" "$BASE/repo/bot.failed-$TS"
    mv "$BASE/repo/bot.previous" "$BASE/repo/bot"
    cd "$BASE/repo/bot" && docker compose -p solane-bot --env-file "$BOT_ENV" up -d
  fi
}

if ! mkdir "$LOCK" 2>/dev/null; then
  echo "Another bot deployment is already running: $LOCK" >&2
  exit 1
fi
trap cleanup EXIT
trap rollback ERR

mkdir -p "$BASE/releases/$TS" "$BASE/backups" "$BASE/repo" "$BASE/shared"
install -m 600 "$ENV_UPLOAD" "$BOT_ENV"
cp "$ARCHIVE" "$BASE/releases/$TS/bot-$COMMIT.tar.gz"

rm -rf "$BASE/repo/bot.new"
mkdir -p "$BASE/repo/bot.new"
tar -xzf "$BASE/releases/$TS/bot-$COMMIT.tar.gz" -C "$BASE/repo/bot.new"

test -f "$BASE/repo/bot.new/docker-compose.yml"
test -f "$BASE/repo/bot.new/Dockerfile"

rm -rf "$BASE/repo/bot.previous"
[ -d "$BASE/repo/bot" ] && mv "$BASE/repo/bot" "$BASE/repo/bot.previous"
mv "$BASE/repo/bot.new" "$BASE/repo/bot"
install -m 600 "$BOT_ENV" "$BASE/repo/bot/.env"

if ! docker network inspect solane-run >/dev/null 2>&1; then
  docker network create solane-run >/dev/null
fi

cd "$BASE/repo/bot"
docker compose -p solane-bot --env-file "$BOT_ENV" build

for attempt in $(seq 1 20); do
  if docker compose -p solane-bot --env-file "$BOT_ENV" run --rm --no-deps bot python - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("http://solane-api:8000/health", timeout=5) as response:
    payload = json.load(response)

raise SystemExit(0 if payload.get("service") == "solane-engine" else 1)
PY
  then
    break
  fi
  if [ "$attempt" -eq 20 ]; then
    echo "Solane Engine is not reachable from Docker network." >&2
    exit 1
  fi
  sleep 2
done

docker compose -p solane-bot --env-file "$BOT_ENV" up -d

for attempt in $(seq 1 20); do
  if docker compose -p solane-bot --env-file "$BOT_ENV" ps --status running --services | grep -qx bot; then
    break
  fi
  if [ "$attempt" -eq 20 ]; then
    echo "Bot container did not stay running." >&2
    docker compose -p solane-bot --env-file "$BOT_ENV" logs --tail=120 bot >&2
    exit 1
  fi
  sleep 2
done

for attempt in $(seq 1 20); do
  if docker compose -p solane-bot --env-file "$BOT_ENV" logs --since 2m bot | grep -q 'GET http://solane-api:8000/api/eve/status "HTTP/1.1 200 OK"'; then
    break
  fi
  if [ "$attempt" -eq 20 ]; then
    echo "Bot did not confirm a fresh Solane Engine status fetch." >&2
    docker compose -p solane-bot --env-file "$BOT_ENV" logs --tail=120 bot >&2
    exit 1
  fi
  sleep 2
done

docker compose -p solane-bot --env-file "$BOT_ENV" ps
docker compose -p solane-bot --env-file "$BOT_ENV" logs --tail=80 bot

echo "Solane Discord bot deploy complete"
'@
  [System.IO.File]::WriteAllText($remoteScriptPath, ($remoteDeploy -replace "`r`n", "`n"), [System.Text.UTF8Encoding]::new($false))

  Invoke-Step "Upload" {
    Invoke-External "scp" @($archive, "${HostName}:$remoteArchive")
    Invoke-External "scp" @($remoteEnv, "${HostName}:$remoteEnvPath")
    Invoke-External "scp" @($remoteScriptPath, "${HostName}:$remoteScript")
  }

  Invoke-Step "Deploy bot on VPS" {
    Invoke-External "ssh" @($HostName, "chmod +x $remoteScript && bash $remoteScript '$RemoteBase' '$remoteArchive' '$remoteEnvPath' '$timestamp' '$commit'")
  }
}
finally {
  if (Test-Path -LiteralPath $tempRoot) {
    Remove-Item -LiteralPath $tempRoot -Recurse -Force
  }
}
