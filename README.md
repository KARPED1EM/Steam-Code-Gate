<div align="center">

# 🚪 Steam Code Gate

**Steam Verification Code Hosting Service**  
Display Steam email verification codes and OTP (Steam TOTP) in a centralized web interface.

<br/>

English | [简体中文](./README.zh-CN.md)

<br/>

![Python](https://img.shields.io/badge/python-3.13%2B-blue?style=flat-square)
![FastAPI](https://img.shields.io/badge/FastAPI-0.128%2B-009688?style=flat-square)
![Docker](https://img.shields.io/badge/docker-ready-2496ED?style=flat-square&logo=docker&logoColor=white)
![License](https://img.shields.io/github/license/karped1em/steam-code-gate?style=flat-square)

</div>

---

## ✨ Features

- 👥 **Multi-user System**  
  Guest / Admin / Super Admin roles supported

- 🔐 **Multi-account Hosting**  
  Manage multiple Steam accounts simultaneously

- 🔄 **Dual Verification Modes**  
  Email verification codes and Steam TOTP (OTP)

- 🛡️ **Permission Control**  
  Guests access via passcode, admins manage their own accounts, super admins manage all

- ⚡ **Automatic Updates**  
  OTP auto-refresh, email codes fetched on demand with debounce protection

---

## 🔑 Default Credentials (Important)

On first startup, the system provides a built-in administrator account:

```
Username: admin
Password: admin123
````

⚠️ **For security reasons, please change the password immediately after login.**

---

## 🧱 Tech Stack

- **Backend**: FastAPI · SQLAlchemy · SQLite  
- **Frontend**: Jinja2 · Vanilla JavaScript  
- **Authentication**: JWT · bcrypt  
- **Architecture**: Repository · DTO · SOLID  

---

## 🚀 Docker Deployment (Recommended)

No local Python environment required.

Create `compose.yml`:

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

Start:

```bash
docker compose up -d
```

Open in browser:

```
http://<SERVER-IP>:13780
```

> ⚠️ Make sure to change `JWT_SECRET_KEY` to a strong random value.

---

## 🧪 Local Development

You may configure environment variables using a `.env` file.

Example `.env`:

```env
DATABASE_PATH=./scg.db
JWT_SECRET_KEY=dev-secret
```

Start the application:

```bash
uv run python run.py
```

Open:

```
http://localhost:8000
```

---

## ⚙️ Configuration

### Environment Variables (Required)

> ❗ Both environment variables are **mandatory** and must not be empty.
> The application will refuse to start if any of them is missing or empty.

| Name             | Description               |
| ---------------- | ------------------------- |
| `DATABASE_PATH`  | SQLite database file path |
| `JWT_SECRET_KEY` | JWT secret key            |

### Database

SQLite database file will be created automatically on first startup.

---

## 📦 Upgrade

Pull the latest image and restart:

```bash
docker compose pull
docker compose up -d
```

Data stored in volumes will not be affected.
