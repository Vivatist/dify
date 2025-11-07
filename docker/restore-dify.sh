#!/bin/bash

# Dify Restore Script
# Восстанавливает Dify из резервной копии

set -e

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Dify Restore Script ===${NC}"
echo ""

# Проверка аргумента
if [ -z "$1" ]; then
    echo -e "${RED}Ошибка: Не указан путь к бэкапу!${NC}"
    echo ""
    echo "Использование:"
    echo "  $0 <backup_directory>"
    echo ""
    echo "Пример:"
    echo "  $0 ./backups/dify_backup_20240115_123000"
    echo "  $0 ./backups/dify_backup_20240115_123000.tar.gz"
    echo ""
    echo "Доступные бэкапы:"
    ls -1d ./backups/dify_backup_* 2>/dev/null | tail -5 || echo "  Нет доступных бэкапов"
    exit 1
fi

BACKUP_SOURCE="$1"

# Если это tar.gz, распаковываем
if [[ "$BACKUP_SOURCE" == *.tar.gz ]]; then
    echo -e "${YELLOW}Обнаружен архив, распаковка...${NC}"
    BACKUP_DIR="${BACKUP_SOURCE%.tar.gz}"
    if [ -d "$BACKUP_DIR" ]; then
        echo -e "${RED}⚠ Директория $BACKUP_DIR уже существует${NC}"
        read -p "Перезаписать? (y/n) " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            exit 1
        fi
        rm -rf "$BACKUP_DIR"
    fi
    tar -xzf "$BACKUP_SOURCE" -C ./backups/
    echo "✓ Архив распакован"
else
    BACKUP_DIR="$BACKUP_SOURCE"
fi

# Проверка существования бэкапа
if [ ! -d "$BACKUP_DIR" ]; then
    echo -e "${RED}Ошибка: Директория бэкапа не найдена: $BACKUP_DIR${NC}"
    exit 1
fi

echo -e "${YELLOW}Восстановление из: $BACKUP_DIR${NC}"
echo ""

# Предупреждение
echo -e "${RED}⚠⚠⚠ ВНИМАНИЕ ⚠⚠⚠${NC}"
echo -e "${RED}Восстановление ПЕРЕЗАПИШЕТ текущие данные!${NC}"
echo -e "${RED}Все текущие данные будут потеряны!${NC}"
echo ""
read -p "Продолжить? Введите 'yes' для подтверждения: " -r
if [[ ! $REPLY == "yes" ]]; then
    echo "Отменено"
    exit 1
fi

# 1. Остановка всех сервисов
echo -e "${GREEN}[1/7]${NC} Остановка Dify..."
docker compose down
echo "✓ Сервисы остановлены"

# 2. Восстановление конфигурации
echo -e "${GREEN}[2/7]${NC} Восстановление конфигурационных файлов..."
if [ -f "$BACKUP_DIR/config/.env" ]; then
    cp -v "$BACKUP_DIR/config/.env" ./.env
    echo "✓ .env восстановлен"
else
    echo -e "${RED}⚠ Warning: .env not found in backup${NC}"
fi

if [ -f "$BACKUP_DIR/config/docker-compose.yaml" ]; then
    cp -v "$BACKUP_DIR/config/docker-compose.yaml" ./docker-compose.yaml
    echo "✓ docker-compose.yaml восстановлен"
fi

# 3. Восстановление Weaviate
echo -e "${GREEN}[3/7]${NC} Восстановление данных Weaviate..."
if [ -d "$BACKUP_DIR/volumes/weaviate" ]; then
    echo "Удаление старых данных Weaviate..."
    rm -rf ./volumes/weaviate
    echo "Копирование данных из бэкапа (может занять время)..."
    cp -r "$BACKUP_DIR/volumes/weaviate" ./volumes/weaviate
    echo "✓ Weaviate восстановлен"
else
    echo -e "${YELLOW}⚠ Weaviate data not found in backup${NC}"
fi

# 4. Восстановление storage
echo -e "${GREEN}[4/7]${NC} Восстановление загруженных файлов..."
if [ -d "$BACKUP_DIR/volumes/storage" ]; then
    echo "Удаление старых файлов..."
    rm -rf ./volumes/app/storage
    mkdir -p ./volumes/app
    echo "Копирование файлов из бэкапа..."
    cp -r "$BACKUP_DIR/volumes/storage" ./volumes/app/storage
    echo "✓ Storage восстановлен"
else
    echo -e "${YELLOW}⚠ Storage data not found in backup${NC}"
fi

# 5. Восстановление plugin data
echo -e "${GREEN}[5/7]${NC} Восстановление данных плагинов..."
if [ -f "$BACKUP_DIR/volumes/plugin_daemon.tar.gz" ]; then
    echo "Удаление старых данных плагинов..."
    sudo rm -rf ./volumes/plugin_daemon
    echo "Распаковка данных плагинов (может занять время)..."
    sudo tar -xzf "$BACKUP_DIR/volumes/plugin_daemon.tar.gz" -C ./volumes/
    echo "✓ Plugin data восстановлен"
elif [ -d "$BACKUP_DIR/volumes/plugin_daemon" ]; then
    sudo rm -rf ./volumes/plugin_daemon
    sudo cp -r "$BACKUP_DIR/volumes/plugin_daemon" ./volumes/plugin_daemon
    echo "✓ Plugin data восстановлен"
else
    echo -e "${YELLOW}⚠ Plugin data not found in backup${NC}"
fi

# 6. Запуск только базы данных для восстановления
echo -e "${GREEN}[6/7]${NC} Восстановление базы данных PostgreSQL..."

# Очистка старых данных PostgreSQL
echo "Удаление старых данных PostgreSQL..."
rm -rf ./volumes/db/data
mkdir -p ./volumes/db/data

# Запуск только БД
echo "Запуск PostgreSQL..."
docker compose up -d db
echo "Ожидание инициализации PostgreSQL (30 секунд)..."
sleep 30

# Проверка, что БД готова
echo "Проверка готовности PostgreSQL..."
for i in {1..10}; do
    if docker compose exec -T db pg_isready -U postgres > /dev/null 2>&1; then
        echo "✓ PostgreSQL готов"
        break
    fi
    echo "Ожидание... ($i/10)"
    sleep 3
done

# Восстановление дампа
if [ -f "$BACKUP_DIR/database/"dify_db_*.sql.gz ]; then
    DB_DUMP=$(ls "$BACKUP_DIR/database/"dify_db_*.sql.gz | head -1)
    DB_NAME=$(grep "^DB_DATABASE=" .env | cut -d'=' -f2)
    DB_USER=$(grep "^DB_USERNAME=" .env | cut -d'=' -f2)
    
    echo "Восстановление дампа: $(basename $DB_DUMP)"
    
    # Создание базы если не существует
    docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS $DB_NAME;" || true
    docker compose exec -T db psql -U postgres -c "CREATE DATABASE $DB_NAME;" || true
    
    # Восстановление данных
    gunzip -c "$DB_DUMP" | docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME"
    echo "✓ База данных восстановлена"
else
    echo -e "${RED}⚠ Database dump not found in backup!${NC}"
fi

# Восстановление Redis
echo ""
echo "Восстановление Redis..."
docker compose stop redis 2>/dev/null || true
if [ -f "$BACKUP_DIR/database/"redis_dump_*.rdb ]; then
    REDIS_DUMP=$(ls "$BACKUP_DIR/database/"redis_dump_*.rdb | head -1)
    rm -f ./volumes/redis/data/dump.rdb
    mkdir -p ./volumes/redis/data
    cp "$REDIS_DUMP" ./volumes/redis/data/dump.rdb
    echo "✓ Redis dump восстановлен"
else
    echo -e "${YELLOW}⚠ Redis dump not found in backup${NC}"
fi

# 7. Запуск всех сервисов
echo -e "${GREEN}[7/7]${NC} Запуск всех сервисов Dify..."
docker compose up -d

echo ""
echo "Ожидание инициализации сервисов (60 секунд)..."
sleep 60

# Проверка статуса
echo ""
echo -e "${GREEN}=== Статус сервисов ===${NC}"
docker compose ps

echo ""
echo -e "${GREEN}=== Restore Complete ===${NC}"
echo -e "Восстановление завершено из: ${YELLOW}$BACKUP_DIR${NC}"
echo ""
echo -e "${YELLOW}Рекомендации:${NC}"
echo "1. Проверьте логи: docker compose logs --tail=100"
echo "2. Откройте web-интерфейс: http://localhost/console"
echo "3. Убедитесь, что все данные восстановлены корректно"
echo ""
echo -e "${GREEN}✓ Dify успешно восстановлен!${NC}"
