#!/bin/bash
# Docker 镜像加速器配置脚本（Linux）

set -e

DAEMON_JSON="/etc/docker/daemon.json"
BACKUP_FILE="/etc/docker/daemon.json.backup.$(date +%Y%m%d_%H%M%S)"

echo "=== Docker 镜像加速器配置脚本 ==="
echo ""

# 检查是否为 root 用户
if [ "$EUID" -ne 0 ]; then 
    echo "错误: 请使用 root 权限运行此脚本"
    echo "使用方法: sudo bash $0"
    exit 1
fi

# 备份现有配置
if [ -f "$DAEMON_JSON" ]; then
    echo "备份现有配置到: $BACKUP_FILE"
    cp "$DAEMON_JSON" "$BACKUP_FILE"
fi

# 创建配置目录
mkdir -p /etc/docker

# 创建新的 daemon.json 配置
echo "创建/更新 daemon.json 配置..."
cat > "$DAEMON_JSON" << 'EOF'
{
  "registry-mirrors": [
    "https://dockerproxy.com",
    "https://docker.mirrors.ustc.edu.cn",
    "https://hub-mirror.c.163.com",
    "https://mirror.baidubce.com",
    "https://docker.nju.edu.cn"
  ],
  "max-concurrent-downloads": 10,
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
EOF

echo "✓ 配置文件已创建: $DAEMON_JSON"
echo ""
echo "配置内容："
cat "$DAEMON_JSON" | python3 -m json.tool 2>/dev/null || cat "$DAEMON_JSON"
echo ""

# 验证 JSON 格式
echo "验证 JSON 格式..."
if python3 -m json.tool "$DAEMON_JSON" > /dev/null 2>&1; then
    echo "✓ JSON 格式正确"
else
    echo "✗ JSON 格式错误！"
    exit 1
fi

echo ""
echo "=== 重启 Docker 服务 ==="
echo "重新加载 systemd 配置..."
systemctl daemon-reload

echo "重启 Docker 服务..."
systemctl restart docker

echo "等待 Docker 服务启动..."
sleep 3

# 检查 Docker 服务状态
if systemctl is-active --quiet docker; then
    echo "✓ Docker 服务运行正常"
else
    echo "✗ Docker 服务启动失败！"
    echo "查看日志: journalctl -u docker -n 50"
    exit 1
fi

echo ""
echo "=== 验证镜像源配置 ==="
docker info 2>/dev/null | grep -A 10 "Registry Mirrors" || echo "警告: 未在 docker info 中看到镜像源配置"

echo ""
echo "=== 配置完成 ==="
echo "现在可以尝试拉取镜像："
echo "  docker pull openjdk:17-alpine"
echo ""
echo "如果仍然失败，可以尝试："
echo "  1. 检查网络连接"
echo "  2. 检查防火墙设置"
echo "  3. 查看 Docker 日志: journalctl -u docker -f"

