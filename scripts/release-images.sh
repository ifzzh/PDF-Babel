#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION_FILE="$ROOT_DIR/docker.version"

VERSION=${1:-}
if [[ -z "$VERSION" ]]; then
  if [[ -f "$VERSION_FILE" ]]; then
    VERSION=$(cat "$VERSION_FILE")
  else
    echo "用法: $0 <version>" >&2
    exit 1
  fi
fi

# 允许传入 v0.4.1 形式
VERSION=${VERSION#v}

if [[ -z "$VERSION" ]]; then
  echo "version 不能为空" >&2
  exit 1
fi

BACKEND_REPO="ifzzh520/pdf-babel-backend"
FRONTEND_REPO="ifzzh520/pdf-babel-frontend"

# 记录本地版本号
printf "%s" "$VERSION" > "$VERSION_FILE"

cd "$ROOT_DIR"

echo "==> Build backend: $BACKEND_REPO:$VERSION"
docker build -f Dockerfile.backend \
  -t "$BACKEND_REPO:$VERSION" \
  -t "$BACKEND_REPO:latest" \
  .

echo "==> Build frontend: $FRONTEND_REPO:$VERSION"
docker build -f Dockerfile.frontend \
  -t "$FRONTEND_REPO:$VERSION" \
  -t "$FRONTEND_REPO:latest" \
  .

echo "==> Push backend"
docker push "$BACKEND_REPO:$VERSION"
docker push "$BACKEND_REPO:latest"

echo "==> Push frontend"
docker push "$FRONTEND_REPO:$VERSION"
docker push "$FRONTEND_REPO:latest"

echo "Done. version=$VERSION"
