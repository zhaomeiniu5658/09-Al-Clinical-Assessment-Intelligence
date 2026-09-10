param(
    [string]$MySqlVolume,
    [string]$StorageVolume
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$mysqlTarget = Join-Path $projectRoot "data\mysql"
$storageTarget = Join-Path $projectRoot "data\storage"

function Test-DockerAvailable {
    docker info *> $null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker Desktop is not running. Start Docker Desktop and run this script again."
    }
}

function Resolve-VolumeName([string]$ExplicitName, [string]$LogicalName) {
    if ($ExplicitName) {
        docker volume inspect $ExplicitName *> $null
        if ($LASTEXITCODE -ne 0) {
            throw "Docker volume '$ExplicitName' does not exist."
        }
        return $ExplicitName
    }

    $matches = @(docker volume ls --filter "label=com.docker.compose.volume=$LogicalName" --format "{{.Name}}")
    $matches = @($matches | Where-Object { $_ })
    if ($matches.Count -eq 0) {
        throw "No old Docker volume was found for '$LogicalName'. Pass its name explicitly."
    }
    if ($matches.Count -gt 1) {
        throw "More than one '$LogicalName' volume was found: $($matches -join ', '). Pass the correct name explicitly."
    }
    return $matches[0]
}

function Assert-EmptyTarget([string]$Target) {
    New-Item -ItemType Directory -Force -Path $Target | Out-Null
    $existing = @(Get-ChildItem -Force -Path $Target | Where-Object { $_.Name -ne ".gitkeep" })
    if ($existing.Count -gt 0) {
        throw "Target directory is not empty: $Target. No files were changed."
    }
}

function Copy-Volume([string]$VolumeName, [string]$Target) {
    Write-Host "Copying '$VolumeName' to '$Target'..."
    docker run --rm `
        --mount "type=volume,source=$VolumeName,target=/from,readonly" `
        --mount "type=bind,source=$Target,target=/to" `
        alpine sh -c "cp -a /from/. /to/"
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to copy Docker volume '$VolumeName'."
    }
}

Test-DockerAvailable
Assert-EmptyTarget $mysqlTarget
Assert-EmptyTarget $storageTarget

$resolvedMySqlVolume = Resolve-VolumeName $MySqlVolume "mysql_data"
$resolvedStorageVolume = Resolve-VolumeName $StorageVolume "app_storage"

Push-Location $projectRoot
try {
    docker compose down
    if ($LASTEXITCODE -ne 0) {
        throw "Failed to stop the project containers."
    }

    Copy-Volume $resolvedMySqlVolume $mysqlTarget
    Copy-Volume $resolvedStorageVolume $storageTarget

    Write-Host "Migration completed. The old Docker volumes were kept as a backup."
    Write-Host "Start the project with: docker compose up -d --build"
}
finally {
    Pop-Location
}
