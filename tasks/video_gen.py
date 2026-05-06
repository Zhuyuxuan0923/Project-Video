import logging
from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from ai_backends import get_backend

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_video(self, script_result: dict, backend_name: str = "mock") -> dict:
    try:
        scenes = script_result.get("scenes", [])
        images = script_result.get("images", [])
        logger.info("[视频Worker] 开始合成视频，场景数: %d，图片数: %d", len(scenes), len(images))
        backend = get_backend(backend_name)
        video_result = backend.generate_video(scenes, images)
        result = {
            "topic": script_result.get("topic", ""),
            "title": script_result.get("title", ""),
            "scenes": scenes,
            "images": images,
            "narration": script_result.get("narration", []),
            "video": video_result,
        }
        logger.info("[视频Worker] 视频合成完成: %s (时长: %ds)",
                    video_result["video_url"], video_result["duration"])
        return result
    except Exception as exc:
        logger.error("[视频Worker] 合成失败 (第%d次): %s", self.request.retries + 1, exc)
        try:
            raise self.retry(exc=exc)
        except MaxRetriesExceededError:
            logger.error("[视频Worker] 已达最大重试次数，任务失败")
            raise
