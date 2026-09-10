# Dify Docker 部署

本目录是 Dify `1.17.0` 的 Docker Compose 部署配置，独立于临床量表质控系统运行。

## 启动

在项目根目录执行：

```bash
cd dify
docker compose up -d
docker compose ps
```

访问：

- Dify 管理台：http://localhost:8081
- HTTPS 预留端口：https://localhost:8443

第一次访问会进入 `/install`，按页面提示创建 Dify 管理员和工作区。

## 与临床系统的连接

临床系统容器通过宿主机地址访问 Dify：

```env
DIFY_OPENAI_BASE_URL=http://host.docker.internal:8081
```

在 Dify 中创建或导入量表工作流后，发布为 API，复制应用 API Key，填入项目根目录 `.env`：

```env
DIFY_HAMD_API_KEY=app-xxxxxxxx
DIFY_HAMA_API_KEY=app-xxxxxxxx
DIFY_PHQ9_API_KEY=app-xxxxxxxx
```

然后重启临床系统后端：

```bash
cd ..
docker compose up -d --build backend
```

项目中的 `AI临床量表智能质控系统.yml` 是可导入 Dify 的工作流文件。

## 停止与日志

```bash
docker compose down
docker compose logs -f api
docker compose logs -f nginx
```

不要使用 `docker compose down -v`，否则会删除 Dify 的 Docker 卷。Dify 的数据库、上传文件和向量数据位于 `dify/volumes/`。

## 端口

临床系统使用：

- 前端：`8080`
- 后端：`8000`
- MySQL：`3306`

Dify 使用：

- Web/Nginx：`8081`
- HTTPS：`8443`
- 插件调试：`5004`
