#!/bin/bash

# Dify Backup Script
# Создает резервную копию всех данных Dify включая базу данных, векторную БД, файлы и конфигурацию

set -e

# Конфигурация
BACKUP_ROOT="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/dify_backup_$TIMESTAMP"

# Цвета для вывода
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Dify Backup Script ===${NC}"
echo -e "${YELLOW}Начало резервного копирования: $(date)${NC}"
echo ""

# Создаем директорию для бэкапа
echo -e "${GREEN}[1/7]${NC} Создание директории для бэкапа..."
mkdir -p "$BACKUP_DIR"/{config,database,volumes,logs}

# 1. Backup конфигурации (.env файлы)
echo -e "${GREEN}[2/7]${NC} Копирование конфигурационных файлов..."
cp -v .env "$BACKUP_DIR/config/.env" 2>/dev/null || echo "Warning: .env not found"
cp -v .env.example "$BACKUP_DIR/config/.env.example" 2>/dev/null || true
cp -v docker-compose.yaml "$BACKUP_DIR/config/docker-compose.yaml"

# 2. Backup PostgreSQL database
echo -e "${GREEN}[3/7]${NC} Создание дампа базы данных PostgreSQL..."
if docker compose ps db | grep -q "Up"; then
    DB_USER=$(grep "^DB_USERNAME=" .env | cut -d'=' -f2)
    DB_NAME=$(grep "^DB_DATABASE=" .env | cut -d'=' -f2)
    DB_PASSWORD=$(grep "^DB_PASSWORD=" .env | cut -d'=' -f2)
    
    docker compose exec -T db pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_DIR/database/dify_db_$TIMESTAMP.sql.gz"
    echo "✓ Database dump created: dify_db_$TIMESTAMP.sql.gz"
else
    echo -e "${RED}⚠ Warning: PostgreSQL container not running, skipping database backup${NC}"
fi

# 3. Backup Redis data
echo -e "${GREEN}[4/7]${NC} Создание дампа Redis..."
if docker compose ps redis | grep -q "Up"; then
    docker compose exec -T redis redis-cli save > /dev/null 2>&1
    sleep 2
    if [ -f "./volumes/redis/data/dump.rdb" ]; then
        cp -v ./volumes/redis/data/dump.rdb "$BACKUP_DIR/database/redis_dump_$TIMESTAMP.rdb"
        echo "✓ Redis dump created: redis_dump_$TIMESTAMP.rdb"
    else
        echo -e "${YELLOW}⚠ Warning: Redis dump not found at ./volumes/redis/data/dump.rdb${NC}"
    fi
else
    echo -e "${RED}⚠ Warning: Redis container not running, skipping Redis backup${NC}"
fi

# 4. Backup Weaviate vector database
echo -e "${GREEN}[5/7]${NC} Копирование данных Weaviate (векторная БД)..."
if [ -d "./volumes/weaviate" ]; then
    echo "Copying Weaviate data (this may take a while)..."
    cp -r ./volumes/weaviate "$BACKUP_DIR/volumes/weaviate"
    echo "✓ Weaviate data copied"
else
    echo "⚠ Warning: Weaviate directory not found"
fi

# 5. Backup uploaded files and storage
echo -e "${GREEN}[6/7]${NC} Копирование загруженных файлов..."
if [ -d "./volumes/app/storage" ]; then
    echo "Copying storage data..."
    cp -r ./volumes/app/storage "$BACKUP_DIR/volumes/storage"
    echo "✓ Storage data copied"
else
    echo "⚠ Warning: Storage directory not found"
fi

# 6. Backup plugin data
if [ -d "./volumes/plugin_daemon" ]; then
    echo "Copying plugin data..."
    # Use tar to handle symlinks properly
    tar -czf "$BACKUP_DIR/volumes/plugin_daemon.tar.gz" -C ./volumes plugin_daemon 2>/dev/null || \
        cp -rL ./volumes/plugin_daemon "$BACKUP_DIR/volumes/plugin_daemon" 2>/dev/null || \
        echo "⚠ Warning: Some plugin files skipped (symlinks)"
    echo "✓ Plugin data copied"
fi

# 7. Создание README с информацией о бэкапе
echo -e "${GREEN}[7/7]${NC} Создание информационного файла..."
cat > "$BACKUP_DIR/README.md" <<EOF
# Dify Backup - $TIMESTAMP

## Backup Information
- Date: $(date)
- Dify Version: 1.9.2
- Hostname: $(hostname)
- Docker Compose Version: $(docker compose version --short 2>/dev/null || echo "unknown")

## Contents
- \`config/\` - Configuration files (.env, docker-compose.yaml)
- \`database/\` - PostgreSQL and Redis dumps
- \`volumes/\` - Persistent data (Weaviate, storage, plugins)
- \`logs/\` - Application logs (if any)

## Restore Instructions

### 1. Stop Dify services
\`\`\`bash
cd /path/to/dify/docker
docker compose down
\`\`\`

### 2. Restore configuration
\`\`\`bash
cp config/.env ./.env
cp config/docker-compose.yaml ./docker-compose.yaml
\`\`\`

### 3. Restore volumes
\`\`\`bash
rm -rf ./volumes/weaviate
cp -r volumes/weaviate ./volumes/weaviate

rm -rf ./volumes/app/storage
cp -r volumes/storage ./volumes/app/storage

rm -rf ./volumes/plugin_daemon
cp -r volumes/plugin_daemon ./volumes/plugin_daemon
\`\`\`

### 4. Restore PostgreSQL database
\`\`\`bash
# Start only database
docker compose up -d db
sleep 10

# Restore dump
gunzip -c database/dify_db_$TIMESTAMP.sql.gz | docker compose exec -T db psql -U postgres -d dify
\`\`\`

### 5. Restore Redis
\`\`\`bash
cp database/redis_dump_$TIMESTAMP.rdb ./volumes/redis/dump.rdb
\`\`\`

### 6. Start all services
\`\`\`bash
docker compose up -d
\`\`\`

## Notes
- Vector database: Weaviate
- Storage type: OpenDAL (local filesystem)
- Database: PostgreSQL 15

## Backup Size
\`\`\`
$(du -sh "$BACKUP_DIR" 2>/dev/null || echo "Calculating...")
\`\`\`
EOF

# Подсчет размера бэкапа
BACKUP_SIZE=$(du -sh "$BACKUP_DIR" | cut -f1)

# Создание tar.gz архива (опционально)
echo ""
read -p "Создать сжатый архив? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${GREEN}Создание архива...${NC}"
    cd "$BACKUP_ROOT"
    tar -czf "dify_backup_$TIMESTAMP.tar.gz" "dify_backup_$TIMESTAMP"
    ARCHIVE_SIZE=$(du -sh "dify_backup_$TIMESTAMP.tar.gz" | cut -f1)
    echo -e "${GREEN}✓ Архив создан: dify_backup_$TIMESTAMP.tar.gz ($ARCHIVE_SIZE)${NC}"
    cd - > /dev/null
fi

# Итоговая информация
echo ""
echo -e "${GREEN}=== Backup Complete ===${NC}"
echo -e "Backup location: ${YELLOW}$BACKUP_DIR${NC}"
echo -e "Backup size: ${YELLOW}$BACKUP_SIZE${NC}"
echo -e "Timestamp: ${YELLOW}$TIMESTAMP${NC}"
echo ""
echo -e "${GREEN}✓ Резервное копирование завершено успешно!${NC}"

# Очистка старых бэкапов (старше 30 дней)
echo ""
read -p "Удалить бэкапы старше 30 дней? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Очистка старых бэкапов..."
    find "$BACKUP_ROOT" -name "dify_backup_*" -type d -mtime +30 -exec rm -rf {} + 2>/dev/null || true
    find "$BACKUP_ROOT" -name "dify_backup_*.tar.gz" -type f -mtime +30 -delete 2>/dev/null || true
    echo "✓ Очистка завершена"
fi

echo ""
echo -e "${YELLOW}Рекомендация: Сохраните бэкап в безопасном месте вне сервера!${NC}"
