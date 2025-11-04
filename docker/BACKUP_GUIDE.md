# Dify Backup & Restore Guide

## Обзор

Система резервного копирования Dify включает полное сохранение всех данных:
- ✅ Конфигурация (.env, docker-compose.yaml)
- ✅ База данных PostgreSQL (SQL dump)
- ✅ Redis кеш (RDB dump)
- ✅ Векторная БД Weaviate (полная копия)
- ✅ Загруженные файлы (storage)
- ✅ Данные плагинов

## Быстрый старт

### Linux/Mac (bash)

```bash
cd /path/to/dify/docker

# Создать бэкап
./backup-dify.sh

# Восстановить из бэкапа
./restore-dify.sh ./backups/dify_backup_20240115_123000
```

### Windows (PowerShell)

```powershell
cd C:\Users\Andrey\dify\docker

# Создать бэкап
.\backup-dify.ps1

# Создать бэкап без архивации
.\backup-dify.ps1 -NoArchive

# Восстановить из бэкапа
.\restore-dify.ps1 -BackupPath .\backups\dify_backup_20240115_123000
```

## Структура бэкапа

```
dify_backup_20240115_123000/
├── config/
│   ├── .env                          # Конфигурация окружения
│   ├── .env.example                  # Пример конфигурации
│   └── docker-compose.yaml           # Docker Compose манифест
├── database/
│   ├── dify_db_20240115_123000.sql.gz    # PostgreSQL dump (сжатый)
│   └── redis_dump_20240115_123000.rdb    # Redis persistence
├── volumes/
│   ├── weaviate/                     # Векторная БД (~100MB-10GB)
│   ├── storage/                      # Загруженные файлы
│   └── plugin_daemon/                # Данные плагинов
└── README.md                         # Инструкции по восстановлению
```

## Рекомендации по бэкапу

### Частота

- **Продакшн**: Ежедневно (автоматически)
- **Тестирование**: Еженедельно
- **Перед обновлением**: Обязательно

### Хранение

1. Локальные бэкапы удаляются автоматически через 30 дней
2. Храните архивы в облаке (S3, Google Drive, OneDrive)
3. Минимум 3 последних бэкапа в безопасном месте

### Размер бэкапов

Типичные размеры:
- Новая установка: ~200MB
- Малый проект: 500MB - 2GB
- Средний проект: 2-10GB
- Большой проект: 10GB+

Основной объем: Weaviate (векторные эмбеддинги) и загруженные файлы.

## Автоматизация

### Linux/Mac - Cron

```bash
# Редактировать crontab
crontab -e

# Ежедневный бэкап в 02:00
0 2 * * * cd /path/to/dify/docker && ./backup-dify.sh

# Еженедельный бэкап в воскресенье в 03:00
0 3 * * 0 cd /path/to/dify/docker && ./backup-dify.sh
```

### Windows - Task Scheduler

```powershell
# Создать scheduled task для ежедневного бэкапа
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-File C:\Users\Andrey\dify\docker\backup-dify.ps1 -NoArchive -SkipOldCleanup"

$trigger = New-ScheduledTaskTrigger -Daily -At 02:00

$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -RunOnlyIfNetworkAvailable

Register-ScheduledTask -TaskName "DifyBackup" -Action $action -Trigger $trigger -Settings $settings
```

## Восстановление

### Полное восстановление

```bash
# 1. Остановить Dify
docker compose down

# 2. Восстановить (автоматически)
./restore-dify.sh ./backups/dify_backup_20240115_123000

# 3. Проверить статус
docker compose ps
docker compose logs --tail=100
```

### Частичное восстановление

#### Только конфигурация

```bash
cp backups/dify_backup_20240115_123000/config/.env ./.env
docker compose restart
```

#### Только база данных

```bash
# Остановить только API и worker
docker compose stop api worker worker_beat

# Восстановить БД
gunzip -c backups/dify_backup_20240115_123000/database/dify_db_*.sql.gz | \
    docker compose exec -T db psql -U postgres -d dify

# Перезапустить
docker compose start api worker worker_beat
```

#### Только векторная БД

```bash
docker compose stop weaviate
rm -rf ./volumes/weaviate
cp -r backups/dify_backup_20240115_123000/volumes/weaviate ./volumes/weaviate
docker compose start weaviate
```

## Миграция на новый сервер

### 1. Подготовка

```bash
# На старом сервере
cd /path/to/dify/docker
./backup-dify.sh

# Создать архив
cd backups
tar -czf dify_backup_20240115_123000.tar.gz dify_backup_20240115_123000/

# Скопировать на новый сервер (scp, rsync, etc.)
scp dify_backup_20240115_123000.tar.gz user@newserver:/tmp/
```

### 2. Установка на новом сервере

```bash
# На новом сервере
git clone https://github.com/Vivatist/dify.git
cd dify/docker

# Скопировать скрипты восстановления
cp /path/to/restore-dify.sh ./

# Распаковать бэкап
mkdir -p backups
tar -xzf /tmp/dify_backup_20240115_123000.tar.gz -C backups/

# Восстановить
./restore-dify.sh ./backups/dify_backup_20240115_123000
```

### 3. Проверка

```bash
# Проверить все сервисы
docker compose ps

# Проверить логи
docker compose logs --tail=100

# Открыть web-интерфейс
# http://<new-server-ip>/console
```

## Troubleshooting

### Ошибка: "Database dump failed"

```bash
# Проверить статус PostgreSQL
docker compose ps db

# Проверить логи
docker compose logs db --tail=50

# Проверить подключение
docker compose exec db psql -U postgres -c "\l"
```

### Ошибка: "Permission denied"

```bash
# Linux/Mac: Добавить права на выполнение
chmod +x backup-dify.sh restore-dify.sh

# Проверить владельца volumes
sudo chown -R $USER:$USER ./volumes/
```

### Бэкап слишком большой

```bash
# Очистить старые данные Weaviate перед бэкапом
docker compose exec weaviate curl -X DELETE localhost:8080/v1/schema

# Очистить неиспользуемые файлы
docker compose exec api python -m app.commands.cleanup_storage

# Сжать архив максимально
tar -czf - dify_backup_20240115_123000 | pigz -9 > dify_backup_20240115_123000.tar.gz
```

### Восстановление зависло

```bash
# Остановить все
docker compose down

# Очистить volumes полностью
rm -rf ./volumes/*

# Начать восстановление заново
./restore-dify.sh ./backups/dify_backup_20240115_123000
```

## Проверка целостности бэкапа

```bash
# Проверить размеры
du -sh backups/dify_backup_*/

# Проверить структуру
tree -L 2 backups/dify_backup_20240115_123000/

# Проверить SQL dump
gunzip -c backups/dify_backup_20240115_123000/database/dify_db_*.sql.gz | head -50

# Проверить Redis dump
file backups/dify_backup_20240115_123000/database/redis_dump_*.rdb
```

## Best Practices

1. **Тестируйте восстановление**: Регулярно проверяйте, что бэкапы можно восстановить
2. **Мониторинг**: Настройте уведомления об успешных/неудачных бэкапах
3. **Версионирование**: Храните несколько версий бэкапов
4. **Шифрование**: Шифруйте бэкапы перед отправкой в облако
5. **Документация**: Обновляйте .env.example при изменении конфигурации

## Полезные команды

```bash
# Список всех бэкапов
ls -lth backups/

# Размер каждого бэкапа
du -sh backups/dify_backup_*/ | sort -h

# Удалить старые бэкапы (старше 30 дней)
find backups/ -name "dify_backup_*" -type d -mtime +30 -exec rm -rf {} +

# Проверить свободное место
df -h .

# Бэкап с логированием
./backup-dify.sh 2>&1 | tee backup_$(date +%Y%m%d_%H%M%S).log
```

## Дополнительные ресурсы

- [Dify Documentation](https://docs.dify.ai/)
- [Docker Compose Backup](https://docs.docker.com/storage/volumes/#back-up-restore-or-migrate-data-volumes)
- [PostgreSQL Backup](https://www.postgresql.org/docs/current/backup.html)
- [Weaviate Backup](https://weaviate.io/developers/weaviate/configuration/backups)

## Поддержка

При проблемах с бэкапом/восстановлением:
1. Проверьте логи: `docker compose logs`
2. Проверьте свободное место: `df -h`
3. Проверьте права доступа: `ls -la volumes/`
4. Создайте issue в репозитории с логами
