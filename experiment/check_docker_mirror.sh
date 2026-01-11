#!/bin/bash
# Docker 镜像加速器检查和配置脚本

echo "=== 检查 Docker daemon.json 配置 ==="
echo ""

# 检查配置文件是否存在
if [ -f /etc/docker/daemon.json ]; then
    echo "✓ 找到配置文件: /etc/docker/daemon.json"
    echo "当前配置内容："
    cat /etc/docker/daemon.json | python3 -m json.tool 2>/dev/null || cat /etc/docker/daemon.json
    echo ""
else
    echo "✗ 配置文件不存在: /etc/docker/daemon.json"
    echo ""
fi

# 检查 Docker 信息中的镜像源配置
echo "=== 检查 Docker 系统信息 ==="
docker info 2>/dev/null | grep -A 10 "Registry Mirrors" || echo "未找到镜像源配置"
echo ""

# 检查 Docker 服务状态
echo "=== 检查 Docker 服务状态 ==="
systemctl status docker --no-pager -l | head -10
echo ""

echo "=== 测试镜像拉取 ==="
echo "尝试拉取测试镜像..."
docker pull hello-world:latest 2>&1 | head -5

