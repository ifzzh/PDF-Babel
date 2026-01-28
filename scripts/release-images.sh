#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
VERSION_BACKEND_FILE="$ROOT_DIR/docker.version.backend"
VERSION_FRONTEND_FILE="$ROOT_DIR/docker.version.frontend"
VERSION_BACKEND_BASE_FILE="$ROOT_DIR/docker.version.backend.base"

BACKEND_VERSION=${1:-}
FRONTEND_VERSION=${2:-}
BACKEND_BASE_VERSION=${3:-}

if [[ -z "$BACKEND_VERSION" ]]; then
  if [[ -f "$VERSION_BACKEND_FILE" ]]; then
    BACKEND_VERSION=$(cat "$VERSION_BACKEND_FILE")
  else
    echo "用法: $0 <backend_version> <frontend_version> [backend_base_version]" >&2
    exit 1
  fi
fi

if [[ -z "$FRONTEND_VERSION" ]]; then
  if [[ -f "$VERSION_FRONTEND_FILE" ]]; then
    FRONTEND_VERSION=$(cat "$VERSION_FRONTEND_FILE")
  else
    echo "用法: $0 <backend_version> <frontend_version> [backend_base_version]" >&2
    exit 1
  fi
fi

if [[ -z "$BACKEND_BASE_VERSION" ]]; then
  if [[ -f "$VERSION_BACKEND_BASE_FILE" ]]; then
    BACKEND_BASE_VERSION=$(cat "$VERSION_BACKEND_BASE_FILE")
  else
    BACKEND_BASE_VERSION="$BACKEND_VERSION"
  fi
fi

BACKEND_VERSION=${BACKEND_VERSION#v}
FRONTEND_VERSION=${FRONTEND_VERSION#v}
BACKEND_BASE_VERSION=${BACKEND_BASE_VERSION#v}

if [[ -z "$BACKEND_VERSION" || -z "$FRONTEND_VERSION" || -z "$BACKEND_BASE_VERSION" ]]; then
  echo "version 不能为空" >&2
  exit 1
fi

BACKEND_REPO="ifzzh520/pdf-babel-backend"
BACKEND_BASE_REPO="ifzzh520/pdf-babel-backend-base"
FRONTEND_REPO="ifzzh520/pdf-babel-frontend"

# 记录本地版本号
printf "%s" "$BACKEND_VERSION" > "$VERSION_BACKEND_FILE"
printf "%s" "$FRONTEND_VERSION" > "$VERSION_FRONTEND_FILE"
printf "%s" "$BACKEND_BASE_VERSION" > "$VERSION_BACKEND_BASE_FILE"

cd "$ROOT_DIR"

ensure_base_image() {
  local image="$1"
  local tag="$2"
  local dockerfile="$3"

  if docker image inspect "${image}:${tag}" >/dev/null 2>&1; then
    echo "==> Found local base image: ${image}:${tag}"
    return 0
  fi

  echo "==> Try pull base image: ${image}:${tag}"
  if docker pull "${image}:${tag}"; then
    docker tag "${image}:${tag}" "${image}:latest"
    return 0
  fi

  echo "==> Build backend base: ${image}:${tag}"
  docker build -f "$dockerfile" \
    -t "${image}:${tag}" \
    -t "${image}:latest" \
    .
}

ensure_base_image "$BACKEND_BASE_REPO" "$BACKEND_BASE_VERSION" "Dockerfile.backend.base"

echo "==> Build backend: $BACKEND_REPO:$BACKEND_VERSION"
docker build -f Dockerfile.backend \
  --build-arg BASE_IMAGE="$BACKEND_BASE_REPO:$BACKEND_BASE_VERSION" \
  -t "$BACKEND_REPO:$BACKEND_VERSION" \
  -t "$BACKEND_REPO:latest" \
  .

echo "==> Build frontend: $FRONTEND_REPO:$FRONTEND_VERSION"
docker build -f Dockerfile.frontend \
  -t "$FRONTEND_REPO:$FRONTEND_VERSION" \
  -t "$FRONTEND_REPO:latest" \
  .

echo "==> Push backend base"
docker push "$BACKEND_BASE_REPO:$BACKEND_BASE_VERSION"
docker push "$BACKEND_BASE_REPO:latest"

echo "==> Push backend"
docker push "$BACKEND_REPO:$BACKEND_VERSION"
docker push "$BACKEND_REPO:latest"

echo "==> Push frontend"
docker push "$FRONTEND_REPO:$FRONTEND_VERSION"
docker push "$FRONTEND_REPO:latest"

echo "Done. backend_base=$BACKEND_BASE_VERSION backend=$BACKEND_VERSION frontend=$FRONTEND_VERSION"
