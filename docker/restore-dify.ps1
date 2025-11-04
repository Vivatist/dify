# Dify Restore Script for Windows PowerShell
# Восстанавливает Dify из резервной копии

param(
    [Parameter(Mandatory=$true)]
    [string]$BackupPath
)

$ErrorActionPreference = "Stop"

Write-Host "=== Dify Restore Script ===" -ForegroundColor Green
Write-Host ""

# Проверка существования бэкапа
if ($BackupPath -like "*.zip") {
    Write-Host "Обнаружен архив, распаковка..." -ForegroundColor Yellow
    $extractPath = $BackupPath -replace '\.zip$', ''
    if (Test-Path $extractPath) {
        Write-Host "⚠ Директория $extractPath уже существует" -ForegroundColor Red
        $response = Read-Host "Перезаписать? (y/n)"
        if ($response -ne 'y' -and $response -ne 'Y') {
            exit 1
        }
        Remove-Item $extractPath -Recurse -Force
    }
    Expand-Archive -Path $BackupPath -DestinationPath (Split-Path $BackupPath) -Force
    $BACKUP_DIR = $extractPath
    Write-Host "✓ Архив распакован"
} else {
    $BACKUP_DIR = $BackupPath
}

if (-not (Test-Path $BACKUP_DIR)) {
    Write-Host "Ошибка: Директория бэкапа не найдена: $BACKUP_DIR" -ForegroundColor Red
    Write-Host ""
    Write-Host "Доступные бэкапы:"
    Get-ChildItem -Path ".\backups" -Directory -Filter "dify_backup_*" | Select-Object -Last 5 | ForEach-Object {
        Write-Host "  $_"
    }
    exit 1
}

Write-Host "Восстановление из: $BACKUP_DIR" -ForegroundColor Yellow
Write-Host ""

# Предупреждение
Write-Host "⚠⚠⚠ ВНИМАНИЕ ⚠⚠⚠" -ForegroundColor Red
Write-Host "Восстановление ПЕРЕЗАПИШЕТ текущие данные!" -ForegroundColor Red
Write-Host "Все текущие данные будут потеряны!" -ForegroundColor Red
Write-Host ""
$confirmation = Read-Host "Продолжить? Введите 'yes' для подтверждения"
if ($confirmation -ne "yes") {
    Write-Host "Отменено"
    exit 1
}

# 1. Остановка всех сервисов
Write-Host "[1/7] Остановка Dify..." -ForegroundColor Green
docker compose down
Write-Host "✓ Сервисы остановлены"

# 2. Восстановление конфигурации
Write-Host "[2/7] Восстановление конфигурационных файлов..." -ForegroundColor Green
if (Test-Path "$BACKUP_DIR\config\.env") {
    Copy-Item "$BACKUP_DIR\config\.env" ".\.env" -Force
    Write-Host "✓ .env восстановлен"
} else {
    Write-Host "⚠ Warning: .env not found in backup" -ForegroundColor Yellow
}

if (Test-Path "$BACKUP_DIR\config\docker-compose.yaml") {
    Copy-Item "$BACKUP_DIR\config\docker-compose.yaml" ".\docker-compose.yaml" -Force
    Write-Host "✓ docker-compose.yaml восстановлен"
}

# 3. Восстановление Weaviate
Write-Host "[3/7] Восстановление данных Weaviate..." -ForegroundColor Green
if (Test-Path "$BACKUP_DIR\volumes\weaviate") {
    Write-Host "Удаление старых данных Weaviate..."
    if (Test-Path ".\volumes\weaviate") {
        Remove-Item ".\volumes\weaviate" -Recurse -Force
    }
    Write-Host "Копирование данных из бэкапа (может занять время)..."
    Copy-Item "$BACKUP_DIR\volumes\weaviate" ".\volumes\weaviate" -Recurse -Force
    Write-Host "✓ Weaviate восстановлен"
} else {
    Write-Host "⚠ Weaviate data not found in backup" -ForegroundColor Yellow
}

# 4. Восстановление storage
Write-Host "[4/7] Восстановление загруженных файлов..." -ForegroundColor Green
if (Test-Path "$BACKUP_DIR\volumes\storage") {
    Write-Host "Удаление старых файлов..."
    if (Test-Path ".\volumes\app\storage") {
        Remove-Item ".\volumes\app\storage" -Recurse -Force
    }
    New-Item -ItemType Directory -Force -Path ".\volumes\app" | Out-Null
    Write-Host "Копирование файлов из бэкапа..."
    Copy-Item "$BACKUP_DIR\volumes\storage" ".\volumes\app\storage" -Recurse -Force
    Write-Host "✓ Storage восстановлен"
} else {
    Write-Host "⚠ Storage data not found in backup" -ForegroundColor Yellow
}

# 5. Восстановление plugin data
Write-Host "[5/7] Восстановление данных плагинов..." -ForegroundColor Green
if (Test-Path "$BACKUP_DIR\volumes\plugin_daemon") {
    if (Test-Path ".\volumes\plugin_daemon") {
        Remove-Item ".\volumes\plugin_daemon" -Recurse -Force
    }
    Copy-Item "$BACKUP_DIR\volumes\plugin_daemon" ".\volumes\plugin_daemon" -Recurse -Force
    Write-Host "✓ Plugin data восстановлен"
} else {
    Write-Host "⚠ Plugin data not found in backup" -ForegroundColor Yellow
}

# 6. Запуск только базы данных для восстановления
Write-Host "[6/7] Восстановление базы данных PostgreSQL..." -ForegroundColor Green

# Очистка старых данных PostgreSQL
Write-Host "Удаление старых данных PostgreSQL..."
if (Test-Path ".\volumes\db\data") {
    Remove-Item ".\volumes\db\data" -Recurse -Force
}
New-Item -ItemType Directory -Force -Path ".\volumes\db\data" | Out-Null

# Запуск только БД
Write-Host "Запуск PostgreSQL..."
docker compose up -d db
Write-Host "Ожидание инициализации PostgreSQL (30 секунд)..."
Start-Sleep -Seconds 30

# Проверка, что БД готова
Write-Host "Проверка готовности PostgreSQL..."
$ready = $false
for ($i = 1; $i -le 10; $i++) {
    $result = docker compose exec -T db pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL готов"
        $ready = $true
        break
    }
    Write-Host "Ожидание... ($i/10)"
    Start-Sleep -Seconds 3
}

if (-not $ready) {
    Write-Host "⚠ PostgreSQL не готов после 30 секунд ожидания" -ForegroundColor Yellow
}

# Восстановление дампа
$dbDump = Get-ChildItem -Path "$BACKUP_DIR\database" -Filter "dify_db_*.sql.gz" | Select-Object -First 1
if ($dbDump) {
    $DB_NAME = (Select-String -Path ".env" -Pattern "^DB_DATABASE=(.+)$").Matches.Groups[1].Value
    $DB_USER = (Select-String -Path ".env" -Pattern "^DB_USERNAME=(.+)$").Matches.Groups[1].Value
    
    Write-Host "Восстановление дампа: $($dbDump.Name)"
    
    # Создание базы если не существует
    docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" 2>$null | Out-Null
    docker compose exec -T db psql -U postgres -c "CREATE DATABASE $DB_NAME;" 2>$null | Out-Null
    
    # Восстановление данных
    $dumpContent = Get-Content $dbDump.FullName -Raw -Encoding Byte
    $dumpContent | docker compose exec -T db sh -c "gunzip | psql -U $DB_USER -d $DB_NAME" 2>$null
    Write-Host "✓ База данных восстановлена"
} else {
    Write-Host "⚠ Database dump not found in backup!" -ForegroundColor Red
}

# Восстановление Redis
Write-Host ""
Write-Host "Восстановление Redis..."
docker compose stop redis 2>$null | Out-Null
$redisDump = Get-ChildItem -Path "$BACKUP_DIR\database" -Filter "redis_dump_*.rdb" | Select-Object -First 1
if ($redisDump) {
    if (Test-Path ".\volumes\redis\data\dump.rdb") {
        Remove-Item ".\volumes\redis\data\dump.rdb" -Force
    }
    New-Item -ItemType Directory -Force -Path ".\volumes\redis\data" | Out-Null
    Copy-Item $redisDump.FullName ".\volumes\redis\data\dump.rdb" -Force
    Write-Host "✓ Redis dump восстановлен"
} else {
    Write-Host "⚠ Redis dump not found in backup" -ForegroundColor Yellow
}

# 7. Запуск всех сервисов
Write-Host "[7/7] Запуск всех сервисов Dify..." -ForegroundColor Green
docker compose up -d

Write-Host ""
Write-Host "Ожидание инициализации сервисов (60 секунд)..."
Start-Sleep -Seconds 60

# Проверка статуса
Write-Host ""
Write-Host "=== Статус сервисов ===" -ForegroundColor Green
docker compose ps

Write-Host ""
Write-Host "=== Restore Complete ===" -ForegroundColor Green
Write-Host "Восстановление завершено из: " -NoNewline
Write-Host $BACKUP_DIR -ForegroundColor Yellow
Write-Host ""
Write-Host "Рекомендации:" -ForegroundColor Yellow
Write-Host "1. Проверьте логи: docker compose logs --tail=100"
Write-Host "2. Откройте web-интерфейс: http://localhost/console"
Write-Host "3. Убедитесь, что все данные восстановлены корректно"
Write-Host ""
Write-Host "✓ Dify успешно восстановлен!" -ForegroundColor Green
