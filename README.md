# AI 短剧自动生成系统

基于 Celery 分布式任务队列，用户输入主题即可自动完成 **文案 → 图片 → 视频** 全流程生成。

## 架构

```
用户输入主题 → Master 调度器 → Redis → Worker(文案) → Worker(图片) → Worker(视频)
                                              ↑
                                         Flower 实时监控
```

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 启动 Redis
docker-compose up -d redis

# 3. 启动 Worker (终端 A)
python cli.py worker --type all

# 4. 提交任务 (终端 B)
python cli.py run "霸道总裁爱上我"

# 5. 监控面板
open http://localhost:5555
```

## 命令

| 命令 | 说明 |
|------|------|
| `python cli.py run "主题"` | 提交生成任务 |
| `python cli.py status <id>` | 查询任务状态 |
| `python cli.py worker --type all` | 启动全部 Worker |
| `python cli.py worker --type copywriting` | 启动文案 Worker |

## 项目结构

```
├── config.py           Celery 配置
├── celery_app.py       Celery 实例
├── orchestrator.py     Master 调度器
├── cli.py              CLI 入口
├── tasks/              三个 Worker 任务
├── ai_backends/        可插拔 AI 后端
└── docker-compose.yml  Redis + Flower
```

## 容错

每步 `max_retries=3`，指数退避 `60s`，失败自动重试，Flower 面板实时可见。

## 接入真实 AI

在 `ai_backends/` 下新增继承 `BaseAIBackend` 的类，注册到 `__init__.py` 的 `_registry` 即可，无需改动 Worker 或调度器代码。
