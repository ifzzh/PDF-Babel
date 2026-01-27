#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION_BACKEND_FILE="$ROOT_DIR/docker.version.backend"
VERSION_FRONTEND_FILE="$ROOT_DIR/docker.version.frontend"

BACKEND_VERSION=${1:-}
FRONTEND_VERSION=${2:-}

if [[ -z "$BACKEND_VERSION" ]]; then
  if [[ -f "$VERSION_BACKEND_FILE" ]]; then
    BACKEND_VERSION=$(cat "$VERSION_BACKEND_FILE")
  else
    echo "用法: $0 <backend_version> <frontend_version>" >&2
    exit 1
  fi
fi

if [[ -z "$FRONTEND_VERSION" ]]; then
  if [[ -f "$VERSION_FRONTEND_FILE" ]]; then
    FRONTEND_VERSION=$(cat "$VERSION_FRONTEND_FILE")
  else
    echo "用法: $0 <backend_version> <frontend_version>" >&2
    exit 1
  fi
fi

BACKEND_VERSION=${BACKEND_VERSION#v}
FRONTEND_VERSION=${FRONTEND_VERSION#v}

if [[ -z "$BACKEND_VERSION" || -z "$FRONTEND_VERSION" ]]; then
  echo "version 不能为空" >&2
  exit 1
fi

BACKEND_REPO="ifzzh520/pdf-babel-backend"
FRONTEND_REPO="ifzzh520/pdf-babel-frontend"

# 记录本地版本号
printf "%s" "$BACKEND_VERSION" > "$VERSION_BACKEND_FILE"
printf "%s" "$FRONTEND_VERSION" > "$VERSION_FRONTEND_FILE"

cd "$ROOT_DIR"

echo "==> Build backend: $BACKEND_REPO:$BACKEND_VERSION"
docker build -f Dockerfile.backend \
  -t "$BACKEND_REPO:$BACKEND_VERSION" \
  -t "$BACKEND_REPO:latest" \
  .

echo "==> Build frontend: $FRONTEND_REPO:$FRONTEND_VERSION"
docker build -f Dockerfile.frontend \
  -t "$FRONTEND_REPO:$FRONTEND_VERSION" \
  -t "$FRONTEND_REPO:latest" \
  .

echo "==> Push backend"
docker push "$BACKEND_REPO:$BACKEND_VERSION"
docker push "$BACKEND_REPO:latest"

echo "==> Push frontend"
docker push "$FRONTEND_REPO:$FRONTEND_VERSION"
docker push "$FRONTEND_REPO:latest"

echo "Done. backend=$BACKEND_VERSION frontend=$FRONTEND_VERSION"
