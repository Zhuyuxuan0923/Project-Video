import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from ai_backends import get_backend

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_script(self, topic: str, backend_name: str = "mock") -> dict:
    try:
        logger.info("[文案Worker] 开始生成短剧文案，主题: %s", topic)
        backend = get_backend(backend_name)
        result = backend.generate_script(topic)
        result["topic"] = topic
        logger.info("[文案Worker] 文案生成完成，标题: %s，场景数: %d",
                    result["title"], len(result["scenes"]))
        return result
    except Exception as exc:
        logger.error("[文案Worker] 生成失败 (第%d次): %s", self.request.retries + 1, exc)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error("[文案Worker] 已达最大重试次数，任务失败")
            raise
