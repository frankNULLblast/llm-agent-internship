#!/usr/bin/env bash
# Day 3 步骤 6：用龙蜥官方镜像对比容器与宿主机，观察可写层的生命周期
# 对应教材：Linux Day 3 → 分步操作 → 6. 运行龙蜥 8.10 容器并比较宿主机
set -Eeuo pipefail

export LC_ALL=C

ANOLIS_IMAGE='registry.openanolis.cn/openanolis/anolisos:8.10'

echo '== pull =='
podman pull "$ANOLIS_IMAGE"
podman image inspect "$ANOLIS_IMAGE" \
  --format 'id={{.Id}} created={{.Created}}'

echo '== host =='
cat /etc/os-release
uname -r
ps -eo pid,user,comm | head

echo '== container =='
# 容器内 /etc/os-release 是龙蜥 8.10 用户空间，
# 但 uname -r 与宿主机一致 —— 容器共享宿主机内核。
podman run --rm "$ANOLIS_IMAGE" cat /etc/os-release
podman run --rm "$ANOLIS_IMAGE" uname -r
# 不依赖容器内是否装了 ps，直接数 /proc 里的进程目录，观察 PID namespace 隔离
podman run --rm "$ANOLIS_IMAGE" \
  sh -c 'printf "PID 1: "; cat /proc/1/comm; set -- /proc/[0-9]*; printf "visible process directories: %s\n" "$#"'

echo '== writable layer lifecycle =='
podman run --detach --name disposable "$ANOLIS_IMAGE" \
  sh -c 'if test -e /tmp/proof.txt; then echo proof-already-existed; else printf "container-layer\n" > /tmp/proof.txt; echo proof-created; fi; exec sleep 600'
podman exec disposable cat /tmp/proof.txt
podman stop disposable
podman start disposable
# 日志应先 proof-created，重启后 proof-already-existed：
# 同一容器的可写层在 stop/start 之间保留
podman logs disposable
podman exec disposable cat /tmp/proof.txt
podman rm -f disposable

# 删掉容器后，新容器不该继承旧可写层里的文件，退出码应为 0
podman run --rm "$ANOLIS_IMAGE" test ! -e /tmp/proof.txt
printf 'fresh_container_has_no_old_file_exit_code=%s\n' "$?"
