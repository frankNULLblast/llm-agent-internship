# Linux Day 1：裸金属起步

对应教材：`大模型、智能体学习 plus（linux）.md` → **Linux Day 1：VMware、龙蜥安装、首次登录与 SSH**（第 293–826 行），以及全局约定第 1.1–2.3 节。

## 这天做了什么

从零把实验环境搭起来：在 Windows 宿主机上装 VMware Workstation Pro 26H1，创建固定规格的 `linux-lab` 虚拟机，安装 Anolis OS 8.10 最小化系统，用普通用户 `intern` 首次登录，完成系统更新、基础工具安装、三个基础服务启用，再从 Windows 通过 SSH/scp 打通，最后建立 `~/linux-lab` 学习仓库并留下第一份基线证据。

固定参数（教材硬性约定，不可自行更改）：

| 项目 | 固定值 |
|---|---|
| 虚拟机名 | `linux-lab` |
| 主机名 | `linux-lab` |
| 普通用户 | `intern`（属于 `wheel` 组） |
| 资源 | 4 vCPU / 8GB RAM / 80GB SCSI 系统盘 |
| 网络 | VMware NAT |
| 系统 | Anolis OS 8.10 x86_64，Minimal Install |
| ISO | `AnolisOS-8.10-x86_64-dvd.iso`，18,442,354,688 字节，MD5 `88ebd69a5b25c90d28b86e444cf767e8` |
| 快照 | `day1-clean-install` |

## 本目录脚本

按顺序执行，每个脚本都对应教材里的一节：

| 脚本 | 对应教材小节 | 作用 | 是否修改系统 |
|---|---|---|---|
| `01-identity-check.sh` | 分步操作 4 | 身份、主机名、系统版本、时区检查 | 否（只读） |
| `02-hardware-network-check.sh` | 分步操作 5 | 内存/磁盘/网卡/路由/DNS/外网连通性 | 否（只读） |
| `03-install-base-tools.sh` | 分步操作 6 | `dnf upgrade` + 安装教材固定的基础工具清单 | **是** |
| `04-services-and-firewall.sh` | 分步操作 7 | 启用 sshd/firewalld/vmtoolsd，确认 firewalld 放行 ssh | **是** |
| `05-baseline-evidence.sh` | 分步操作 10 | 建 `~/linux-lab` 仓库、写 `.gitignore`、生成 `evidence/day01-system.txt` | 是（仅家目录） |

`03` 执行完可能装上新内核，需要手动 `sudo reboot` 后再跑 `04`。

## 关键命令

首次登录的身份检查：

```bash
whoami            # 应为 intern
id                # 组列表应含 wheel
hostnamectl       # Static hostname 应为 linux-lab
cat /etc/anolis-release
timedatectl       # 时区应为 Asia/Shanghai
```

取虚拟机 IP（后面几天反复用到，`VM_IF` 常见为 `ens33`，但以实际输出为准）：

```bash
VM_IF=$(ip route show default | awk 'NR == 1 {print $5}')
VM_IP=$(ip -4 -o address show dev "$VM_IF" |
    awk 'NR == 1 {split($4, address, "/"); print address[1]}')
printf '默认网卡：%s\n虚拟机IP：%s\n' "$VM_IF" "$VM_IP"
```

启用并检查三个基础服务：

```bash
sudo systemctl enable --now sshd
sudo systemctl enable --now firewalld
sudo systemctl enable --now vmtoolsd
getenforce
```

从 Windows PowerShell 7 连过来（`$vmIp` 换成上面算出的真实地址）：

```powershell
$vmIp = '<虚拟机当前 NAT IPv4>'
Test-NetConnection -ComputerName $vmIp -Port 22
ssh "intern@$vmIp"
```

scp 传固定文件：

```powershell
$localFile = Join-Path $HOME 'Downloads\host-to-vm.txt'
'Windows host to Anolis VM' | Set-Content -LiteralPath $localFile -Encoding utf8
scp $localFile "intern@${vmIp}:/home/intern/"
ssh "intern@$vmIp" 'cat /home/intern/host-to-vm.txt'
```

## 预期结果

教材给出的语义检查点：

- `/etc/os-release` 的 `VERSION_ID` 是 `8.10`；
- `whoami` 输出 `intern`，`id` 的组包含 `wheel`；
- `getenforce` 输出 `Enforcing`；
- `sshd`、`firewalld`、`vmtoolsd` 三者都是 `enabled` + `active`；
- 存在默认路由，且 DNS 能解析 `mirrors.openanolis.cn`；
- Windows 侧 `Test-NetConnection ... -Port 22` 的 `TcpTestSucceeded` 为 `True`；
- SSH 登录后 `hostname` 显示 `linux-lab`；
- scp 过去的文件内容是 `Windows host to Anolis VM`；
- `~/linux-lab` 有一次基线提交且工作区干净；
- Workstation 中存在 `day1-clean-install` 快照。

> 说明：本目录的脚本没有在当前这台 Windows 机器上实跑（Day 1 的对象是 VMware 里的 Anolis 虚拟机），因此仓库里不放 Day 1 的输出文件。上面列的是教材规定的**预期行为**，实跑后的真实输出应由 `05-baseline-evidence.sh` 写入虚拟机内的 `~/linux-lab/evidence/day01-system.txt`。

## 高风险动作与红线

- 日常不用 root 登录，只用 `sudo` 临时提权执行单条命令；
- 不关闭 SELinux、不长期停用 firewalld、不开放 root SSH 登录；
- Day 1 不添加第二块磁盘，5GB 练习盘留到 Day 2；
- 不把密码、私钥、Token 写进 Git、截图或每日总结；
- 快照不是备份，只用于短期实验回退。

## 常见问题（教材"常见错误及修复"节选）

| 现象 | 根因与修复 |
|---|---|
| 提示不支持 VT-x/AMD-V | UEFI/BIOS 未启用虚拟化，先改固件设置 |
| 启动后又进入安装器 | CD/DVD 仍从 ISO 启动，关机后取消 Connect at power on |
| `intern is not in the sudoers file` | 安装时漏勾管理员，用 root 把用户加进 `wheel`，不要开 root SSH |
| 没有 IPv4 | 确认网卡是 NAT 且已连接，再查 `nmcli device status` |
| 能 ping IP 但域名失败 | DNS 问题，查 `/etc/resolv.conf` 和 `nmcli connection show` |
| SSH 提示主机密钥变化 | 确实恢复过快照时，先核对 IP，再 `ssh-keygen -R <VM_IP>` |
| 更新后内核没变 | 新内核要重启才生效，用 `uname -r` 与 `rpm -q kernel` 对照 |
