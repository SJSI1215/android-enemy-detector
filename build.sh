#!/bin/bash
# 安卓APK构建脚本 (需要Docker)
# 用法: bash build.sh

echo "=== Building Android APK with Buildozer ==="

# 方法1: 使用官方buildozer镜像
docker run --rm -v "$(pwd)":/app -w /app \
    kivy/buildozer:latest \
    buildozer android debug

# 方法2: 如果Docker不可用, 手动安装buildozer
# pip install buildozer cython
# buildozer init
# buildozer android debug

echo "=== APK生成在 bin/ 目录 ==="
ls -la bin/*.apk 2>/dev/null || echo "构建失败, 请检查上方日志"
