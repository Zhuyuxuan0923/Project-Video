import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from ai_backends import get_backend

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_images(self, script_result: dict, backend_name: str = "mock") -> dict:
    try:
        scenes = script_result.get("scenes", [])
        logger.info("[图片Worker] 开始生成图片，场景数: %d", len(scenes))
        backend = get_backend(backend_name)
        images = []
        for i, scene in enumerate(scenes):
            prompt = f"{scene['location']}, {scene['description']}, cinematic lighting, 8K"
            img = backend.generate_image(prompt, i)
            images.append(img)
            logger.info("[图片Worker] 场景 %d/%d 图片已生成: %s", i + 1, len(scenes), img["url"])
        script_result["images"] = images
        logger.info("[图片Worker] 所有图片生成完成，共 %d 张", len(images))
        return script_result
    except Exception as exc:
        logger.error("[图片Worker] 生成失败 (第%d次): %s", self.request.retries + 1, exc)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error("[图片Worker] 已达最大重试次数，任务失败")
            raise
