# AI 文档自动化助手 - 部署文档

## 一、项目概述

AI 文档自动化助手是一个基于微服务架构的文档分析系统，支持上传 PDF/Word 文件，自动提取文本，通过 LLM 进行结构化分析，并生成 Word 报告。

### 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        用户浏览器                                │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Nginx (端口 80)                               │
│              前端静态文件 + /api/ 反向代理                         │
└──────────┬──────────────────────────────────────────────────────┘
           │
           ▼
┌──────────────────┐         ┌──────────────────┐
│    Frontend      │         │     Backend      │
│   React + Vite   │ ──────→ │    FastAPI       │
│   端口 80        │  HTTP   │    端口 8000      │
└──────────────────┘         └──┬──┬──┬──┬──────┘
                                │  │  │  │
           ┌────────────────────┘  │  │  └───────────────────┐
           ▼                       ▼  ▼                      ▼
    ┌────────────┐          ┌──────────┐            ┌──────────────┐
    │   MySQL    │          │  Redis   │            │    MinIO     │
    │  端口 3306 │          │ 端口 6379│            │  端口 9000   │
    └────────────┘          └──────────┘            └──────┬───────┘
                                                           │
           ┌───────────────────────────────────────────────┘
           ▼
    ┌──────────────────────────────────────────┐
    │              RabbitMQ                     │
    │            端口 5672 / 15672              │
    └──────────────────────┬───────────────────┘
                           │
                           ▼
                   ┌──────────────────┐
                   │    Algorithm     │
                   │    FastAPI       │
                   │    端口 8001     │
                   └──────────────────┘
```

### 通信流程

1. 前端通过 Nginx 反向代理调用后端 API
2. 后端上传文件到 MinIO，任务信息存入 MySQL，任务消息推送到 RabbitMQ
3. 算法服务从 RabbitMQ 消费任务，从 MinIO 下载文件
4. 算法服务解析文本、调用 LLM 分析、生成报告
5. 报告上传到 MinIO，结果回传到 RabbitMQ
6. 后端消费结果，更新 MySQL 状态，发送通知

---

## 二、环境要求

### 硬件要求

| 资源 | 最低配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核 |
| 内存 | 4 GB | 8 GB |
| 磁盘 | 20 GB | 50 GB |

### 软件要求

| 软件 | 版本 |
|------|------|
| Docker | 20.10+ |
| Docker Compose | 1.29+ |
| 操作系统 | Ubuntu 20.04+ / CentOS 7+ |

---

## 三、快速部署

### 3.1 克隆项目

```bash
git clone <repository-url>
cd document_automation_assistant
```

### 3.2 配置环境变量

#### 基础设施配置

复制并编辑根目录的 `.env` 文件：

```bash
cp .env.example .env
```

编辑 `.env`：

```env
# Docker Compose 基础设施配置
MYSQL_ROOT_PASSWORD=your-mysql-password
RABBITMQ_USER=admin
RABBITMQ_PASS=your-rabbitmq-password
MINIO_ROOT_USER=minioadmin
MINIO_ROOT_PASSWORD=your-minio-password
```

#### 后端配置

编辑 `ai-doc-backend/.env`：

```env
APP_ENV=production
APP_PORT=8000

# MySQL
MYSQL_HOST=mysql
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your-mysql-password
MYSQL_DATABASE=doc_assistant

# Redis
REDIS_URL=redis://redis:6379/0

# RabbitMQ
RABBITMQ_URL=amqp://admin:your-rabbitmq-password@rabbitmq:5672/

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-minio-password
MINIO_BUCKET=doc-assistant
MINIO_SECURE=false

# JWT
JWT_SECRET=your-random-secret-key-change-in-production
JWT_EXPIRE_HOURS=24

# 上传限制
MAX_UPLOAD_SIZE_MB=50
ALLOWED_EXTENSIONS=pdf,docx
```

#### 算法配置

编辑 `ai-doc-algorithm/.env`：

```env
APP_PORT=8001

# RabbitMQ
RABBITMQ_URL=amqp://admin:your-rabbitmq-password@rabbitmq:5672/

# Redis
REDIS_URL=redis://redis:6379

# MinIO
MINIO_ENDPOINT=minio:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=your-minio-password
MINIO_SECURE=false

# LLM 配置 (必须配置有效的 API Key)
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_API_KEY=your-actual-api-key
LLM_MODEL=deepseek-chat
LLM_TIMEOUT=120
LLM_MAX_RETRY=2

# 文本处理
CHUNK_SIZE=6000
CHUNK_OVERLAP=500
```

### 3.3 启动服务

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3.4 验证部署

```bash
# 检查所有容器是否正常运行
docker ps

# 测试后端 API
curl http://localhost:8000/health

# 测试算法服务
curl http://localhost:8001/health

# 测试前端页面
curl http://localhost:80
```

---

## 四、服务端口

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端 | 80 | Web 界面 |
| 后端 API | 8000 | REST API |
| 算法服务 | 8001 | 文档处理 |
| MySQL | 3306 | 数据库 |
| Redis | 6379 | 缓存 |
| RabbitMQ | 5672 | 消息队列 |
| RabbitMQ 管理界面 | 15672 | Web 管理 |
| MinIO API | 9000 | 对象存储 |
| MinIO 控制台 | 9001 | Web 管理 |

---

## 五、默认账号

| 服务 | 用户名 | 密码 |
|------|--------|------|
| MySQL | root | 在 .env 中配置 |
| RabbitMQ | admin | 在 .env 中配置 |
| MinIO | minioadmin | 在 .env 中配置 |

---

## 六、项目结构

```
document_automation_assistant/
├── docker-compose.yml          # Docker Compose 编排文件
├── .env.example                # 环境变量示例
├── DEPLOYMENT.md               # 本文档
│
├── ai-doc-frontend/            # 前端项目
│   ├── src/                    # React 源码
│   ├── nginx.conf              # Nginx 配置
│   ├── Dockerfile              # 前端镜像
│   └── package.json            # 依赖配置
│
├── ai-doc-backend/             # 后端项目
│   ├── app/                    # FastAPI 应用
│   │   ├── api/                # API 路由
│   │   ├── models/             # 数据库模型
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── services/           # 业务逻辑
│   │   └── utils/              # 工具函数
│   ├── Dockerfile              # 后端镜像
│   └── requirements.txt        # Python 依赖
│
└── ai-doc-algorithm/           # 算法项目
    ├── app/                    # FastAPI 应用
    │   ├── services/           # 核心服务
    │   ├── prompts/            # LLM 提示词
    │   └── templates/          # 报告模板
    ├── Dockerfile              # 算法镜像
    └── requirements.txt        # Python 依赖
```

---

## 七、API 接口

### 认证接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/auth/register | 用户注册 |
| POST | /api/auth/login | 用户登录 |
| GET | /api/auth/me | 获取当前用户信息 |

### 任务接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/tasks | 上传文件并创建任务 |
| GET | /api/tasks | 获取任务列表 |
| GET | /api/tasks/{task_no} | 获取任务详情 |
| GET | /api/tasks/{task_no}/result | 获取分析结果 |
| GET | /api/tasks/{task_no}/download | 下载报告 |

### 通知接口

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/notify-config | 创建通知配置 |
| GET | /api/notify-config | 获取通知配置 |
| DELETE | /api/notify-config/{id} | 删除通知配置 |
| POST | /api/notify-config/test | 测试通知 |

---

## 八、数据库表结构

### user 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| username | VARCHAR(64) | 用户名 |
| password_hash | VARCHAR(255) | 密码哈希 |
| company_name | VARCHAR(128) | 公司名称 |
| phone | VARCHAR(32) | 手机号 |
| is_active | TINYINT | 是否启用 |
| created_at | DATETIME | 创建时间 |

### document_task 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| task_no | VARCHAR(64) | 任务编号 |
| user_id | BIGINT | 用户 ID |
| analyze_type | VARCHAR(32) | 分析类型 (policy/bidding) |
| original_filename | VARCHAR(255) | 原始文件名 |
| minio_key | VARCHAR(512) | MinIO 存储路径 |
| status | VARCHAR(32) | 状态 |
| result_json | JSON | 分析结果 |
| report_minio_key | VARCHAR(512) | 报告存储路径 |
| created_at | DATETIME | 创建时间 |

### notify_config 表

| 字段 | 类型 | 说明 |
|------|------|------|
| id | BIGINT | 主键 |
| user_id | BIGINT | 用户 ID |
| notify_type | VARCHAR(32) | 通知类型 (feishu/wecom/dingtalk) |
| webhook_url | VARCHAR(1024) | Webhook 地址 |
| is_enabled | TINYINT | 是否启用 |

---

## 九、MinIO 存储结构

```
doc-assistant/
├── uploads/                    # 用户上传的原始文件
│   └── 2026/05/09/
│       └── TASK202605090001_original.pdf
├── reports/                    # 算法生成的报告
│   └── TASK202605090001_report.docx
└── texts/                      # 提取的中间文本
    └── TASK202605090001_cleaned.txt
```

---

## 十、RabbitMQ 队列

| Exchange | Queue | Routing Key | 说明 |
|----------|-------|-------------|------|
| doc.task.exchange | doc.task.queue | task.create | 任务队列 |
| doc.result.exchange | doc.result.queue | task.result | 结果队列 |

---

## 十一、常见问题

### 1. 容器启动失败

```bash
# 查看容器日志
docker logs doc-backend
docker logs doc-algorithm
docker logs doc-frontend

# 检查容器状态
docker ps -a
```

### 2. 数据库连接失败

检查 MySQL 容器是否正常运行：

```bash
docker logs doc-mysql
docker exec -it doc-mysql mysql -u root -p
```

### 3. RabbitMQ 连接失败

检查 RabbitMQ 管理界面：http://localhost:15672

### 4. MinIO 连接失败

检查 MinIO 控制台：http://localhost:9001

### 5. LLM API 调用失败

确保 `ai-doc-algorithm/.env` 中配置了有效的 API Key：

```env
LLM_API_KEY=your-actual-api-key
```

---

## 十二、维护命令

### 查看日志

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f algorithm
docker-compose logs -f frontend
```

### 重启服务

```bash
# 重启所有服务
docker-compose restart

# 重启特定服务
docker-compose restart backend
docker-compose restart algorithm
docker-compose restart frontend
```

### 停止服务

```bash
# 停止所有服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v
```

### 更新服务

```bash
# 重新构建并启动
docker-compose up -d --build

# 重新构建特定服务
docker-compose up -d --build backend
docker-compose up -d --build algorithm
docker-compose up -d --build frontend
```

---

## 十三、备份与恢复

### 数据库备份

```bash
# 备份 MySQL
docker exec doc-mysql mysqldump -u root -p doc_assistant > backup.sql

# 恢复 MySQL
docker exec -i doc-mysql mysql -u root -p doc_assistant < backup.sql
```

### MinIO 备份

```bash
# 备份 MinIO 数据
docker cp doc-minio:/data ./minio-backup

# 恢复 MinIO 数据
docker cp ./minio-backup doc-minio:/data
```

---

## 十四、安全建议

1. **修改默认密码**：生产环境必须修改所有默认密码
2. **JWT Secret**：使用随机生成的强密钥
3. **HTTPS**：生产环境建议配置 SSL 证书
4. **防火墙**：仅开放必要端口
5. **定期备份**：配置自动备份策略

---

## 十五、技术支持

如有问题，请查看：

1. 本文档的常见问题部分
2. 各服务的日志输出
3. Docker 和 Docker Compose 官方文档
