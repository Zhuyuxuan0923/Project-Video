import sys
import logging
import click

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

QUEUE_MAP = {
    "copywriting": ["copywriting"],
    "image_gen": ["image_gen"],
    "video_gen": ["video_gen"],
    "all": ["copywriting", "image_gen", "video_gen"],
}


@click.group()
def cli():
    """AI 短剧自动生成系统 - 基于 Celery 分布式任务队列"""


@cli.command()
@click.argument("topic")
@click.option("--backend", default="mock", help="AI 后端 (默认: mock)")
@click.option("--timeout", default=600, help="超时时间 (秒)")
def run(topic, backend, timeout):
    """提交一个短剧生成任务"""
    from orchestrator import DramaOrchestrator
    orchestrator = DramaOrchestrator(backend_name=backend)
    try:
        orchestrator.run_and_wait(topic, timeout=timeout)
    except KeyboardInterrupt:
        print("\n[!] Cancelled waiting, task still running in background")
    except Exception as e:
        print(f"\n[!] Error: {e}")


@cli.command()
@click.argument("task_id")
def status(task_id):
    """查询任务状态"""
    from orchestrator import DramaOrchestrator
    orchestrator = DramaOrchestrator()
    result = orchestrator.get_status(task_id)
    print(f"  任务ID: {result['task_id']}")
    print(f"  状态: {result['state']}")
    if result["info"]:
        print(f"  详情: {result['info']}")


@cli.command()
@click.option("--type", "worker_type", default="all", help="Worker 类型: copywriting, image_gen, video_gen, all")
@click.option("--concurrency", default=1, help="并发数")
def worker(worker_type, concurrency):
    """启动 Worker"""
    if worker_type not in QUEUE_MAP:
        print(f"[!] 未知 Worker 类型: {worker_type}")
        print(f"    可用: {list(QUEUE_MAP.keys())}")
        sys.exit(1)

    queues = QUEUE_MAP[worker_type]
    app_name = f"drama-{worker_type}"

    print(f"\n{'='*50}")
    print(f"  启动 Worker: {worker_type}")
    print(f"  监听队列: {queues}")
    print(f"  并发数: {concurrency}")
    print(f"  Hostname: {app_name}")
    print(f"{'='*50}\n")

    from celery_app import app
    argv = [
        "-A", "celery_app",
        "worker",
        "-Q", ",".join(queues),
        "-l", "INFO",
        "--hostname", f"{app_name}@%h",
        "-P", "solo",
    ]
    app.worker_main(argv)


@cli.command()
@click.option("--category", default="all", help="类别: copywriting, image_gen, video_gen, all")
def scout(category):
    """检索当前最新的 AI API 并推荐 (文案/图片/视频)"""
    from api_scout import scout_all, scout_category, print_report, CATEGORIES

    if category == "all":
        scout_all()
    elif category in CATEGORIES:
        data = scout_category(category)
        print_report(data)
    else:
        print(f"[!] Unknown category: {category}")
        print(f"    Available: all, {', '.join(CATEGORIES.keys())}")


if __name__ == "__main__":
    cli()
