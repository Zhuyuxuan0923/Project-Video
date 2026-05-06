import json
import time
import urllib.request
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

import celery_app  # noqa
from orchestrator import DramaOrchestrator, STAGES
from ai_backends import _registry

app = FastAPI(title="AI Drama Studio")
_jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

HISTORY: list[dict] = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    template = _jinja_env.get_template("index.html")
    backends = list(_registry.keys())
    return HTMLResponse(template.render(
        request=request,
        stage_keys=[s[0] for s in STAGES],
        stage_labels=[s[1] for s in STAGES],
        backends=backends,
    ))


@app.post("/api/submit")
async def submit(topic: str = Form(...), backend: str = Form("mock")):
    orch = DramaOrchestrator(backend_name=backend)
    task_id = orch._dispatch("copywriting", {"topic": topic})
    entry = {
        "id": task_id,
        "topic": topic,
        "backend": backend,
        "stage": "copywriting",
        "state": "PENDING",
        "submitted_at": time.strftime("%H:%M:%S"),
    }
    HISTORY.insert(0, entry)
    return JSONResponse(entry)


@app.get("/api/tasks")
async def list_tasks():
    from celery.result import AsyncResult

    for entry in HISTORY:
        if entry["state"] in ("SUCCESS", "FAILURE"):
            continue
        r = AsyncResult(entry["id"])
        entry["state"] = r.state
        if r.state == "SUCCESS":
            entry["result"] = r.info
            entry["stage"] = "done"
        elif r.state == "FAILURE":
            entry["error"] = str(r.info)
    return JSONResponse(HISTORY[:20])


@app.get("/api/task/{task_id}")
async def get_task(task_id: str):
    from celery.result import AsyncResult
    r = AsyncResult(task_id)
    data = {"id": task_id, "state": r.state}
    if r.state == "SUCCESS":
        data["result"] = r.info
        all_task_ids = [h["id"] for h in HISTORY]
        if task_id in all_task_ids:
            idx = all_task_ids.index(task_id)
            HISTORY[idx]["state"] = "SUCCESS"
            HISTORY[idx]["result"] = r.info
            HISTORY[idx]["stage"] = "done"
    elif r.state == "FAILURE":
        data["error"] = str(r.info)
    return JSONResponse(data)


@app.post("/api/advance")
async def advance_stage(task_id: str = Form(...), stage: str = Form(...), backend: str = Form("mock")):
    from celery.result import AsyncResult

    r = AsyncResult(task_id)
    if r.state != "SUCCESS":
        return JSONResponse({"error": "previous stage not completed", "state": r.state})

    orch = DramaOrchestrator(backend_name=backend)
    next_stage = None
    stage_order = [s[0] for s in STAGES]
    if stage in stage_order:
        idx = stage_order.index(stage)
        if idx + 1 < len(stage_order):
            next_stage = stage_order[idx + 1]
    if next_stage is None:
        return JSONResponse({"error": "no next stage"})

    new_id = orch._dispatch(next_stage, r.info)
    entry = {
        "id": new_id,
        "topic": r.info.get("topic", ""),
        "backend": orch.backend_name,
        "stage": next_stage,
        "state": "PENDING",
        "submitted_at": time.strftime("%H:%M:%S"),
    }
    HISTORY.insert(0, entry)
    return JSONResponse(entry)


@app.post("/api/save")
async def save_result(task_id: str = Form(...), save_path: str = Form(...)):
    from celery.result import AsyncResult

    result_data = None
    for entry in HISTORY:
        if entry["id"] == task_id and entry.get("result"):
            result_data = entry["result"]
            break

    if result_data is None:
        r = AsyncResult(task_id)
        if r.state == "SUCCESS":
            result_data = r.info
    if result_data is None:
        return JSONResponse({"error": "task not found or not completed"}, status_code=404)

    out = Path(save_path)
    try:
        out.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        return JSONResponse({"error": f"cannot create directory: {e}"}, status_code=400)

    images = result_data.get("images", [])
    img_dir = out / "images"
    img_dir.mkdir(parents=True, exist_ok=True)
    saved_count = 0
    for img in images:
        url = img.get("url", "")
        scene_id = img.get("scene_id", saved_count)
        local_path = img_dir / f"scene_{scene_id}.png"
        try:
            urllib.request.urlretrieve(url, str(local_path))
            img["local_path"] = str(local_path)
            img["local_size"] = local_path.stat().st_size
            saved_count += 1
        except Exception as e:
            img["local_error"] = str(e)

    topic = result_data.get("topic", "untitled")
    title = result_data.get("title", "untitled")

    with open(out / "result.json", "w", encoding="utf-8") as f:
        json.dump(result_data, f, ensure_ascii=False, indent=2)

    with open(out / "script.txt", "w", encoding="utf-8") as f:
        f.write(f"《{title}》\n")
        f.write(f"主题: {topic}\n")
        f.write(f"{'='*40}\n\n")
        for s in result_data.get("scenes", []):
            f.write(f"场景 {s.get('id', '')}: {s.get('location', '')} / {s.get('time', '')}\n")
            f.write(f"  {s.get('description', '')}\n\n")
        f.write(f"{'='*40}\n\n")
        f.write("旁白:\n")
        for i, n in enumerate(result_data.get("narration", []), 1):
            f.write(f"  {i}. {n}\n")

    return JSONResponse({
        "ok": True,
        "path": str(out),
        "images_saved": saved_count,
        "files": ["script.txt", "result.json"] + [f"images/scene_{img.get('scene_id', i)}.png" for i, img in enumerate(images)],
    })
