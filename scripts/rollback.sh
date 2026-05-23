#!/bin/bash

# 联邦智枢 回滚脚本
# 使用方法: ./rollback.sh [environment] [version]
# environment: dev, prod (默认: dev)
# version: 回滚到的版本标签（可选）

set -e

ENVIRONMENT=${1:-dev}
VERSION=${2:-previous}

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)

if docker compose version >/dev/null 2>&1; then
    COMPOSE_CMD=(docker compose)
elif command -v docker-compose >/dev/null 2>&1; then
    COMPOSE_CMD=(docker-compose)
else
    echo "错误: Docker Compose未安装，请先安装Docker Desktop 或 docker compose plugin"
    exit 1
fi

echo "=========================================="
echo "联邦智枢 回滚脚本"
echo "环境: $ENVIRONMENT"
echo "版本: $VERSION"
echo "=========================================="

# 选择docker-compose文件
if [ "$ENVIRONMENT" = "prod" ]; then
    COMPOSE_FILE="docker/docker-compose.prod.yml"
else
    COMPOSE_FILE="docker/docker-compose.dev.yml"
fi

cd "$PROJECT_DIR"

# 停止当前服务
echo "停止当前服务..."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" down

# 如果有指定版本，切换到该版本
if [ "$VERSION" != "previous" ]; then
    echo "切换到版本: $VERSION"
    git checkout "$VERSION"
fi

# 重新构建并启动
echo "重新构建并启动..."
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" build
"${COMPOSE_CMD[@]}" -f "$COMPOSE_FILE" up -d

echo "回滚完成"





