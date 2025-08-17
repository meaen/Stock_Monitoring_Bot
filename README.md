# 🐍 Python 全自动库存监控机器人

这是一个强大的商品库存和价格监控脚本教程。它使用 Python 和 Selenium 模拟真实浏览器访问网页以对抗反爬虫机制，通过 Telegram 发送实时通知，并最终部署为一个可在Linux服务器上7x24小时无人值守运行的系统服务。比如可以用来监控独角数卡、异次元发卡等各种发卡程序，或者是你想要监控的其他一些不太严格的商品链接。

---

## 目录

- [第一部分：准备工作](#第一部分准备工作-prerequisites)
- [第二部分：服务器环境准备](#第二部分服务器环境准备-environment-setup)
- [第三部分：创建 Telegram 机器人](#第三部分创建-telegram-机器人-telegram-bot-setup)
- [第四部分：编写与配置监控脚本](#第四部分编写与配置监控脚本-the-script)
- [第五部分：测试脚本](#第五部分测试脚本-manual-test)
- [第六部分：部署为系统服务](#第六部分部署为系统服务-deployment-as-a-service)
- [第七部分：服务管理与日志查看](#第七部分服务管理与日志查看-management)

---

## 第一部分：准备工作 (Prerequisites)

- **一台Linux服务器**： Ubuntu、debian等服务器都行。ipv4还是ipv6都可以，要是你监控的网站不支持ipv6你可以可以套一个cf的免费v4出口。
- **一个Telegram账号**：用于接收库存和价格变动通知。
- **基础的SSH工具**：如 Termius, Xshell, PuTTY 或系统自带的终端，用于连接你的服务器。

---

## 第二部分：服务器环境准备 (Environment Setup)

连接上你的服务器后，依次执行以下命令来安装所有必需的软件和依赖。

### 步骤 2.1: 更新系统软件包列表

这是一个好习惯，可以确保你安装的软件都是最新的。（非必须，这比较耗时）

```bash
sudo apt update
sudo apt upgrade -y
```

### 步骤 2.2: 安装 Python 和 pip

系统通常自带Python，但我们确保 `pip`（Python的包管理器）也已安装。

```bash
sudo apt install python3 python3-pip -y
```

### 步骤 2.3: 安装 Google Chrome 浏览器

我们的脚本需要驱动一个真实的浏览器，所以必须在服务器上安装它。

```bash
# 下载Chrome的官方安装包
wget [https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb](https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb)

# 安装Chrome，apt会自动处理所有依赖
sudo apt install ./google-chrome-stable_current_amd64.deb -y
```

### 步骤 2.4: 安装 Python 依赖库

安装 `selenium`（浏览器“遥控器”）和 `undetected-chromedriver`（能避免被网站检测到的“智能钥匙”）。

```bash
pip3 install selenium undetected-chromedriver
```

---

## 第三部分：创建 Telegram 机器人 (Telegram Bot Setup)

你需要一个机器人来给你发消息。

1.  在Telegram里搜索 `BotFather` 并开始对话。
2.  发送 `/newbot` 命令。
3.  按照提示，为你的机器人设置一个**名称 (Name)**，例如 `我的库存监控助手`。
4.  再设置一个**用户名 (Username)**，它必须以 `bot` 结尾，例如 `my_stock_monitor_bot`。
5.  创建成功后，`BotFather` 会给你一长串 **Token**。**请务必复制并保存好这个Token**。
6.  接着，在Telegram里搜索并找到你的机器人，给它发送一条任意消息（比如 `/start`）。
7.  **获取你的 Chat ID**：在浏览器中访问以下链接（把`你的Token`换成你刚刚获取到的Token）：
    `https://api.telegram.org/bot你的Token/getUpdates`
    在返回的页面中，找到 `"chat":{"id":一串数字}`，这串数字就是你的 **Chat ID**。

---

## 第四部分：编写与配置监控脚本 (The Script)

现在，我们来创建并配置核心的监控脚本。

### 步骤 4.1: 创建项目目录并进入

```bash
mkdir ~/stock_monitor
cd ~/stock_monitor
```

### 步骤 4.2: 创建脚本文件

使用 `nano` 编辑器创建一个新的Python文件。

```bash
nano stock_monitor.py
```

### 步骤 4.3: 粘贴最终脚本代码

请将本仓库中的 [`stock_monitor.py`](https://github.com/meaen/Stock_Monitoring_Bot/blob/main/stock_monitor.py) 文件内的完整代码，粘贴至 `nano` 编辑器中。

### 步骤 4.4: 配置脚本

1.  在 `nano` 编辑器里，找到脚本顶部的配置区域。
2.  将 `TELEGRAM_BOT_TOKEN` 的值替换成你自己的Bot Token。
3.  将 `TELEGRAM_CHAT_ID` 的值替换成你自己的Chat ID。
4.  （可选）在 `MONITOR_PRODUCTS` 列表中，修改商品名称，或添加/删除你想监控的商品。
5.  配置完成后，按 `Ctrl + X`，然后按 `Y`，最后按回车键，保存并退出。

---

## 第五部分：测试脚本 (Manual Test)

在正式部署前，先手动运行一次，确保一切正常。

```bash
python3 stock_monitor.py
```

如果你的配置都正确，你应该能看到脚本开始检查商品，并成功收到第一批Telegram通知。确认无误后，按 `Ctrl + C` 停止脚本。

---

## 第六部分：部署为系统服务 (Deployment as a Service)

为了让脚本能开机自启、无人值守地运行，我们将其创建为一个系统服务。

### 步骤 6.1: 创建服务文件

```bash
sudo nano /etc/systemd/system/stock-monitor.service
```

### 步骤 6.2: 粘贴服务配置

将下面的配置内容完整地复制并粘贴到编辑器中。

```ini
[Unit]
Description=Stock Monitor Service by Gemini
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/stock_monitor
ExecStart=/usr/bin/python3 /home/ubuntu/stock_monitor/stock_monitor.py
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
```

> **注意**：这里的 `User` 和路径 `WorkingDirectory`/`ExecStart` 都是基于你的用户名是 `ubuntu`。如果你的用户名是 `root` 或其他，请务必修改。

粘贴后，按 `Ctrl + X` -> `Y` -> 回车，保存并退出。

### 步骤 6.3: 启动并设置开机自启

依次运行以下命令：

```bash
# 重新加载systemd配置，让新服务生效
sudo systemctl daemon-reload

# 立即启动服务
sudo systemctl start stock-monitor

# 设置服务为开机自启
sudo systemctl enable stock-monitor
```

---

## 第七部分：服务管理与日志查看 (Management)

现在，你的脚本已经是一个真正的后台服务了。

- **查看服务状态**:
  ```bash
  sudo systemctl status stock-monitor.service
  ```
  > 看到绿色的 `active (running)` 就代表一切正常。

- **查看实时日志**:
  ```bash
  journalctl -u stock-monitor.service -f
  ```

- **停止服务**:
  ```bash
  sudo systemctl stop stock-monitor.service
  ```

- **重启服务** (例如，在你修改了`stock_monitor.py`的配置后):
  ```bash
  sudo systemctl restart stock-monitor.service
  ```

至此，你已成功搭建了一个强大、稳定、全自动的库存监控系统。恭喜！
