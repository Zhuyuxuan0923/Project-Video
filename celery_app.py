import os
from pathlib import Path

# 自动加载项目根目录的 .env 文件
_env_path = Path(__file__).parent / ".env"
if _env_path.exists():
    for _line in _env_path.read_text(encoding="utf-8").splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _val = _line.split("=", 1)
            _key, _val = _key.strip(), _val.strip()
            if _key not in os.environ:
                os.environ[_key] = _val

from celery import Celery

app = Celery("drama")
app.config_from_object("config")

app.conf.update(
    task_routes={
        "tasks.copywriting.generate_script": {"queue": "copywriting"},
        "tasks.image_gen.generate_images": {"queue": "image_gen"},
        "tasks.video_gen.generate_video": {"queue": "video_gen"},
    },
    imports=["tasks.copywriting", "tasks.image_gen", "tasks.video_gen"],
)
