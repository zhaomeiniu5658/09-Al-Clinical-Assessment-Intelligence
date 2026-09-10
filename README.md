# AI临床量表智能质控系统

单用户版临床量表智能质控系统。用户上传医患对话音频、量表类型和医生打分表，系统通过讯飞 ASR 转录文本，再通过 Dify Workflow 提炼医生评分、生成 AI 评分和质控分析。

## 技术栈

- 前端：Vue3、TypeScript、Element Plus、Vite
- 后端：FastAPI、SQLAlchemy、Alembic、MySQL8
- 异步任务：FastAPI BackgroundTasks
- AI 能力：Dify Workflow 或 OpenAI-compatible Chat Completions
- ASR：讯飞录音文件转写 LFASR
- 部署：Docker Compose

## 功能

- 单用户登录
- 上传音频解析弹窗
- 质控列表自动刷新
- 保存原始音频和 ASR 转录文本
- 展示医生评分、AI 评分、评分依据、证据分析、错误原因、优化建议
- 支持失败任务重试
- 支持人工复核评分、复核原因和审核意见

## 快速启动

1. 创建环境配置：

```bash
cp .env.example .env
```

2. 修改 `.env`：

- `ADMIN_USERNAME` / `ADMIN_PASSWORD`
- `JWT_SECRET_KEY`
- `DIFY_OPENAI_BASE_URL`
- `DIFY_OPENAI_MODEL`
- `DIFY_HAMD_API_KEY`
- `DIFY_HAMA_API_KEY`
- `DIFY_PHQ9_API_KEY`
- `DIFY_PROTOCOL=workflow`
- `DIFY_WORKFLOW_BASE_URL`
- `DIFY_WORKFLOW_API_KEY`
- `DIFY_WORKFLOW_USER`
- `DIFY_WORKFLOW_REQUIRE_DOCTOR_TEST_FILE`
- `XFYUN_APP_ID`
- `XFYUN_API_KEY`
- `XFYUN_API_SECRET`

3. 启动：

```bash
docker compose up --build
```

4. 访问：

- 前端：http://localhost:8080
- 后端健康检查：http://localhost:8000/health
- OpenAPI：http://localhost:8000/docs

运行数据均保存在项目目录中：MySQL 数据位于 `data/mysql`，上传文件位于 `data/storage`。迁移电脑时可直接复制整个项目目录。

更完整的 Docker、数据库迁移和新电脑部署说明见 [`DOCKER部署.md`](DOCKER部署.md)。

Dify 的独立 Docker 服务位于 [`dify/`](dify/)，管理台默认地址为 `http://localhost:8081`。

## Dify 接口约定

### Workflow

当前测试环境工作流地址为 `http://101.200.145.196:8888`，工作流输入为：

- `dialog`：ASR 转录的对话文本
- `doctor_test`：医生打分表文件

后端调用：

```text
POST {DIFY_WORKFLOW_BASE_URL}/v1/workflows/run
Authorization: Bearer <DIFY_WORKFLOW_API_KEY>
```

医生打分表会先通过 `/v1/files/upload` 上传，再以 `local_file` 引用传给工作流。API Key 只放在本地 `.env`，不要提交到 Git。

创建任务接口新增字段 `doctor_test_file`；在当前远程工作流配置下，该字段对 HAMD 任务实际必填，仅支持 Excel 文件（`.xls` 或 `.xlsx`）。当前远程工作流仅支持 HAMD（HAM-D17）。

### OpenAI-compatible

每个量表配置一个 Dify 应用 API Key，量表对应的大模型、知识库和提示词由 Dify 应用内部配置：

- `DIFY_HAMD_API_KEY`
- `DIFY_HAMA_API_KEY`
- `DIFY_PHQ9_API_KEY`

后端调用：

```text
POST {DIFY_OPENAI_BASE_URL}/v1/chat/completions
Authorization: Bearer <DIFY_APP_API_KEY>
```

请求采用 OpenAI Chat Completions 格式。`model` 默认填 `DIFY_OPENAI_MODEL=dify`，实际使用的大模型以 Dify 应用内部设置为准。

模型需要返回结构化 JSON，字段如下：

```json
{
  "doctor_score": 18,
  "ai_score": 20,
  "scoring_basis": "评分依据",
  "evidence_analysis": "证据分析",
  "error_reason": "错误原因",
  "optimization_suggestion": "优化建议"
}
```

后端会从 `choices[0].message.content` 解析 JSON。

## 讯飞 ASR

后端封装了讯飞录音文件转写 LFASR 流程：

1. `prepare`
2. 分片 `upload`
3. `merge`
4. 轮询 `getProgress`
5. `getResult`

默认支持上传扩展名：

```text
mp3, wav, m4a, aac, flac, ogg, webm, amr
```

如果生产环境的讯飞接口对音频编码有更严格要求，可以在上传后增加 ffmpeg 转码步骤；当前版本保留原始音频并直接提交给讯飞。

## 本地开发

后端：

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

前端：

```bash
cd frontend
npm install
npm run dev
```

## API

- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`
- `POST /api/v1/tasks`
- `GET /api/v1/tasks`
- `GET /api/v1/tasks/{task_id}`
- `GET /api/v1/tasks/{task_id}/audio`
- `POST /api/v1/tasks/{task_id}/retry`
- `POST /api/v1/tasks/{task_id}/review`

## 项目结构

```text
backend/
  app/
    api/
    core/
    db/
    models/
    schemas/
    services/
    tasks/
  alembic/
  tests/
frontend/
  src/
    api/
    router/
    stores/
    types/
    views/
    styles/
docker-compose.yml
.env.example
README.md
```
