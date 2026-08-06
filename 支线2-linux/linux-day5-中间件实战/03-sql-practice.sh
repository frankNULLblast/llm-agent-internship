#!/usr/bin/env bash
# Day 5 步骤 9：SQL 练习 —— 建表、插入、COMMIT 与 ROLLBACK 的行为对比
# 对应教材：Linux Day 5 → 分步操作 → 9. 练习 SQL、提交与回滚
#
# 密码通过 MYSQL_PWD 环境变量传入容器，不出现在命令行参数里。
# 运行前必须先 source middleware/.env。
set -Eeuo pipefail

export LC_ALL=C

for name in MYSQL_USER MYSQL_PASSWORD MYSQL_DATABASE; do
  if [[ -z "${!name:-}" ]]; then
    echo "STOP: $name is not set; source middleware/.env first" >&2
    exit 1
  fi
done

echo '== transaction semantics drill =='
podman exec -i \
  --env MYSQL_PWD="$MYSQL_PASSWORD" \
  mysql-lab \
  mysql --user="$MYSQL_USER" "$MYSQL_DATABASE" <<'SQL'
SHOW DATABASES;
SHOW TABLES;
DESCRIBE lab_events;

CREATE TABLE IF NOT EXISTS day5_sql_practice (
  id INT NOT NULL PRIMARY KEY,
  item VARCHAR(32) NOT NULL,
  status VARCHAR(16) NOT NULL
) ENGINE=InnoDB;

DELETE FROM day5_sql_practice;
INSERT INTO day5_sql_practice (id, item, status)
VALUES
  (1, 'network', 'new'),
  (2, 'container', 'new');

SELECT * FROM day5_sql_practice ORDER BY id;

START TRANSACTION;
UPDATE day5_sql_practice SET status = 'rollback-demo' WHERE id = 1;
SELECT * FROM day5_sql_practice WHERE id = 1;
ROLLBACK;
SELECT * FROM day5_sql_practice WHERE id = 1;

START TRANSACTION;
UPDATE day5_sql_practice SET status = 'done' WHERE id = 2;
COMMIT;
SELECT * FROM day5_sql_practice ORDER BY id;

DROP TABLE day5_sql_practice;
SHOW TABLES;
SQL

# 精确检查：
#   回滚后 id=1 的 status 仍是 new
#   提交后 id=2 的 status 是 done
#   最后只剩业务表 lab_events

echo '== business table should still be empty =='
podman exec \
  --env MYSQL_PWD="$MYSQL_PASSWORD" \
  mysql-lab \
  mysql --batch --skip-column-names \
  --user="$MYSQL_USER" "$MYSQL_DATABASE" \
  --execute 'SELECT COUNT(*) FROM lab_events;'
# 预期精确输出 0
