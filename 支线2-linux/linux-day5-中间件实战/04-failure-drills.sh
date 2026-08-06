#!/usr/bin/env bash
# Day 5 步骤 14-17：空队列 / 坏 JSON / 数据库失败 / 事务中途失败 / 消息持久化
# 对应教材：Linux Day 5 → 分步操作 → 14./15./16./17.
#
# 这组演练共同证明一件事：数据库成功提交前不 ACK，提交后才 ACK。
#
# 运行前：
#   cd "$HOME/linux-lab"
#   source .venv/bin/activate
#   set -a; source middleware/.env; set +a
#
# 用法：./04-failure-drills.sh {empty|malformed|baddb|txnfail|happy|durable}
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
cd "$LAB_DIR"

for name in MYSQL_USER MYSQL_PASSWORD MYSQL_DATABASE RABBITMQ_DEFAULT_USER; do
  if [[ -z "${!name:-}" ]]; then
    echo "STOP: $name is not set; source middleware/.env first" >&2
    exit 1
  fi
done

list_queues() {
  podman exec rabbitmq-lab \
    rabbitmqctl -q list_queues \
    name messages_ready messages_unacknowledged durable
}

count_events() {
  podman exec \
    --env MYSQL_PWD="$MYSQL_PASSWORD" \
    mysql-lab \
    mysql --batch --skip-column-names \
    --user="$MYSQL_USER" "$MYSQL_DATABASE" \
    --execute 'SELECT COUNT(*) FROM lab_events;'
}

case "${1:-}" in
  empty)
    # 第一次运行消费者会声明 durable 队列，但没有消息
    echo '== step 14: empty queue =='
    python middleware/consume_once.py || printf 'exit_code=%s\n' "$?"
    list_queues
    # 预期：打印 QUEUE_EMPTY，退出码 2，ready/unacked 均为 0
    ;;

  malformed)
    echo '== step 15: malformed JSON is NACKed and requeued =='
    python middleware/send_event.py --malformed-test
    list_queues
    python middleware/consume_once.py || printf 'exit_code=%s\n' "$?"
    list_queues
    # 预期：PROCESSING_FAILED: JSONDecodeError...，退出码 1，
    #       消息因 NACK(requeue=True) 仍有 messages_ready=1

    # 只清空这个固定测试队列。确认队列名精确是 linux.events，
    # 且里面只有刚才故意造的坏消息；不要在共享或生产 RabbitMQ 上运行。
    podman exec rabbitmq-lab rabbitmqctl purge_queue linux.events
    podman exec rabbitmq-lab \
      rabbitmqctl -q list_queues name messages_ready messages_unacknowledged
    ;;

  baddb)
    echo '== step 16: wrong database password =='
    podman exec \
      --env MYSQL_PWD="$MYSQL_PASSWORD" \
      mysql-lab \
      mysql --user="$MYSQL_USER" "$MYSQL_DATABASE" \
      --execute 'DELETE FROM lab_events;'

    python middleware/send_event.py
    list_queues

    # 一次性错误密码，不改动当前 shell 里的真实密码
    MYSQL_PASSWORD='intentionally-wrong-for-test' \
      python middleware/consume_once.py || printf 'exit_code=%s\n' "$?"
    list_queues
    # 预期：MySQL 认证失败，退出码 1，消息重新变成 ready
    ;;

  txnfail)
    echo '== step 16: duplicate key inside the same transaction =='
    python middleware/consume_once.py --transaction-failure-test ||
      printf 'exit_code=%s\n' "$?"
    list_queues
    count_events
    # 预期：IntegrityError，退出码 1，队列 ready 仍为 1，数据库计数仍为 0。
    # 第一条 INSERT 已在事务内执行，但随后的错误让整个事务回滚。
    ;;

  happy)
    echo '== step 16: normal consumption =='
    python middleware/consume_once.py
    list_queues
    podman exec \
      --env MYSQL_PWD="$MYSQL_PASSWORD" \
      mysql-lab \
      mysql --table \
      --user="$MYSQL_USER" "$MYSQL_DATABASE" \
      --execute 'SELECT id,event_id,intern_name,event_type,created_at FROM lab_events ORDER BY id;'
    # 预期：队列为 0，数据库精确 1 行
    ;;

  durable)
    echo '== step 17: the message survives a container rebuild =='
    python middleware/send_event.py
    list_queues
    # 预期：linux.events 是 durable，ready 为 1

    # 只删容器本身，保留命名卷
    podman stop --time 30 rabbitmq-lab
    podman rm rabbitmq-lab
    podman volume exists linux-lab-rabbitmq-data

    cat <<'NOTE'
容器已删除，命名卷保留。现在用相同名称、hostname、网络、卷和本地密码重建：
  ./02-start-middleware.sh
重建后再次 list_queues，durable 队列和 ready=1 的持久消息应当还在，
然后可以用 ./04-failure-drills.sh happy 正常消费掉它。
NOTE
    ;;

  *)
    echo "usage: $0 {empty|malformed|baddb|txnfail|happy|durable}" >&2
    exit 2
    ;;
esac
