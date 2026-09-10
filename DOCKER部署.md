# Docker 部署说明

本项目已经将 MySQL、FastAPI 后端和 Vue 前端放进 Docker Compose：

```text
frontend (Nginx :80)
    -> /api/* 代理到 backend:8000
backend (FastAPI :8000)
    -> mysql:3306
mysql (MySQL 8.4)
```

## 新电脑首次启动

### 1. 安装 Docker

在新电脑安装并启动 Docker Desktop，确认使用 Linux containers。

检查命令：

```bash
docker --version
docker compose version
```

### 2. 检查项目文件

从代码包迁移时，至少保留：

```text
.env
docker-compose.yml
backend/
frontend/
data/
```

如果没有 `.env`，从模板创建：

```bash
cp .env.example .env
```

Windows PowerShell：

```powershell
Copy-Item .env.example .env
```

首次使用请修改 `.env` 中的：

- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`
- `FRONTEND_PORT`
- Dify 和讯飞配置（如果需要真实 AI 质控和语音转写）

### 3. 启动全部服务

在项目根目录执行：

```bash
docker compose up -d --build
```

查看服务状态：

```bash
docker compose ps
```

预期服务：

```text
mysql
backend
frontend
```

访问地址：

- 前端页面：`http://localhost:8080`
- 平台登录页：`http://localhost:8080/platform/login`
- 平台首页：`http://localhost:8080/platform`
- 后端健康检查：`http://localhost:8000/health`
- 后端 OpenAPI：`http://localhost:8000/docs`

如果 `.env` 中设置了其他端口，以 `.env` 为准。

## Dify Docker 服务

本项目现在同时包含独立的 Dify Docker 部署目录：

```text
dify/
```

Dify 使用自己的 PostgreSQL、Redis、Weaviate、API、Web、Worker 和沙箱容器，不复用临床系统的 MySQL。启动 Dify：

```bash
cd dify
docker compose up -d
docker compose ps
```

访问 Dify 管理台：

```text
http://localhost:8081
```

首次访问会进入 Dify 初始化页面。创建或导入量表工作流并发布 API 后，把对应的应用 API Key 写入项目根目录 `.env`：

```env
DIFY_OPENAI_BASE_URL=http://host.docker.internal:8081
DIFY_HAMD_API_KEY=app-xxxxxxxx
DIFY_HAMA_API_KEY=app-xxxxxxxx
DIFY_PHQ9_API_KEY=app-xxxxxxxx
```

项目根目录的 `AI临床量表智能质控系统.yml` 可导入 Dify。修改 API Key 后重启临床后端：

```bash
cd ..
docker compose up -d --build backend
```

Dify 的数据库和运行数据位于 `dify/volumes/`，不要删除。完整说明见 [`dify/README.md`](dify/README.md)。

## 数据保存位置

Compose 使用项目目录绑定挂载：

```text
data/mysql/       MySQL 数据库文件
data/storage/     音频和知识库上传文件
```

执行下面的命令不会删除这两个目录：

```bash
docker compose down
```

不要使用：

```bash
docker compose down -v
```

也不要在没有备份的情况下删除 `data/mysql`。

## 从另一台电脑迁移

### 只迁移代码，创建新数据库

如果打包时没有包含原电脑的 `data/mysql`，新电脑会创建一个空的 MySQL 数据库。后端容器启动时会自动执行：

```text
alembic upgrade head
```

然后自动创建默认管理员账号：

```text
用户名：.env 中的 ADMIN_USERNAME
密码：.env 中的 ADMIN_PASSWORD
```

### 同时迁移原有业务数据

不要直接跨电脑复制正在运行中的 MySQL 原始数据目录，尤其是 Windows 和 macOS/Linux 之间迁移。推荐在旧电脑导出 SQL：

```bash
docker compose exec mysql mysqldump \
  -uroot \
  -p"${MYSQL_ROOT_PASSWORD}" \
  --all-databases \
  --single-transaction \
  --routines \
  --events > clinical_qc_backup.sql
```

新电脑启动 MySQL 后导入：

```bash
docker compose up -d mysql
docker compose exec -T mysql mysql \
  -uroot \
  -p"${MYSQL_ROOT_PASSWORD}" < clinical_qc_backup.sql
docker compose up -d --build backend frontend
```

如果使用 Windows PowerShell，可以先在 `.env` 中读取并手动替换密码，或使用 Docker Desktop 提供的终端执行导出命令。

上传的音频和知识库文件位于 `data/storage`，可以直接复制，但复制前应先停止服务：

```bash
docker compose down
```

## 日常命令

查看日志：

```bash
docker compose logs -f backend
docker compose logs -f mysql
docker compose logs -f frontend
```

重新构建并启动：

```bash
docker compose up -d --build
```

停止服务：

```bash
docker compose down
```

查看后端健康状态：

```bash
curl http://localhost:8000/health
```

预期返回：

```json
{"status":"ok"}
```

## 常见问题

### 3306 或 8080 已被占用

修改 `.env`：

```env
MYSQL_PORT=13306
FRONTEND_PORT=18080
BACKEND_PORT=18000
```

注意：`MYSQL_HOST` 和容器内部的 `MYSQL_PORT` 不要改。Compose 内部连接仍然使用：

```env
MYSQL_HOST=mysql
MYSQL_PORT=3306
```

修改后重新启动：

```bash
docker compose up -d --build
```

### 前端打开但接口报错

先检查：

```bash
docker compose ps
docker compose logs --tail=100 backend
docker compose logs --tail=100 mysql
```

确认 `backend` 和 `mysql` 状态为 `healthy` 或 `Up`。

### 登录账号忘记了

默认账号由 `.env` 中的 `ADMIN_USERNAME` 和 `ADMIN_PASSWORD` 决定。首次初始化后，修改 `.env` 不会自动覆盖已有数据库用户密码；需要通过用户管理或数据库方式修改。
