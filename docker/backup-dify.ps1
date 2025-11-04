# Dify Backup Script for Windows PowerShell
# Создает резервную копию всех данных Dify

param(
    [switch]$NoArchive,
    [switch]$SkipOldCleanup
)

$ErrorActionPreference = "Stop"

# Конфигурация
$BACKUP_ROOT = ".\backups"
$TIMESTAMP = Get-Date -Format "yyyyMMdd_HHmmss"
$BACKUP_DIR = "$BACKUP_ROOT\dify_backup_$TIMESTAMP"

Write-Host "=== Dify Backup Script ===" -ForegroundColor Green
Write-Host "Начало резервного копирования: $(Get-Date)" -ForegroundColor Yellow
Write-Host ""

# Создаем директорию для бэкапа
Write-Host "[1/7] Создание директории для бэкапа..." -ForegroundColor Green
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR\config" | Out-Null
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR\database" | Out-Null
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR\volumes" | Out-Null
New-Item -ItemType Directory -Force -Path "$BACKUP_DIR\logs" | Out-Null

# 1. Backup конфигурации
Write-Host "[2/7] Копирование конфигурационных файлов..." -ForegroundColor Green
if (Test-Path ".env") {
    Copy-Item ".env" "$BACKUP_DIR\config\.env" -Force
    Write-Host "✓ .env скопирован"
} else {
    Write-Host "⚠ Warning: .env not found" -ForegroundColor Yellow
}

if (Test-Path ".env.example") {
    Copy-Item ".env.example" "$BACKUP_DIR\config\.env.example" -Force
}

Copy-Item "docker-compose.yaml" "$BACKUP_DIR\config\docker-compose.yaml" -Force
Write-Host "✓ docker-compose.yaml скопирован"

# 2. Backup PostgreSQL database
Write-Host "[3/7] Создание дампа базы данных PostgreSQL..." -ForegroundColor Green
$dbStatus = docker compose ps db --format json | ConvertFrom-Json
if ($dbStatus.State -eq "running") {
    $DB_USER = (Select-String -Path ".env" -Pattern "^DB_USERNAME=(.+)$").Matches.Groups[1].Value
    $DB_NAME = (Select-String -Path ".env" -Pattern "^DB_DATABASE=(.+)$").Matches.Groups[1].Value
    
    Write-Host "Создание дампа базы '$DB_NAME'..."
    docker compose exec -T db pg_dump -U $DB_USER $DB_NAME | gzip > "$BACKUP_DIR\database\dify_db_$TIMESTAMP.sql.gz"
    Write-Host "✓ Database dump created: dify_db_$TIMESTAMP.sql.gz"
} else {
    Write-Host "⚠ Warning: PostgreSQL container not running" -ForegroundColor Yellow
}

# 3. Backup Redis data
Write-Host "[4/7] Создание дампа Redis..." -ForegroundColor Green
$redisStatus = docker compose ps redis --format json | ConvertFrom-Json
if ($redisStatus.State -eq "running") {
    docker compose exec -T redis redis-cli save
    Start-Sleep -Seconds 2
    if (Test-Path ".\volumes\redis\data\dump.rdb") {
        Copy-Item ".\volumes\redis\data\dump.rdb" "$BACKUP_DIR\database\redis_dump_$TIMESTAMP.rdb" -Force
        Write-Host "✓ Redis dump created"
    } else {
        Write-Host "⚠ Warning: Redis dump not found" -ForegroundColor Yellow
    }
} else {
    Write-Host "⚠ Warning: Redis container not running" -ForegroundColor Yellow
}

# 4. Backup Weaviate vector database
Write-Host "[5/7] Копирование данных Weaviate (векторная БД)..." -ForegroundColor Green
if (Test-Path ".\volumes\weaviate") {
    Write-Host "Copying Weaviate data (this may take a while)..."
    Copy-Item ".\volumes\weaviate" "$BACKUP_DIR\volumes\weaviate" -Recurse -Force
    Write-Host "✓ Weaviate data copied"
} else {
    Write-Host "⚠ Warning: Weaviate directory not found" -ForegroundColor Yellow
}

# 5. Backup uploaded files and storage
Write-Host "[6/7] Копирование загруженных файлов..." -ForegroundColor Green
if (Test-Path ".\volumes\app\storage") {
    Write-Host "Copying storage data..."
    Copy-Item ".\volumes\app\storage" "$BACKUP_DIR\volumes\storage" -Recurse -Force
    Write-Host "✓ Storage data copied"
} else {
    Write-Host "⚠ Warning: Storage directory not found" -ForegroundColor Yellow
}

# 6. Backup plugin data
if (Test-Path ".\volumes\plugin_daemon") {
    Write-Host "Copying plugin data..."
    # Use robocopy to skip problematic symlinks
    robocopy ".\volumes\plugin_daemon" "$BACKUP_DIR\volumes\plugin_daemon" /E /R:1 /W:1 /NP /NFL /NDL /NC /NS | Out-Null
    if ($LASTEXITCODE -lt 8) {
        Write-Host "✓ Plugin data copied"
    } else {
        Write-Host "⚠ Warning: Some plugin files may be skipped" -ForegroundColor Yellow
    }
}

# 7. Создание README
Write-Host "[7/7] Создание информационного файла..." -ForegroundColor Green
$dockerComposeVersion = docker compose version --short 2>$null
$readmeContent = @"
# Dify Backup - $TIMESTAMP

## Backup Information
- Date: $(Get-Date)
- Dify Version: 1.9.2
- Hostname: $env:COMPUTERNAME
- Docker Compose Version: $dockerComposeVersion

## Contents
- ``config/`` - Configuration files (.env, docker-compose.yaml)
- ``database/`` - PostgreSQL and Redis dumps
- ``volumes/`` - Persistent data (Weaviate, storage, plugins)

## Restore Instructions (PowerShell)

### 1. Stop Dify services
``````powershell
cd C:\Users\Andrey\dify\docker
docker compose down
``````

### 2. Restore configuration
``````powershell
Copy-Item config\.env .\.env -Force
Copy-Item config\docker-compose.yaml .\docker-compose.yaml -Force
``````

### 3. Restore volumes
``````powershell
Remove-Item .\volumes\weaviate -Recurse -Force
Copy-Item volumes\weaviate .\volumes\weaviate -Recurse

Remove-Item .\volumes\app\storage -Recurse -Force
Copy-Item volumes\storage .\volumes\app\storage -Recurse

Remove-Item .\volumes\plugin_daemon -Recurse -Force
Copy-Item volumes\plugin_daemon .\volumes\plugin_daemon -Recurse
``````

### 4. Restore PostgreSQL database
``````powershell
# Start only database
docker compose up -d db
Start-Sleep -Seconds 10

# Restore dump
Get-Content database\dify_db_$TIMESTAMP.sql.gz | gunzip | docker compose exec -T db psql -U postgres -d dify
``````

### 5. Restore Redis
``````powershell
Copy-Item database\redis_dump_$TIMESTAMP.rdb .\volumes\redis\dump.rdb -Force
``````

### 6. Start all services
``````powershell
docker compose up -d
``````

## Notes
- Vector database: Weaviate
- Storage type: OpenDAL (local filesystem)
- Database: PostgreSQL 15
"@

Set-Content -Path "$BACKUP_DIR\README.md" -Value $readmeContent

# Подсчет размера бэкапа
$backupSize = (Get-ChildItem -Path $BACKUP_DIR -Recurse | Measure-Object -Property Length -Sum).Sum / 1MB
$backupSizeFormatted = "{0:N2} MB" -f $backupSize

# Создание архива (опционально)
Write-Host ""
if (-not $NoArchive) {
    $response = Read-Host "Создать сжатый архив? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Создание архива..." -ForegroundColor Green
        $archivePath = "$BACKUP_ROOT\dify_backup_$TIMESTAMP.zip"
        Compress-Archive -Path $BACKUP_DIR -DestinationPath $archivePath -Force
        $archiveSize = (Get-Item $archivePath).Length / 1MB
        $archiveSizeFormatted = "{0:N2} MB" -f $archiveSize
        Write-Host "✓ Архив создан: dify_backup_$TIMESTAMP.zip ($archiveSizeFormatted)" -ForegroundColor Green
    }
}

# Итоговая информация
Write-Host ""
Write-Host "=== Backup Complete ===" -ForegroundColor Green
Write-Host "Backup location: " -NoNewline
Write-Host $BACKUP_DIR -ForegroundColor Yellow
Write-Host "Backup size: " -NoNewline
Write-Host $backupSizeFormatted -ForegroundColor Yellow
Write-Host "Timestamp: " -NoNewline
Write-Host $TIMESTAMP -ForegroundColor Yellow
Write-Host ""
Write-Host "✓ Резервное копирование завершено успешно!" -ForegroundColor Green

# Очистка старых бэкапов
Write-Host ""
if (-not $SkipOldCleanup) {
    $response = Read-Host "Удалить бэкапы старше 30 дней? (y/n)"
    if ($response -eq 'y' -or $response -eq 'Y') {
        Write-Host "Очистка старых бэкапов..."
        $cutoffDate = (Get-Date).AddDays(-30)
        Get-ChildItem -Path $BACKUP_ROOT -Directory -Filter "dify_backup_*" | 
            Where-Object { $_.CreationTime -lt $cutoffDate } | 
            Remove-Item -Recurse -Force
        Get-ChildItem -Path $BACKUP_ROOT -File -Filter "dify_backup_*.zip" | 
            Where-Object { $_.CreationTime -lt $cutoffDate } | 
            Remove-Item -Force
        Write-Host "✓ Очистка завершена"
    }
}

Write-Host ""
Write-Host "Рекомендация: Сохраните бэкап в безопасном месте вне сервера!" -ForegroundColor Yellow
