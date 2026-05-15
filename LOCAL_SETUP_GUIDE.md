# 📘 QueryBridge Local Setup Guide

Welcome to the **Enterprise Analytics Operating System**. This guide will help you get QueryBridge running locally in a production-hardened state.

## 📋 Prerequisites
- **Docker Desktop** (latest version)
- **PowerShell 7+** (for Windows users)
- **8GB RAM** (16GB recommended for AI operations)

## 🚀 One-Command Startup (Recommended)

### Windows
Run the following in your terminal:
```powershell
./start-querybridge.ps1
```

### Linux / macOS
```bash
docker-compose up -d --build
```

## 🔐 Environment Configuration
The system requires valid keys for security and AI operations.
1. Copy `.env.example` to `.env`
2. Update the following variables:
   - `JWT_SECRET`: Used for session signing.
   - `ENCRYPTION_KEY`: Used for securing your data source credentials.
   - `NVIDIA_API_KEY`: Required for the AI Intelligence runtime.

## 🔍 Service Map
| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend** | [http://localhost:3000](http://localhost:3000) | Main Analytics Dashboard |
| **Nginx Proxy** | [http://localhost](http://localhost) | Unified Gateway |
| **API Docs** | [http://localhost:8000/docs](http://localhost:8000/docs) | Backend API Reference |
| **Metrics** | [http://localhost:8000/metrics](http://localhost:8000/metrics) | Real-time Performance Data |
| **Grafana** | [http://localhost:3001](http://localhost:3001) | Operational Dashboards |

## 🛠️ Troubleshooting
If a service fails to start:
1. Run `./scripts/validate-system.py` to check for port conflicts.
2. Check logs with `docker-compose logs -f <service_name>`.
3. Use `docker-compose restart <service_name>` to recover.

---
**Privacy First:** All data processing occurs within your Docker network. No business data is ever sent to external servers.
