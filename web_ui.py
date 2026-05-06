import time
from pathlib import Path

from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader

import celery_app  # noqa
from orchestrator import DramaOrchestrator, STAGES

app = FastAPI(title="AI Drama Studio")
_jinja_env = Environment(loader=FileSystemLoader(str(Path(__file__).parent / "templates")))

HISTORY: list[dict] = []


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    template = _jinja_env.get_template("index.html")
    return HTMLResponse(template.render(
        request=request,
        stage_keys=[s[0] for s in STAGES],
        stage_labels=[s[1] for s in STAGES],
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
async def advance_stage(task_id: str = Form(...), stage: str = Form(...)):
    from celery.result import AsyncResult

    r = AsyncResult(task_id)
    if r.state != "SUCCESS":
        return JSONResponse({"error": "previous stage not completed", "state": r.state})

    orch = DramaOrchestrator()
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
