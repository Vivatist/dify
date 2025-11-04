# Dify Backup Quick Start

## TL;DR

```bash
# Создать бэкап (bash)
./backup-dify.sh

# Создать бэкап (PowerShell)
.\backup-dify.ps1

# Восстановить (bash)
./restore-dify.sh ./backups/dify_backup_YYYYMMDD_HHMMSS

# Восстановить (PowerShell)
.\restore-dify.ps1 -BackupPath .\backups\dify_backup_YYYYMMDD_HHMMSS
```

## Что входит в бэкап

✅ `.env` - вся конфигурация  
✅ PostgreSQL - база данных (SQL dump)  
✅ Redis - кеш (RDB dump)  
✅ Weaviate - векторные эмбеддинги  
✅ Storage - загруженные файлы  
✅ Plugins - данные плагинов  

## Автоматический бэкап

### Windows (Task Scheduler)

```powershell
# Ежедневно в 2:00
$action = New-ScheduledTaskAction -Execute "PowerShell.exe" `
    -Argument "-File C:\Users\Andrey\dify\docker\backup-dify.ps1 -NoArchive -SkipOldCleanup"

$trigger = New-ScheduledTaskTrigger -Daily -At 02:00

Register-ScheduledTask -TaskName "DifyBackup" -Action $action -Trigger $trigger
```

### Linux/Mac (Cron)

```bash
# Редактировать crontab
crontab -e

# Добавить: ежедневно в 2:00
0 2 * * * cd /path/to/dify/docker && ./backup-dify.sh
```

## Важные моменты

⚠️ Бэкапы > 30 дней удаляются автоматически (опционально)  
⚠️ Храните бэкапы вне сервера (облако, внешний диск)  
⚠️ Тестируйте восстановление регулярно  
⚠️ Перед обновлением Dify - обязательный бэкап  

## Проблемы?

См. подробное руководство: [BACKUP_GUIDE.md](BACKUP_GUIDE.md)
