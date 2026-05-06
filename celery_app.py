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
