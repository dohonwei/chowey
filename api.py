"""
基于 FastAPI 的周易起卦与 AI 解卦后端服务。

用法概览（本机开发）：
1. 安装依赖：
   pip install fastapi "uvicorn[standard]" requests

2. 启动服务（在本项目目录）：
   uvicorn api:app --reload --host 0.0.0.0 --port 8000

3. 微信小程序中通过 `wx.request` 调用：
   - POST http://你的电脑局域网IP:8000/cast
   - POST http://你的电脑局域网IP:8000/ai

说明：
- 逻辑全部复用 `logic.py` / `data.py`；
- 大模型接口使用 OpenAI 兼容协议；
- 建议把密钥放在环境变量 `LLM_API_KEY` 中，
  或在 `ai_interpret_hexagram` 调用时传入 api_key（仅限本机自用）。
"""

from __future__ import annotations

import os
import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from logic import (
    Line,
    analyze_hexagram,
    cast_single_line,
    interpret_hexagram,
    ai_interpret_hexagram,
)

BASE_DIR = Path(__file__).resolve().parent
WEB_DIR = BASE_DIR / "web"
GUI_CONFIG_PATH = BASE_DIR / "gui_config.json"


def _load_local_config() -> dict:
    if not GUI_CONFIG_PATH.exists():
        return {}
    try:
        with GUI_CONFIG_PATH.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


LOCAL_CONFIG = _load_local_config()
DEFAULT_MODEL_NAME = (
    os.getenv("LLM_MODEL")
    or os.getenv("DEEPSEEK_MODEL")
    or LOCAL_CONFIG.get("model_name")
    or "Qwen3.6-27B"
)
DEFAULT_BASE_URL = (
    os.getenv("LLM_BASE_URL")
    or os.getenv("DEEPSEEK_BASE_URL")
    or LOCAL_CONFIG.get("base_url")
    or "https://wgooold.cn"
)

app = FastAPI(
    title="YiJing API",
    description="用于网页与小程序调用的周易起卦与 AI 解卦后端。",
    version="1.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=WEB_DIR), name="static")


# -------------------------
# Pydantic 数据模型
# -------------------------


class LineOut(BaseModel):
    value: int = Field(..., description="6=老阴, 7=少阳, 8=少阴, 9=老阳")
    is_yang: bool
    is_moving: bool
    display_symbol: str
    yin_yang_label: str


class CastResponse(BaseModel):
    lines: List[LineOut]
    bits: str = Field(..., description="本卦二进制（自下而上，1=阳，0=阴），如 111111")
    moving_positions: List[int] = Field(
        ..., description="动爻位置列表（1=初爻，6=上爻）"
    )
    interpretation: dict


class AnalyzeRequest(BaseModel):
    lines: List[int] = Field(
        ...,
        description="六爻数值列表，长度 6，自下而上，每个值为 6/7/8/9。",
        min_items=6,
        max_items=6,
    )


class AiRequest(BaseModel):
    lines: List[int] = Field(
        ...,
        description="六爻数值列表，长度 6，自下而上，每个值为 6/7/8/9。",
        min_items=6,
        max_items=6,
    )
    question: str = Field(..., description="用户提问，如：事业/感情/健康等。")
    # 可选：若你想单独为后端设置一套密钥，可以在此传入
    api_key: Optional[str] = Field(
        None,
        description="（可选）API Key；不传则从环境变量 LLM_API_KEY 或 DEEPSEEK_API_KEY 读取。",
    )
    model: Optional[str] = Field(
        None,
        description="（可选）模型名称；不传则使用环境变量 LLM_MODEL 或默认值。",
    )


class AiResponse(BaseModel):
    ai_text: str


# -------------------------
# 工具函数
# -------------------------


def _lines_from_values(values: List[int]) -> List[Line]:
    """将 [6,7,8,9] 数组转为 Line 列表。"""

    if len(values) != 6:
        raise ValueError("必须提供 6 个爻值。")
    for v in values:
        if v not in (6, 7, 8, 9):
            raise ValueError("每一爻的值必须是 6、7、8 或 9。")
    return [Line(value=v) for v in values]


def _serialize_lines(lines: List[Line]) -> List[LineOut]:
    """把 Line 列表序列化为可 JSON 输出的结构。"""

    return [
        LineOut(
            value=ln.value,
            is_yang=ln.is_yang,
            is_moving=ln.is_moving,
            display_symbol=ln.display_symbol,
            yin_yang_label=ln.yin_yang_label,
        )
        for ln in lines
    ]


# -------------------------
# 路由：起卦 & 解卦
# -------------------------


@app.post("/cast", response_model=CastResponse)
def cast_hexagram() -> CastResponse:
    """
    服务器端随机起一卦（掷钱 6 次），返回六爻、本卦二进制、动爻及本地解卦结果。

    适合微信小程序直接调用，而不在前端做随机数逻辑。
    """

    lines_py: List[Line] = [cast_single_line() for _ in range(6)]
    result = analyze_hexagram(lines_py)
    interp = interpret_hexagram(result)

    moving_positions = [i + 1 for i in result.moving_line_indices]

    return CastResponse(
        lines=_serialize_lines(lines_py),
        bits=result.bits,
        moving_positions=moving_positions,
        interpretation=interp,
    )


@app.post("/analyze", response_model=CastResponse)
def analyze_from_client(req: AnalyzeRequest) -> CastResponse:
    """
    根据前端提供的 6 个爻值（6/7/8/9）进行解卦。

    如果你希望在微信小程序端自己做“掷钱”随机，只需把 6 个值传到这个接口即可。
    """

    lines_py = _lines_from_values(req.lines)
    result = analyze_hexagram(lines_py)
    interp = interpret_hexagram(result)
    moving_positions = [i + 1 for i in result.moving_line_indices]

    return CastResponse(
        lines=_serialize_lines(lines_py),
        bits=result.bits,
        moving_positions=moving_positions,
        interpretation=interp,
    )


@app.post("/ai", response_model=AiResponse)
def ai_explain(req: AiRequest) -> AiResponse:
    """
    调用 OpenAI 兼容大模型，对已经确定的六爻 + 本卦/变卦进行 AI 深度解卦。

    一般调用流程（前端）：
    1. 先用 /cast 或 /analyze 拿到六爻与本地解卦；
    2. 然后把同一组六爻和用户提问传给 /ai。
    """

    lines_py = _lines_from_values(req.lines)
    result = analyze_hexagram(lines_py)

    api_key = (
        req.api_key
        or os.getenv("LLM_API_KEY")
        or os.getenv("DEEPSEEK_API_KEY")
        or LOCAL_CONFIG.get("api_key")
    )

    ai_text = ai_interpret_hexagram(
        result,
        user_question=req.question,
        api_key=api_key,
        model=req.model or DEFAULT_MODEL_NAME,
        base_url=DEFAULT_BASE_URL,
    )

    return AiResponse(ai_text=ai_text)


@app.get("/")
def web_index():
    """返回网页端入口。"""

    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {"status": "ok", "message": "YiJing API is running, but web assets are missing."}


@app.get("/health")
def health() -> dict:
    """简单健康检查。"""

    return {"status": "ok", "message": "YiJing API is running."}
