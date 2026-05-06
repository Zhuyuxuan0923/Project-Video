import os
import json
import logging
from typing import Any

from openai import OpenAI

from .mock import MockAIBackend

logger = logging.getLogger(__name__)


def _repair_json(text: str) -> dict:
    """Try to salvage truncated JSON by auto-closing brackets/braces."""
    stack = []
    for ch in text:
        if ch in "{[":
            stack.append(ch)
        elif ch in "}]":
            if stack and ((stack[-1] == "{" and ch == "}") or (stack[-1] == "[" and ch == "]")):
                stack.pop()
    closing = ""
    for opener in reversed(stack):
        closing += "}" if opener == "{" else "]"
    repaired = text + closing
    return json.loads(repaired)

SYSTEM_PROMPT = """You are a professional short drama scriptwriter. Given a topic, generate a 3-scene short drama script.

Output must be valid JSON with this exact structure:
{
  "title": "drama title in Chinese",
  "scenes": [
    {"id": 1, "location": "location in Chinese", "time": "time of day in Chinese", "description": "vivid scene description in Chinese"},
    {"id": 2, "location": "location in Chinese", "time": "time of day in Chinese", "description": "vivid scene description in Chinese"},
    {"id": 3, "location": "location in Chinese", "time": "time of day in Chinese", "description": "vivid scene description in Chinese"}
  ],
  "narration": ["poetic narration line 1", "poetic narration line 2", "poetic narration line 3"]
}

Rules:
- All text must be in Chinese
- title should be catchy and emotionally resonant
- Each scene description should be vivid, visual, and suitable for image generation
- narration should be poetic, emotionally moving, like voiceover lines
- Output ONLY the JSON object, no markdown, no code blocks"""


class DeepSeekBackend(MockAIBackend):
    """Real backend — DeepSeek for copywriting, SiliconFlow for images, mock for video."""

    def __init__(self, api_key: str | None = None, base_url: str | None = None):
        super().__init__()
        api_key = api_key or os.getenv("DEEPSEEK_API_KEY")
        if not api_key:
            raise ValueError(
                "DEEPSEEK_API_KEY not set. Set it via environment variable or pass api_key= parameter."
            )
        base_url = base_url or os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com/v1")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.client = OpenAI(api_key=api_key, base_url=base_url)
        logger.info("DeepSeekBackend: model=%s base_url=%s", self.model, base_url)

        # SiliconFlow for image generation (optional)
        self.sf_api_key = os.getenv("SILICONFLOW_API_KEY", "")
        self.sf_base_url = os.getenv("SILICONFLOW_BASE_URL", "https://api.siliconflow.cn/v1")
        self.sf_image_model = os.getenv("SILICONFLOW_IMAGE_MODEL", "Qwen/Qwen-Image")
        self.sf_client: OpenAI | None = None
        if self.sf_api_key:
            self.sf_client = OpenAI(api_key=self.sf_api_key, base_url=self.sf_base_url)
            logger.info("DeepSeekBackend: SiliconFlow image model=%s", self.sf_image_model)
        else:
            logger.info("DeepSeekBackend: SILICONFLOW_API_KEY not set, image gen falls back to mock")

    def generate_script(self, topic: str) -> dict[str, Any]:
        logger.info("Calling DeepSeek API for topic: %s", topic)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"请为以下主题创作一部3幕短剧：{topic}"},
            ],
            temperature=0.8,
            max_tokens=4096,
            response_format={"type": "json_object"},
        )

        content = response.choices[0].message.content
        logger.info("DeepSeek raw response length: %d", len(content) if content else 0)

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            # try markdown code block extraction
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            try:
                result = json.loads(content)
            except json.JSONDecodeError:
                # try to repair truncated JSON
                result = _repair_json(content.strip())

        result.setdefault("title", topic)
        result.setdefault("scenes", [])
        result.setdefault("narration", [])
        return result

    def generate_image(self, prompt: str, index: int) -> dict[str, Any]:
        if self.sf_client is None:
            logger.info("SiliconFlow not configured, using mock for image %d", index + 1)
            return super().generate_image(prompt, index)

        full_prompt = f"{prompt}, cinematic composition, soft natural lighting, high quality"
        logger.info("SiliconFlow image gen [%d]: %s", index + 1, full_prompt[:80])

        response = self.sf_client.images.generate(
            model=self.sf_image_model,
            prompt=full_prompt,
            n=1,
            size="1024x576",
        )

        img_url = response.data[0].url
        return {
            "scene_id": index + 1,
            "prompt": prompt,
            "url": img_url,
            "width": getattr(response.data[0], "width", 1024),
            "height": getattr(response.data[0], "height", 576),
        }
