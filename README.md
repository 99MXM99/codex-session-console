# Codex Session Console

一个面向本地 Codex 会话的管理工具。

它的目标很直接：
- 把 `~/.codex` 里的会话记录整理成可视化列表
- 让你直接在页面里筛选、重命名、删除、恢复
- 提供导出能力，方便做备份、归档或二次处理
- 在执行高风险操作前自动备份底层数据

当前版本默认以本地 Web UI 方式运行，并提供两套桌面双击启动方式：
- macOS：桌面 `.app`
- Linux：`.desktop` 桌面入口

## 适合什么场景

- 你有很多 Codex 对话，想统一查看和清理
- 你希望给重要会话设置更清晰的标题
- 你想区分“仍存在”“已删除”“可恢复/不可恢复”的会话
- 你希望把本地会话导出成 `txt` 或 `json`

## 功能概览

- 会话列表查看
- 按状态筛选：`当前存在 / 已删除 / 会话`
- 搜索 `ID / 主题 / 标题`
- 在页面内设置标题
- 批量删除现存会话
- 从备份中恢复支持单条恢复的已删除会话
- 导出 `txt` / `json`
- 多主题切换
- macOS 桌面应用安装

## 运行前提

- 需要已安装 `python3`
- 如果要看到会话数据，本机需要存在 Codex 本地数据目录 `~/.codex`
- 双击启动的系统支持：
  - macOS：支持 `.app`
  - Linux：支持 `.desktop`

如果目标机器没有安装 Codex，或者没有本地会话数据：
- 程序仍然可以启动
- 页面会显示为空
- 不会因为缺少数据直接崩溃

## 快速开始

### 方式一：直接运行项目

进入项目目录后执行：

```bash
python3 app.py --open
```

程序会启动本地服务，并自动打开浏览器页面。

如果你不希望自动打开浏览器，也可以只启动服务：

```bash
python3 app.py
```

默认地址：

```text
http://127.0.0.1:8876
```

### 方式二：双击启动

项目根目录已经带了一个 macOS 启动器：

```text
Launch Codex Session Manager.command
```

双击后会：
- 启动本地服务
- 自动打开页面

### 方式三：安装 macOS 桌面应用

如果你想要桌面图标，执行：

```bash
./tools/install_mac_app.sh
```

执行后会在桌面生成：

```text
Codex Session Console.app
```

之后直接双击这个 `.app` 即可。

如果你后续移动了项目目录，需要重新执行一次安装脚本。

### 方式四：安装 Linux 桌面入口

在 Linux 上执行：

```bash
./tools/install_linux_app.sh
```

这个脚本会创建三样东西：
- `~/.local/bin/codex-session-console`
- `~/.local/share/applications/codex-session-console.desktop`
- 如果存在桌面目录，还会创建 `~/Desktop/Codex Session Console.desktop`

之后你可以：
- 在应用菜单里搜索 `Codex Session Console`
- 或直接双击桌面的 `Codex Session Console.desktop`

有些 Linux 桌面环境第一次双击 `.desktop` 文件时，可能需要你额外点一次：
- `Allow Launching`
- 或“信任并启动”

## 页面怎么用

### 1. 页头

右上角可以：
- 切换主题
- 刷新页面
- 打开快捷命令菜单

### 2. 搜索区

可以搜索：
- 会话 ID
- 主题
- 自定义标题

### 3. 列表区

你会看到三种视图：
- `当前存在`
- `已删除`
- `会话`

列表里支持：
- 复制会话 ID
- 设置标题
- 查看会话状态点
- 恢复支持单条恢复的已删除会话

状态点含义：
- 绿色：可继续对话
- 黄色：已删除，可恢复
- 红色：已删除，不可恢复

### 4. 分页区

底部可以：
- 切换页码
- 调整每页显示数量
- 在 `当前存在` 视图里批量删除已选会话

## 常用命令

启动 UI：

```bash
python3 app.py --open
```

导出文本：

```bash
python3 app.py export txt
```

导出 JSON：

```bash
python3 app.py export json
```

安装桌面应用：

```bash
./tools/install_mac_app.sh
```

安装 Linux 桌面入口：

```bash
./tools/install_linux_app.sh
```

## 数据来源

程序默认读取这些本地文件：

- `~/.codex/state_5.sqlite`
- `~/.codex/session_index.jsonl`
- `~/.codex/history.jsonl`
- `~/.codex/sessions/...`

## 数据安全与恢复

这是这个项目里最重要的部分。

在执行以下操作前，程序会先备份底层数据：
- 删除会话
- 重命名标题

备份目录默认在：

```text
~/.codex/session_manager_backups/
```

说明：
- 旧备份不一定包含完整的原始会话文件
- 新版本删除时会额外备份对应的 rollout 文件
- 只有同时具备元数据和原始会话文件的记录，才会被判定为“可单条恢复”

## 项目结构

这个项目保持“标准库优先”，尽量不引入额外依赖。

- `app.py`
  CLI 入口，只负责参数解析和调度。

- `server.py`
  本地 HTTP 服务层，负责请求处理和页面输出。

- `store.py`
  底层数据访问层，负责读写 SQLite、jsonl、备份和恢复。

- `ui.py`
  页面渲染层，直接输出完整 HTML。

- `models.py`
  共享数据模型。

- `config.py`
  路径、时区、主题等全局配置。

- `Launch Codex Session Manager.command`
  项目内双击启动器。

- `tools/run_local_ui.sh`
  统一的本地启动脚本，macOS 和 Linux 的桌面入口都共用它。

- `tools/install_mac_app.sh`
  安装桌面 `.app`。

- `tools/install_linux_app.sh`
  安装 Linux 的 `.desktop` 桌面入口。

- `macos/`
  macOS 应用模板和图标。

- `linux/`
  Linux 桌面入口模板和图标。

## 工程维护说明

当前版本已经做过一轮工程收口，重点是：
- 启动逻辑收敛成一套脚本，避免双份实现
- 参数解析补了容错，非法页码不会导致服务异常
- `session_index.jsonl` 中的坏行会自动跳过
- 桌面 `.app` 直接使用仓库内置图标，不再现场构建图标

如果你后续要继续开发，建议遵守这几个原则：
- 数据读写只改 `store.py`
- HTTP 行为只改 `server.py`
- 页面结构和样式只改 `ui.py`
- 启动与打包只改 `tools/` 和 `macos/`

## 常见问题

### 双击 `.app` 没反应

先确认：
- 机器上有 `python3`
- 项目目录没有被移动到不存在的位置

如果项目目录移动过，重新执行：

```bash
./tools/install_mac_app.sh
```

### Linux 双击 `.desktop` 没反应

先确认：
- 系统里有 `python3`
- 系统里有 `lsof`
- 最好有 `xdg-open`
- 项目目录没有被移动

如果项目目录移动过，重新执行：

```bash
./tools/install_linux_app.sh
```

如果桌面环境拦截了 `.desktop` 文件，通常需要右键后手动允许启动。

### 页面打开了但没有会话

通常是以下原因之一：
- 本机没有安装 Codex
- `~/.codex` 里没有数据
- 当前用户没有权限读取对应文件

### 删除后为什么有的能恢复，有的不能

因为“单条恢复”要求备份里同时存在：
- 这条会话的元数据
- 这条会话对应的原始 rollout 文件

缺一项就只能显示为不可恢复。

### 安装桌面应用后图标没立刻刷新

这是 Finder 的缓存行为。一般做下面任一操作即可刷新：
- 重新打开 Finder
- 挪动一下桌面上的 `.app`
- 删除后重新执行 `./tools/install_mac_app.sh`

## 适合开源吗

适合。

当前这套结构已经比较清晰，别人 clone 下来后：
- 可以直接运行 `python3 app.py --open`
- macOS 可以执行 `./tools/install_mac_app.sh` 安装桌面应用
- Linux 可以执行 `./tools/install_linux_app.sh` 安装桌面入口

如果你后续要公开到 GitHub，建议下一步补：
- `LICENSE`
- 版本号
- 更新日志
- 页面截图
- 安装演示
