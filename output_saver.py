import json
import logging
import urllib.request
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

OUTPUTS_DIR = Path(__file__).parent / "outputs"


def _sanitize(name: str) -> str:
    return "".join(c for c in name if c.isalnum() or c in "._- ").strip()[:40]


def make_output_folder(topic: str) -> Path:
    folder = OUTPUTS_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{_sanitize(topic)}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def save_images(images: list[dict], topic: str, task_id: str = "") -> tuple[list[dict], str]:
    """Download images to outputs/ folder. Returns (updated_images, folder_path)."""
    folder = make_output_folder(topic)
    img_dir = folder / "images"
    img_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Saving %d images to %s", len(images), img_dir)
    for img in images:
        url = img.get("url", "")
        scene_id = img.get("scene_id", 0)
        local_path = img_dir / f"scene_{scene_id}.png"
        try:
            urllib.request.urlretrieve(url, str(local_path))
            img["local_path"] = str(local_path)
            img["local_size"] = local_path.stat().st_size
            logger.info("  Saved scene %d: %s (%d bytes)", scene_id, local_path.name, img["local_size"])
        except Exception as e:
            logger.error("  Failed to download scene %d: %s", scene_id, e)
            img["local_path"] = url

    with open(folder / "images.json", "w", encoding="utf-8") as f:
        json.dump(images, f, ensure_ascii=False, indent=2)

    return images, str(folder)


def save_result(result: dict, task_id: str = "", folder: str | None = None) -> str:
    """Save complete result JSON and script text. Uses existing folder if provided."""
    topic = result.get("topic", "untitled")
    title = result.get("title", "untitled")
    out = Path(folder) if folder else make_output_folder(topic)
    out.mkdir(parents=True, exist_ok=True)

    with open(out / "result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    with open(out / "script.txt", "w", encoding="utf-8") as f:
        f.write(f"《{title}》\n")
        f.write(f"主题: {topic}\n")
        f.write(f"{'='*40}\n\n")
        for s in result.get("scenes", []):
            f.write(f"场景 {s['id']}: {s['location']} / {s['time']}\n")
            f.write(f"  {s['description']}\n\n")
        f.write(f"{'='*40}\n\n")
        f.write("旁白:\n")
        for i, n in enumerate(result.get("narration", []), 1):
            f.write(f"  {i}. {n}\n")

    logger.info("Result saved to %s", out)
    return str(out)
