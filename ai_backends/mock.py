import time
import uuid
import random
from .base import BaseAIBackend

SAMPLE_SCRIPTS = {
    "default": {
        "title": "命运的重逢",
        "scenes": [
            {"id": 1, "location": "繁华都市的咖啡厅", "time": "午后", "description": "女主角坐在窗边，阳光洒在她的脸上"},
            {"id": 2, "location": "繁忙的十字路口", "time": "黄昏", "description": "男主与女主擦肩而过，似曾相识"},
            {"id": 3, "location": "海边长椅", "time": "傍晚", "description": "两人终于认出彼此，紧紧相拥"},
        ],
        "narration": [
            "在这座拥有千万人口的城市里，两个人的相遇只需要一个瞬间。",
            "命运总是喜欢开玩笑，让彼此思念的人擦肩而过。",
            "真正的缘分，终究会跨过时间和距离，将两颗心再次连接在一起。",
        ],
    }
}


class MockAIBackend(BaseAIBackend):

    def generate_script(self, topic: str) -> dict:
        time.sleep(2)
        return SAMPLE_SCRIPTS.get("default").copy()

    def generate_image(self, prompt: str, index: int) -> dict:
        time.sleep(1.5)
        colors = ["FF6B6B", "4ECDC4", "45B7D1", "96CEB4", "FFEAA7", "DDA0DD", "98D8C8"]
        return {
            "scene_id": index + 1,
            "prompt": prompt,
            "url": f"https://picsum.photos/seed/{uuid.uuid4().hex[:8]}/800/600",
            "width": 800,
            "height": 600,
        }

    def generate_video(self, scenes: list[dict], images: list[dict]) -> dict:
        time.sleep(3)
        return {
            "video_url": f"https://example.com/videos/{uuid.uuid4().hex}.mp4",
            "duration": len(images) * random.randint(3, 6),
            "format": "mp4",
            "resolution": "1920x1080",
            "scenes": scenes,
        }
