<div align="center">

# 🚪 Steam Code Gate

**Steam 验证码托管服务**  
用于在网页中集中展示 Steam 账号的邮箱验证码或 OTP 验证码。

<br/>

[English](./README.md) | 简体中文

<br/>

![Python](https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688?style=flat-square)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/github/license/karped1em/steam-code-gate?style=flat-square)

</div>

---

## ✨ 功能特性

- 👥 **多用户系统**  
  支持访客 / 管理员 / 超级管理员三种角色

- 🔐 **多账号托管**  
  同时管理多个 Steam 账号

- 🔄 **双验证方式**  
  支持邮箱验证码与 Steam TOTP（OTP）

- 🛡️ **权限控制**  
  访客通过口令访问，管理员管理自己的账号，超级管理员管理所有账号

- ⚡ **自动更新机制**  
  OTP 自动刷新，邮箱验证码按需拉取（防抖）

---

## 🔑 默认账号（重要）

系统首次启动时会自动创建内置管理员账号：

````
用户名：admin
密码：admin123
````

⚠️ **请在首次登录后立即修改该密码，以确保安全。**

---

## 🧱 技术栈

- **后端**：FastAPI · SQLAlchemy · SQLite  
- **前端**：Jinja2 · 原生 JavaScript  
- **认证**：JWT · bcrypt  
- **架构**：Repository · DTO · SOLID  

---

## 🚀 Docker 部署（推荐）

无需安装本地 Python 环境，一条命令即可启动。

创建 `compose.yml`：

```yaml
services:
  steam-code-gate:
    image: karped1em/steam-code-gate:latest
    container_name: steam-code-gate
    restart: unless-stopped

    ports:
      - "13780:8000"

    environment:
      DATABASE_PATH: "/data/scg.db"
      JWT_SECRET_KEY: "please-change-me"

    volumes:
      - scg-data:/data

volumes:
  scg-data:
    name: steam-code-gate-data
````

启动：

```bash
docker compose up -d
```

访问：

```
http://<服务器IP>:13780
```

> ⚠️ 请务必修改 `JWT_SECRET_KEY` 为安全随机字符串。

---

## 🧪 本地开发

可以使用 `.env` 文件配置环境变量。

示例 `.env`：

```env
DATABASE_PATH=./scg.db
JWT_SECRET_KEY=dev-secret
```

启动应用：

```bash
uv run python run.py
```

访问：

```
http://localhost:8000
```

---

## ⚙️ 配置

### 环境变量（必填）

> ❗ 以下两个环境变量均 **没有默认值且不能为空**。
> 若未正确配置，程序将拒绝启动。

| 变量名              | 说明             |
| ---------------- | -------------- |
| `DATABASE_PATH`  | SQLite 数据库文件路径 |
| `JWT_SECRET_KEY` | JWT 密钥         |

### 数据库

应用使用 SQLite，首次启动时会自动创建数据库文件。

---

## 📦 升级

拉取最新镜像并重启即可完成升级：

```bash
docker compose pull
docker compose up -d
```

数据存储在 volume 中，不会丢失。
