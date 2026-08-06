#!/usr/bin/env bash
# Day 4 步骤 8-12：kubectl 观察 → 扩缩容 → Pod 自愈 → 错误镜像与回滚 → 采集证据
# 对应教材：Linux Day 4 → 分步操作 → 8./9./10./11./12.
#
# 用法：./04-ops-drills.sh {observe|scale|selfheal|rollback|evidence|all}
set -Eeuo pipefail

export LC_ALL=C

LAB_DIR="$HOME/linux-lab"
KUBECTL='/usr/local/bin/kubectl'
NS='linux-lab'
DEPLOY='linux-lab-web'
SELECTOR='app.kubernetes.io/name=linux-lab-web'

cd "$LAB_DIR"

vm_ip() {
  local iface
  iface="$(ip -4 route show default | awk 'NR == 1 {print $5}')"
  ip -o -4 addr show dev "$iface" scope global |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}'
}

drill_observe() {
  echo '== step 8: get / describe / logs / exec =='
  # get 看摘要，describe 看详细状态和事件，logs 看容器输出，exec 进容器执行
  sudo "$KUBECTL" get namespaces
  sudo "$KUBECTL" -n "$NS" get deployment,replicaset,pod,service -o wide
  sudo "$KUBECTL" -n "$NS" describe deployment "$DEPLOY"
  sudo "$KUBECTL" -n "$NS" describe service "$DEPLOY"
  sudo "$KUBECTL" -n "$NS" logs --selector "$SELECTOR" --tail=20 --prefix
  sudo "$KUBECTL" -n "$NS" exec "deployment/$DEPLOY" -- wget -qO- http://127.0.0.1/
}

drill_scale() {
  echo '== step 9: scale to 3, then let the file win again =='
  sudo "$KUBECTL" -n "$NS" scale "deployment/$DEPLOY" --replicas=3
  sudo "$KUBECTL" -n "$NS" rollout status "deployment/$DEPLOY" --timeout=120s
  sudo "$KUBECTL" -n "$NS" get pods

  # scale 只改了集群里的 live object，没有改文件；
  # 重新 apply YAML，副本数回到文件声明的 2 —— 这就是声明式配置的价值。
  sudo "$KUBECTL" apply --filename k8s/web.yaml
  sudo "$KUBECTL" -n "$NS" rollout status "deployment/$DEPLOY" --timeout=120s
  sudo "$KUBECTL" -n "$NS" get deployment "$DEPLOY"
}

drill_selfheal() {
  echo '== step 10: delete one pod and watch the ReplicaSet restore it =='
  sudo "$KUBECTL" -n "$NS" get pods -l "$SELECTOR" -o wide
  POD_TO_DELETE="$(
    sudo "$KUBECTL" -n "$NS" get pods -l "$SELECTOR" \
      -o jsonpath='{.items[0].metadata.name}'
  )"
  printf 'Deleting pod: %s\n' "$POD_TO_DELETE"
  sudo "$KUBECTL" -n "$NS" delete pod "$POD_TO_DELETE"

  # 不是被删的 Pod「复活」，而是 Deployment 经 ReplicaSet 新建了一个 Pod
  sudo "$KUBECTL" -n "$NS" wait \
    --for=condition=Available "deployment/$DEPLOY" --timeout=120s
  sudo "$KUBECTL" -n "$NS" get pods
}

drill_rollback() {
  echo '== step 11: inject a bad image, locate the error, then roll back =='
  sudo "$KUBECTL" -n "$NS" rollout history "deployment/$DEPLOY"
  sudo "$KUBECTL" -n "$NS" get deployment "$DEPLOY" \
    -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'

  sudo "$KUBECTL" -n "$NS" set image "deployment/$DEPLOY" \
    web=localhost/linux-lab-web:does-not-exist
  sudo "$KUBECTL" -n "$NS" rollout status "deployment/$DEPLOY" --timeout=60s || true
  sudo "$KUBECTL" -n "$NS" get pods -o wide

  FAILED_POD="$(
    sudo "$KUBECTL" -n "$NS" get pods \
      --sort-by=.metadata.creationTimestamp \
      -o jsonpath='{.items[-1:].metadata.name}'
  )"
  printf 'Inspecting pod: %s\n' "$FAILED_POD"
  # imagePullPolicy 是 Never，所以事件通常是 ErrImageNeverPull：
  # 证明 K3s containerd 没有这个标签，不是 Nginx 应用本身报错
  sudo "$KUBECTL" -n "$NS" describe pod "$FAILED_POD"
  sudo "$KUBECTL" -n "$NS" get events \
    --sort-by=.metadata.creationTimestamp | tail -n 30

  sudo "$KUBECTL" -n "$NS" rollout undo "deployment/$DEPLOY"
  sudo "$KUBECTL" -n "$NS" rollout status "deployment/$DEPLOY" --timeout=180s
  sudo "$KUBECTL" -n "$NS" get pods
  sudo "$KUBECTL" -n "$NS" get deployment "$DEPLOY" \
    -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
  curl --fail "http://$(vm_ip):30080/" | grep 'Linux Lab Web 0.1'

  # 最后再 apply 一次，确保 live state 与仓库一致
  sudo "$KUBECTL" apply --filename k8s/web.yaml
}

drill_evidence() {
  echo '== step 12: collect evidence =='
  # 不要把 /etc/rancher/k3s/k3s.yaml 写进 evidence 或 Git
  {
    echo '== k3s version =='
    sudo /usr/local/bin/k3s --version
    echo '== node =='
    sudo "$KUBECTL" get nodes -o wide
    echo '== workload =='
    sudo "$KUBECTL" -n "$NS" get deployment,pods,service -o wide
    echo '== image =='
    sudo "$KUBECTL" -n "$NS" get deployment "$DEPLOY" \
      -o jsonpath='{.spec.template.spec.containers[0].image}{"\n"}'
    echo '== security =='
    getenforce
    systemctl is-active firewalld
    rpm -q k3s-selinux
  } | tee evidence/day04-k3s.txt

  cat <<'NOTE'

提交：
  git add k8s/web.yaml \
    evidence/day04-k3s-installer.sha256 \
    evidence/day04-k3s.txt
  git commit -m "feat: deploy web lab to single-node K3s"
NOTE
}

case "${1:-all}" in
  observe)  drill_observe ;;
  scale)    drill_scale ;;
  selfheal) drill_selfheal ;;
  rollback) drill_rollback ;;
  evidence) drill_evidence ;;
  all)
    drill_observe
    drill_scale
    drill_selfheal
    drill_rollback
    drill_evidence
    ;;
  *)
    echo "usage: $0 {observe|scale|selfheal|rollback|evidence|all}" >&2
    exit 2
    ;;
esac
