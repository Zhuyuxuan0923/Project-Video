import os

broker_url = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
result_backend = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/1")

task_serializer = "json"
result_serializer = "json"
accept_content = ["json"]
timezone = "Asia/Shanghai"
enable_utc = True

task_acks_late = True
task_reject_on_worker_lost = True
task_track_started = True

task_default_queue = "default"
task_queues = {
    "copywriting": {"exchange": "copywriting", "routing_key": "copywriting"},
    "image_gen": {"exchange": "image_gen", "routing_key": "image_gen"},
    "video_gen": {"exchange": "video_gen", "routing_key": "video_gen"},
}

task_routes = {
    "tasks.copywriting.*": {"queue": "copywriting"},
    "tasks.image_gen.*": {"queue": "image_gen"},
    "tasks.video_gen.*": {"queue": "video_gen"},
}

task_default_retry_delay = 60
task_max_retries = 3
