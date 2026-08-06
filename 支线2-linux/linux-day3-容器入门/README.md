# Linux Day 3：容器入门

对应教材：`大模型、智能体学习 plus（linux）.md` → **Linux Day 3：Linux 网络与 Podman 容器**（第 1615–2311 行）。

## 这天做了什么

上半天把网络排错的固定顺序走一遍，下半天用 rootless Podman 把一个 Nginx 页面做成镜像跑起来，并导出 OCI 包给 Day 4 的 K3s 用。

两条主线：

1. **网络**：按 `地址 → 路由 → DNS → 端口/防火墙 → 应用与日志` 五层逐级验证，用 `python3 -m http.server` 起一个临时 Web，只加**运行时**防火墙规则，验证完再撤掉，证明"需要时开放、不用时删除"。
2. **容器**：安装 rootless Podman，用龙蜥官方镜像对比容器与宿主机（共享内核、PID namespace 隔离、可写层生命周期），然后构建 `localhost/linux-lab-web:0.1`，练只读 bind mount 与命名卷，最后 `podman save` 成 OCI archive。

固定输入（教材约定）：

| 项目 | 固定值 |
|---|---|
| 临时 Web 端口 | `8000/tcp`，**只用运行时规则** |
| Podman Web 端口 | `<VM_IP>:8080`，持久规则，Day 3 结束时撤销 |
| 龙蜥容器镜像 | `registry.openanolis.cn/openanolis/anolisos:8.10` |
| Nginx 基础镜像 | `docker.io/library/nginx:1.30.4-alpine` |
| 本地镜像 | `localhost/linux-lab-web:0.1` |
| 命名卷 | `linux-lab-web-data` |
| OCI 包 | `web/linux-lab-web-0.1.oci` |
| DNS 超时靶子 | `192.0.2.1`（RFC 5737 文档网段） |

## 本目录内容

| 文件 | 对应教材小节 | 作用 |
|---|---|---|
| `01-network-diagnose.sh` | 分步操作 1–3 | 五层网络检查 + DNS 超时演练 + 端口/firewalld 检查（只读） |
| `02-temp-http-drill.sh` | 分步操作 4 | 临时 Web 的 `open` / `verify` / `close` 三段式演练 |
| `03-podman-setup.sh` | 分步操作 5 | 安装 Podman、确认 rootless、配置 subuid 与 linger |
| `04-container-concepts.sh` | 分步操作 6 | 容器 vs 宿主机对比、可写层随容器删除消失 |
| `05-build-run-web.sh` | 分步操作 7–8 | 构建并运行 `linux-lab-web:0.1`，开放 8080 |
| `06-volumes-and-export.sh` | 分步操作 9–10 | 只读挂载、命名卷、容器重建、导出 OCI 包 + 采集证据 |
| `web/Containerfile` | 分步操作 7 | 镜像定义：固定基础镜像 + COPY 页面 + EXPOSE + HEALTHCHECK |
| `web/index.html` | 分步操作 7 | 镜像里的固定页面，标题 `Linux Lab Web 0.1` |

实跑时把 `web/` 放到虚拟机的 `~/linux-lab/web/`，脚本都按这个路径写。

## 关键命令

确认 rootless（主线所有容器命令都不加 `sudo`）：

```bash
podman info --format 'rootless={{.Host.Security.Rootless}}'   # 预期 true
loginctl show-user intern -p Linger                            # 预期 Linger=yes
```

容器与宿主机的关键对比：

```bash
podman run --rm registry.openanolis.cn/openanolis/anolisos:8.10 cat /etc/os-release  # 龙蜥用户空间
podman run --rm registry.openanolis.cn/openanolis/anolisos:8.10 uname -r             # 与宿主机相同
```

构建并运行：

```bash
podman pull docker.io/library/nginx:1.30.4-alpine
podman build --pull=never --tag localhost/linux-lab-web:0.1 --file web/Containerfile web
podman run --detach --name linux-lab-web --publish "${VM_IP}:8080:80" localhost/linux-lab-web:0.1
curl --fail "http://${VM_IP}:8080/" | grep 'Linux Lab Web 0.1'
```

导出给 Day 4：

```bash
podman save --format oci-archive --output web/linux-lab-web-0.1.oci localhost/linux-lab-web:0.1
sha256sum web/linux-lab-web-0.1.oci | tee evidence/day03-image.sha256
```

## 预期结果

- 地址、默认路由、DNS 三项能各自独立验证通过；
- 对 `192.0.2.1` 的 DNS 查询超时（非 0 退出码），随后用系统 DNS 查询仍正常 —— 说明是这台 DNS 不可达，不是整个网络断了；
- 临时 Web 开着时 Windows 能拿到 `200` 且正文含 `temporary web works`；`close` 之后 `--query-port` 输出 `no`，再访问失败；
- `podman info` 报告 `rootless=true`；
- 容器内 `/etc/os-release` 是龙蜥 8.10，但 `uname -r` 与宿主机一致；容器里能看到的 `/proc/[0-9]*` 目录数远少于宿主机；
- `disposable` 容器日志先 `proof-created`，stop/start 后 `proof-already-existed`；`podman rm -f` 后新容器里没有 `/tmp/proof.txt`（退出码 `0`）；
- Web 容器约 10–20 秒后 `health=healthy`，页面含 `Linux Lab Web 0.1`；
- 只读挂载里写文件失败；命名卷两次读取都输出 `named-volume-survives`；
- 删掉容器后 `podman image exists` 退出码仍是 `0` —— 容器和镜像不是同一个对象。

> 说明：这些脚本没有在当前 Windows 机器上执行（对象是 VMware 里的 Anolis 虚拟机），所以本目录不放输出文件。以上是教材规定的**预期行为**；实跑后的真实输出由 `06-volumes-and-export.sh` 写进虚拟机的 `~/linux-lab/evidence/day03-network-container.txt`。

## Podman 与 Docker 命令对照

教材以 Podman 为唯一主线，这张表只用于读懂其他资料：

| 任务 | Podman | Docker |
|---|---|---|
| 查看版本 | `podman --version` | `docker --version` |
| 拉镜像 | `podman pull IMAGE` | `docker pull IMAGE` |
| 构建镜像 | `podman build -t NAME .` | `docker build -t NAME .` |
| 运行容器 | `podman run ...` | `docker run ...` |
| 列出运行中容器 | `podman ps` | `docker ps` |
| 含已停止容器 | `podman ps -a` | `docker ps -a` |
| 查看日志 | `podman logs NAME` | `docker logs NAME` |
| 容器内执行 | `podman exec NAME CMD` | `docker exec NAME CMD` |
| 查看详情 | `podman inspect NAME` | `docker inspect NAME` |
| 停止/启动 | `podman stop/start NAME` | `docker stop/start NAME` |
| 删除容器 | `podman rm NAME` | `docker rm NAME` |
| 管理卷 | `podman volume ...` | `docker volume ...` |
| 保存镜像 | `podman save` | `docker save` |

主要差异：Podman 没有必须常驻的中央 daemon，并且原生支持普通用户 rootless 工作流。命令相似**不代表**权限、网络和 systemd 行为完全相同。

## 注意事项

- `podman save` 保存镜像及元数据，可用于 Day 4 导入；`podman export` 只导出容器的合并文件系统，**不能**用来给 K3s 导入镜像；
- 删容器不会删镜像，也不会删命名卷；只有容器自己的可写层随容器消失；
- `*.oci` 必须在 `.gitignore` 里，包大且可重建；
- Day 3 收尾要撤掉 8080 的持久规则，但保留镜像、OCI 包和命名卷。
