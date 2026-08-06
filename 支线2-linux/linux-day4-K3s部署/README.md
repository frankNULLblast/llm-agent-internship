# Linux Day 4：K3s 部署

对应教材：`大模型、智能体学习 plus（linux）.md` → **Linux Day 4：单节点 K3s 与 Kubernetes 核心对象**（第 2313–3097 行）。

## 这天做了什么

把 Day 3 用 Podman 构建的 `localhost/linux-lab-web:0.1` 搬进单节点 K3s，从"我亲自 run 一个容器"切换到"我声明期望状态，控制器负责逼近它"。

顺序是：cgroup v2 硬门禁 → firewalld 最小规则 → 下载并审阅 K3s 安装脚本 → 固定版本安装 → 导入 OCI 镜像 → apply manifest → NodePort 验证 → 一组运维演练（扩缩容 / Pod 自愈 / 错误镜像与回滚）。

固定输入（教材约定）：

| 项目 | 固定值 |
|---|---|
| K3s 版本 | `v1.36.2+k3s1` |
| 安装参数 | `server --selinux` |
| Pod CIDR | `10.42.0.0/16` |
| Service CIDR | `10.43.0.0/16` |
| Namespace | `linux-lab` |
| Deployment | `linux-lab-web`，副本数 `2` |
| 镜像 | `localhost/linux-lab-web:0.1`，`imagePullPolicy: Never` |
| 错误镜像（演练用） | `localhost/linux-lab-web:does-not-exist` |
| Service | `linux-lab-web`，NodePort `30080` |
| probe 路径 | `/` |
| 快照 | `day4-pre-k3s-cgroup`（改启动参数前）、`day4-k3s-ready` |

## 本目录内容

| 文件 | 对应教材小节 | 作用 |
|---|---|---|
| `01-preflight-cgroup.sh` | 分步操作 1 | cgroup v2 硬门禁：`check` / `enable` / `verify` / `rollback` 四段式 |
| `02-install-k3s.sh` | 分步操作 2–4 | firewalld trusted 网段 + 下载审阅安装脚本 + 固定版本安装 |
| `03-import-and-deploy.sh` | 分步操作 5–7 | 导入 OCI 镜像、dry-run、apply、开放 NodePort |
| `04-ops-drills.sh` | 分步操作 8–12 | 观察 / 扩缩容 / 自愈 / 错误镜像回滚 / 采集证据 |
| `k8s/web.yaml` | 分步操作 6 | Namespace + Deployment + Service 三个对象的完整 manifest |
| `附件/day04-k3s-evidence.txt` | 分步操作 12 | **真实运行证据**（见下节） |

## 关键命令

cgroup v2 门禁（Kubernetes 1.36 的 kubelet 默认拒绝 cgroup v1）：

```bash
stat -fc %T /sys/fs/cgroup                                    # 需要 cgroup2fs
podman info --format '{{.Host.CgroupsVersion}}'               # 需要 v2
sudo grubby --update-kernel="$DEFAULT_KERNEL" \
  --args='systemd.unified_cgroup_hierarchy=1'                 # 只改默认内核这一项
```

firewalld 最小规则（只放集群内部网段，不对外开 6443）：

```bash
sudo firewall-cmd --permanent --zone=trusted --add-source=10.42.0.0/16
sudo firewall-cmd --permanent --zone=trusted --add-source=10.43.0.0/16
sudo firewall-cmd --reload
```

安装（**不用** `curl | sh`）：

```bash
curl --fail --location --show-error https://get.k3s.io --output /tmp/install-k3s.sh
chmod 0700 /tmp/install-k3s.sh
sha256sum /tmp/install-k3s.sh | tee evidence/day04-k3s-installer.sha256
less /tmp/install-k3s.sh                # 人工通读
bash -n /tmp/install-k3s.sh             # 语法检查
sudo env INSTALL_K3S_VERSION='v1.36.2+k3s1' \
         INSTALL_K3S_EXEC='server --selinux' \
         sh /tmp/install-k3s.sh
```

导入镜像（Podman 与 K3s containerd 是两套独立存储）：

```bash
sha256sum -c evidence/day03-image.sha256
sudo /usr/local/bin/k3s ctr images import web/linux-lab-web-0.1.oci
sudo /usr/local/bin/k3s ctr images list | grep 'localhost/linux-lab-web:0.1'
```

部署与验证：

```bash
sudo /usr/local/bin/kubectl apply --filename k8s/web.yaml
sudo /usr/local/bin/kubectl -n linux-lab rollout status deployment/linux-lab-web --timeout=180s
curl --fail "http://${VM_IP}:30080/" | grep 'Linux Lab Web 0.1'
```

## 运行证据

`附件/day04-k3s-evidence.txt` 是这一天在虚拟机上实跑后采集的真实输出，关键行：

```text
k3s version v1.36.2+k3s1 (01b6f04a)
linux-lab   Ready   control-plane   16m   v1.36.2+k3s1   192.168.172.100   Anolis OS 8.10   containerd://2.3.2-k3s2
deployment.apps/linux-lab-web   2/2   2   2   ...   localhost/linux-lab-web:0.1
pod/linux-lab-web-786c76b499-bsr8d   1/1   Running   0   ...   10.42.0.12
pod/linux-lab-web-786c76b499-t4bmr   1/1   Running   0   ...   10.42.0.9
service/linux-lab-web   NodePort   10.43.7.149   80:30080/TCP
```

可以逐条对上教材的验收要求：

- **版本固定**：`v1.36.2+k3s1`，没有跟随 latest；
- **节点就绪**：`linux-lab` 是 `Ready`，角色 `control-plane`，单节点同时承担控制面和工作节点；
- **副本符合期望状态**：Deployment `2/2`，两个 Pod 都是 `1/1 Running`，Pod IP 落在 Pod CIDR `10.42.0.0/16` 内；
- **Service**：`NodePort`，ClusterIP `10.43.7.149` 落在 Service CIDR `10.43.0.0/16` 内，映射 `80:30080/TCP`；
- **安全机制没被绕过**：`Enforcing`（SELinux）、`active`（firewalld）、`k3s-selinux-1.6-1.el8.noarch` 已安装；
- **cgroup v2 生效**：`cgroup2fs`，且 `/proc/cmdline` 里能看到 `systemd.unified_cgroup_hierarchy=1`；
- **firewalld trusted**：`10.42.0.0/16 10.43.0.0/16`，NodePort 查询返回 `yes`；
- **NodePort 可访问**：返回页面含 `<h1>Linux Lab Web 0.1</h1>`；
- **rollout history** 有 REVISION 2 和 3，对应"注入错误镜像 → `rollout undo` 回滚"这一步留下的痕迹。

证据文件开头三行是 SSH 客户端关于后量子密钥交换算法的告警，属于采集时的终端提示，与 K3s 本身无关，原样保留未做删改。

## 预期结果（教材验收清单）

- `k3s` 服务 `enabled` + `active`，版本精确包含 `v1.36.2+k3s1`；
- `k3s-selinux` 已安装，SELinux 为 Enforcing，firewalld 为 active；
- 节点 `linux-lab` 为 `Ready`；
- Deployment `READY` 为 `2/2`，两个 Pod 均 `1/1 Running`；
- Windows 访问 `<VM_IP>:30080` 得到固定 HTML；
- 临时 `scale` 到 3 后，重新 `apply` YAML 恢复 2；
- 删除 Pod 后出现**名字不同**的新 Pod，并恢复 2 个 Ready；
- 错误镜像的事件能通过 `describe` 定位（`imagePullPolicy: Never` 下通常是 `ErrImageNeverPull`）；
- `rollout undo` 后镜像回到 `0.1`，NodePort 恢复。

## 红线

- **kubeconfig 权限边界**：`/etc/rancher/k3s/k3s.yaml` 等同集群管理员钥匙。统一用 `sudo /usr/local/bin/kubectl`，不复制到普通用户家目录、不 `chmod 644`、不提交到 Git、不写进 evidence。
- 不执行来源不明的 `curl ... | sh`；先下载成文件、阅读、记录校验值再执行。
- 门禁不通过时**不得**用关闭 SELinux、停用 firewalld、`FailCgroupV1=false`、降级 K3s 或换发行版来绕过；正确做法是保存现象后停止 Day 4，必要时恢复 `day4-pre-k3s-cgroup` 快照。
- 改启动参数只针对"当前正在使用且同时是默认项"的内核，保留其他内核作为恢复入口。
- 单节点实验不对外开放 API `6443`；多节点才需要的 `6443/tcp`、Flannel `8472/udp` 不在本教程范围。

## 概念要点

- `Deployment → ReplicaSet → Pod` 是三层关系：删掉一个 Pod 不是它"复活"，而是 ReplicaSet 新建了一个来恢复期望副本数；
- `scale` 改的是集群里的 live object，**不改文件**；重新 `apply` 后文件里的声明重新生效 —— 这就是把 YAML 放进 Git 作为可审查期望状态的价值；
- **readiness probe** 失败时 Pod 暂时不接 Service 流量，**liveness probe** 连续失败时 kubelet 会重启容器，两者不能互相替代；
- `requests` 用于调度决策，`limits` 是运行上限。
