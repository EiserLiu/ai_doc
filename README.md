# AI 文档自动化助手

> 上传政策文件或招标文件，自动生成摘要、条件、材料清单、时间节点、风险提醒和 Word/PDF 分析报告。

## 简介

AI 文档自动化助手是一个基于微服务架构的智能文档分析系统。用户上传 PDF/Word 文件后，系统自动完成文本提取、AI 结构化分析、报告生成与结果下载，帮助企业和团队将数小时的文档整理工作缩短至几分钟。

### 核心功能

- **政策文件分析** — 自动提取政策要点、申报条件、时间节点、所需材料
- **招标文件分析** — 自动提取投标要求、评分标准、资质条件、风险条款
- **结构化报告** — 生成标准化 Word/PDF 分析报告
- **通知推送** — 支持飞书、企业微信、钉钉 Webhook 通知

### 系统架构

```
浏览器 → Nginx (前端 + 反向代理) → FastAPI 后端
                                      ↓
                            MySQL / Redis / MinIO / RabbitMQ
                                      ↓
                              算法服务 (LLM 分析) → 生成报告
```

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | React + Vite + Ant Design |
| 后端 | FastAPI + SQLAlchemy + JWT |
| 算法 | FastAPI + LLM (DeepSeek) |
| 数据库 | MySQL 8.0 |
| 缓存 | Redis 7 |
| 消息队列 | RabbitMQ 3 |
| 对象存储 | MinIO |
| 部署 | Docker Compose |

## 快速开始

### 环境要求

- Docker 20.10+
- Docker Compose 1.29+
- 内存 4GB+（推荐 8GB）

### 1. 克隆项目

```bash
git clone <repository-url>
cd document_automation_assistant
```

### 2. 配置环境变量

```bash
cp .env.example .env
```

编辑 `.env` 设置基础设施密码，然后分别配置后端和算法服务的环境变量：

```bash
# 后端配置
cp ai-doc-backend/.env.example ai-doc-backend/.env

# 算法配置（必须填入有效的 LLM API Key）
cp ai-doc-algorithm/.env.example ai-doc-algorithm/.env
```

> 算法服务需要配置 `LLM_API_KEY`，默认使用 DeepSeek API。

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 访问系统

| 服务 | 地址 |
|------|------|
| 前端页面 | http://localhost |
| 后端 API | http://localhost:8000 |
| API 文档 | http://localhost:8000/docs |
| 算法服务 | http://localhost:8001 |
| RabbitMQ 管理 | http://localhost:15672 |
| MinIO 控制台 | http://localhost:9001 |

## API 接口

### 认证

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |

### 任务

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/tasks | 上传文件并创建分析任务 |
| GET | /api/tasks | 获取任务列表 |
| GET | /api/tasks/{task_no} | 获取任务详情 |
| GET | /api/tasks/{task_no}/result | 获取分析结果 |
| GET | /api/tasks/{task_no}/download | 下载分析报告 |

### 通知配置

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/notify-config | 创建通知配置 |
| GET | /api/notify-config | 获取通知配置列表 |
| DELETE | /api/notify-config/{id} | 删除通知配置 |
| POST | /api/notify-config/test | 测试通知发送 |

## 项目结构

```
document_automation_assistant/
├── docker-compose.yml
├── .env.example
│
├── ai-doc-frontend/          # 前端 - React + Vite
│   ├── src/
│   ├── nginx.conf
│   └── Dockerfile
│
├── ai-doc-backend/           # 后端 - FastAPI
│   ├── app/
│   │   ├── api/              # API 路由
│   │   ├── models/           # 数据模型
│   │   ├── schemas/          # 请求/响应模型
│   │   ├── services/         # 业务逻辑
│   │   └── utils/            # 工具函数
│   └── Dockerfile
│
└── ai-doc-algorithm/         # 算法服务 - LLM 分析
    ├── app/
    │   ├── services/         # 文本处理 & LLM 调用
    │   ├── prompts/          # 提示词模板
    │   └── templates/        # 报告模板
    └── Dockerfile
```

## 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f

# 重启服务
docker-compose restart

# 重新构建并启动
docker-compose up -d --build

# 停止服务
docker-compose down

# 停止并清除数据
docker-compose down -v
```

## 许可证

MIT License
