#!/usr/bin/env bash
# Day 5 步骤 4-7：拉镜像、建网络与卷、启动 MySQL 与 RabbitMQ、等待健康并校验端口边界
# 对应教材：Linux Day 5 → 分步操作 → 4./5./6./7.
#
# 端口边界（硬性要求）：
#   MySQL 3306      只绑 127.0.0.1
#   RabbitMQ 5672   只绑 127.0.0.1
#   管理页 15672    绑 VM 的 NAT IPv4，只对实验网开放
#
# 运行前必须先加载环境：
#   cd "$HOME/linux-lab"; set -a; source middleware/.env; set +a
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
MYSQL_IMAGE='docker.io/library/mysql:8.4.10'
RABBITMQ_IMAGE='docker.io/library/rabbitmq:4.3.3-management'
NETWORK='linux-lab-middleware'
MYSQL_VOLUME='linux-lab-mysql-data'
RABBITMQ_VOLUME='linux-lab-rabbitmq-data'

cd "$LAB_DIR"

for name in MYSQL_DATABASE MYSQL_USER MYSQL_PASSWORD MYSQL_ROOT_PASSWORD \
            RABBITMQ_DEFAULT_USER RABBITMQ_DEFAULT_PASS; do
  if [[ -z "${!name:-}" ]]; then
    echo "STOP: $name is not set; source middleware/.env first" >&2
    exit 1
  fi
done

echo '== step 4: images, network and named volumes =='
podman pull "$MYSQL_IMAGE"
podman pull "$RABBITMQ_IMAGE"
podman image inspect "$MYSQL_IMAGE" --format 'mysql={{.Id}}'
podman image inspect "$RABBITMQ_IMAGE" --format 'rabbitmq={{.Id}}'

podman network exists "$NETWORK" || podman network create "$NETWORK"
podman volume exists "$MYSQL_VOLUME" || podman volume create "$MYSQL_VOLUME"
podman volume exists "$RABBITMQ_VOLUME" || podman volume create "$RABBITMQ_VOLUME"

podman network inspect "$NETWORK"
podman volume inspect "$MYSQL_VOLUME" "$RABBITMQ_VOLUME"

echo '== step 5: MySQL, loopback only =='
# 数据放命名卷，不放容器可写层；init.sql 以只读方式挂进初始化目录
if podman container exists mysql-lab; then
  echo 'STOP: container mysql-lab already exists; inspect it before continuing' >&2
else
  podman run --detach \
    --name mysql-lab \
    --network "$NETWORK" \
    --hostname mysql-lab \
    --publish 127.0.0.1:3306:3306 \
    --volume "$MYSQL_VOLUME:/var/lib/mysql:Z" \
    --volume "$PWD/middleware/init.sql:/docker-entrypoint-initdb.d/10-init.sql:Z,ro" \
    --env MYSQL_ROOT_PASSWORD="$MYSQL_ROOT_PASSWORD" \
    --env MYSQL_DATABASE="$MYSQL_DATABASE" \
    --env MYSQL_USER="$MYSQL_USER" \
    --env MYSQL_PASSWORD="$MYSQL_PASSWORD" \
    --health-cmd 'mysqladmin ping --host=127.0.0.1 --user=root --password="$MYSQL_ROOT_PASSWORD" --silent' \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 12 \
    "$MYSQL_IMAGE"
fi

echo '== step 6: resolve the VM address for the management UI =='
DEFAULT_IF="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
VM_IP="$(
  ip -o -4 addr show dev "$DEFAULT_IF" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
)"
FIREWALL_ZONE="$(sudo firewall-cmd --get-zone-of-interface="$DEFAULT_IF")"
printf 'VM_IP=%s FIREWALL_ZONE=%s\n' "$VM_IP" "$FIREWALL_ZONE"

echo '== step 6: RabbitMQ, AMQP on loopback and the UI on the NAT address =='
if [[ -z "$VM_IP" || -z "$FIREWALL_ZONE" || "$FIREWALL_ZONE" == 'no zone' ]]; then
  echo 'STOP: VM IP or firewalld zone is unavailable' >&2
  exit 1
elif podman container exists rabbitmq-lab; then
  echo 'STOP: container rabbitmq-lab already exists; inspect it before continuing' >&2
else
  podman run --detach \
    --name rabbitmq-lab \
    --network "$NETWORK" \
    --hostname rabbitmq-lab \
    --publish 127.0.0.1:5672:5672 \
    --publish "${VM_IP}:15672:15672" \
    --volume "$RABBITMQ_VOLUME:/var/lib/rabbitmq:Z" \
    --env RABBITMQ_DEFAULT_USER="$RABBITMQ_DEFAULT_USER" \
    --env RABBITMQ_DEFAULT_PASS="$RABBITMQ_DEFAULT_PASS" \
    --health-cmd 'rabbitmq-diagnostics -q ping' \
    --health-interval 10s \
    --health-timeout 5s \
    --health-retries 12 \
    "$RABBITMQ_IMAGE"
fi

echo '== step 6: firewall rule for the management UI only =='
# 3306 和 5672 根本没绑 VM 外部地址，不需要也不允许加外部规则
sudo firewall-cmd --permanent --zone="$FIREWALL_ZONE" --add-port=15672/tcp
sudo firewall-cmd --reload
sudo firewall-cmd --zone="$FIREWALL_ZONE" --query-port=15672/tcp

echo '== step 7: wait until both containers are healthy =='
wait_for_healthy() {
  local container_name="$1"
  local attempt
  local health

  for attempt in $(seq 1 60); do
    health="$(
      podman inspect "$container_name" \
        --format '{{if .State.Health}}{{.State.Health.Status}}{{else}}none{{end}}'
    )"
    printf '%s health=%s attempt=%s\n' "$container_name" "$health" "$attempt"
    if [[ "$health" == 'healthy' ]]; then
      return 0
    fi
    if [[ "$health" == 'unhealthy' ]]; then
      podman logs --tail 80 "$container_name"
      return 1
    fi
    sleep 5
  done

  podman logs --tail 80 "$container_name"
  return 1
}

wait_for_healthy mysql-lab
wait_for_healthy rabbitmq-lab

podman ps
podman logs --tail 30 mysql-lab
podman logs --tail 30 rabbitmq-lab
ss -lnt | grep -E ':(3306|5672|15672)\b'

echo '== step 7: private port boundary check =='
PRIVATE_LISTENERS="$(ss -lntH | awk '{print $4}')"
if grep -Fxq '127.0.0.1:3306' <<<"$PRIVATE_LISTENERS" &&
   grep -Fxq '127.0.0.1:5672' <<<"$PRIVATE_LISTENERS" &&
   ! grep -Eq '(^0\.0\.0\.0|\[::\]):(3306|5672)$' <<<"$PRIVATE_LISTENERS"; then
  echo 'PRIVATE PORT CHECK PASSED'
else
  echo 'STOP: MySQL or AMQP is missing its loopback listener or is exposed externally' >&2
  exit 1
fi

cat <<NOTE

RabbitMQ 管理页（用户名 labmq，密码在本地 .env）：
  Windows PowerShell 7:
    \$VmIp = '$VM_IP'
    Test-NetConnection -ComputerName \$VmIp -Port 15672
    Start-Process "http://\${VmIp}:15672/"

停止/恢复：
  podman stop --time 30 mysql-lab     ; podman start mysql-lab
  podman stop --time 30 rabbitmq-lab  ; podman start rabbitmq-lab
NOTE
