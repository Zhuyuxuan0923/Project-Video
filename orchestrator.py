import time
import logging
from typing import Any

import celery_app  # noqa: F401 - must load Celery app before importing tasks
from celery.result import AsyncResult
from tasks.copywriting import generate_script
from tasks.image_gen import generate_images
from tasks.video_gen import generate_video

logger = logging.getLogger(__name__)

STAGES = [
    ("copywriting", "Script Generation"),
    ("image_gen", "Image Generation"),
    ("video_gen", "Video Composition"),
]


class DramaOrchestrator:

    def __init__(self, backend_name: str = "mock"):
        self.backend_name = backend_name

    def get_status(self, task_id: str) -> dict[str, Any]:
        r = AsyncResult(task_id)
        return {
            "task_id": task_id,
            "state": r.state,
            "info": r.info if r.state in ("PROGRESS", "SUCCESS") else None,
        }

    def _wait_for_task(self, task_id: str, stage_name: str, timeout: float = 300.0) -> dict:
        start = time.time()

        while True:
            elapsed = time.time() - start
            if elapsed > timeout:
                return {"state": "TIMEOUT", "error": f"Timeout after {timeout}s"}

            status = self.get_status(task_id)
            state = status["state"]

            if state == "SUCCESS":
                return {"state": "SUCCESS", "info": status["info"]}
            elif state == "FAILURE":
                return {"state": "FAILURE", "error": status["info"]}
            elif state == "RETRY":
                print(f"      [~] {stage_name}: retrying...")
            else:
                dots = "." * (int(elapsed) % 4 + 1)
                print(f"\r      [>] {stage_name}: running{dots}   ", end="")

            time.sleep(1.0)

    def run_and_wait(self, topic: str, timeout: float = 600.0) -> dict:
        print(f"\n{'='*55}")
        print(f"  AI Drama Auto-Generation System")
        print(f"  Topic: {topic}")
        print(f"  Backend: {self.backend_name}")
        print(f"{'='*55}\n")

        stage_timeout = timeout / 3.0
        data = {"topic": topic}

        for stage_key, stage_name in STAGES:
            print(f"  [{stage_key.upper()}] Starting {stage_name}...")

            try:
                task_id = self._dispatch(stage_key, data)
                print(f"      Task ID: {task_id}")
                result = self._wait_for_task(task_id, stage_name, timeout=stage_timeout)

                if result["state"] == "FAILURE":
                    print(f"\n      [XX] {stage_name} FAILED: {result.get('error')}")
                    return {"state": "FAILURE", "stage": stage_key, "error": result.get("error")}
                elif result["state"] == "TIMEOUT":
                    print(f"\n      [!] {stage_name} TIMEOUT")
                    return {"state": "TIMEOUT", "stage": stage_key}

                print(f"\r      [OK] {stage_name}: completed{' '*20}")
                data = result["info"]

            except Exception as e:
                print(f"\n      [XX] {stage_name} error: {e}")
                return {"state": "FAILURE", "stage": stage_key, "error": str(e)}

        print(f"\n{'='*55}")
        print(f"  *** Final Result ***")
        print(f"{'='*55}")
        self._print_result(data)
        return {"state": "SUCCESS", "info": data}

    def _dispatch(self, stage: str, data: dict) -> str:
        if stage == "copywriting":
            result = generate_script.delay(data["topic"], backend_name=self.backend_name)
        elif stage == "image_gen":
            result = generate_images.delay(data, backend_name=self.backend_name)
        elif stage == "video_gen":
            result = generate_video.delay(data, backend_name=self.backend_name)
        else:
            raise ValueError(f"Unknown stage: {stage}")
        return result.id

    @staticmethod
    def _print_result(info: dict):
        if not info:
            return
        print(f"  Title: {info.get('title', 'N/A')}")
        print(f"  Scenes: {len(info.get('scenes', []))}")

        images = info.get("images", [])
        print(f"  Images: {len(images)}")
        for img in images:
            print(f"    - Scene {img.get('scene_id')}: {img.get('url')}")

        video = info.get("video", {})
        if video:
            print(f"  Video URL: {video.get('video_url', 'N/A')}")
            print(f"  Duration: {video.get('duration', 'N/A')}s")
            print(f"  Resolution: {video.get('resolution', 'N/A')}")

        narrations = info.get("narration", [])
        if narrations:
            print(f"\n  Narrations:")
            for i, n in enumerate(narrations, 1):
                print(f"    {i}. {n}")
        print()
