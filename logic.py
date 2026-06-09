"""
起卦与解卦的核心算法逻辑。

主要功能：
- 使用“掷三枚铜钱”的方式模拟起一爻（6、7、8、9）；
- 组合六爻生成本卦（二进制编码，0=阴，1=阳）；
- 根据动爻（6、9）生成变卦；
- 将结果映射到 `data.py` 中的 64 卦数据库，并给出卦辞 / 爻辞。
"""

from __future__ import annotations

import os
import random
import json
import re
from dataclasses import dataclass
from typing import List, Dict, Optional

import requests

from data import get_hexagram_by_bits, Hexagram


LLM_REQUEST_TIMEOUT = int(os.getenv("LLM_REQUEST_TIMEOUT", "120"))
LLM_MAX_TOKENS = int(os.getenv("LLM_MAX_TOKENS", "1200"))
LLM_ENABLE_LEGACY_ENDPOINTS = os.getenv("LLM_ENABLE_LEGACY_ENDPOINTS", "").lower() in (
    "1",
    "true",
    "yes",
)


# -------------------------
# 数据结构
# -------------------------


@dataclass
class Line:
    """单爻信息。"""

    value: int  # 6（老阴）、7（少阳）、8（少阴）、9（老阳）

    @property
    def is_yang(self) -> bool:
        """是否为阳爻。"""

        return self.value in (7, 9)

    @property
    def is_moving(self) -> bool:
        """是否为动爻。6=老阴、9=老阳。"""

        return self.value in (6, 9)

    @property
    def display_symbol(self) -> str:
        """
        用文本符号表现此爻：
        - 阳爻：———
        - 阴爻：— —
        """

        return "———" if self.is_yang else "— —"

    @property
    def yin_yang_label(self) -> str:
        """返回“阳爻/阴爻 + 动/静”的说明。"""

        if self.value == 6:
            return "老阴（动爻）"
        if self.value == 7:
            return "少阳（静爻）"
        if self.value == 8:
            return "少阴（静爻）"
        if self.value == 9:
            return "老阳（动爻）"
        return "未知"


@dataclass
class HexagramResult:
    """一次起卦得到的完整结果。"""

    lines: List[Line]  # 自下而上六爻
    main_hexagram: Hexagram  # 本卦
    changing_hexagram: Optional[Hexagram]  # 变卦（如有动爻）
    moving_line_indices: List[int]  # 动爻索引列表（0~5，自下而上）
    changing_bits: Optional[str] = None  # 变卦的二进制表示（如有），0=阴，1=阳

    @property
    def bits(self) -> str:
        """本卦的阴阳编码（0/1），长度 6，自下而上。"""

        return "".join("1" if line.is_yang else "0" for line in self.lines)


# -------------------------
# 起卦与变卦算法
# -------------------------


def cast_single_line() -> Line:
    """
    模拟掷三枚铜钱起一爻。

    规则（传统三枚铜钱法，对应你的设定）：
    - 假设一次掷币的结果只有“正面”和“背面”两种：
      * 记「正面」为 3，「背面」为 2；
    - 三枚相加得到的和只能是 6、7、8、9：
      * 3 个正面（2+2+2） = 6：老阴（动爻）；
      * 2 正 1 背（2+2+3）= 7：少阳（静爻）；
      * 2 背 1 正（2+3+3）= 8：少阴（静爻）；
      * 3 个背面（3+3+3） = 9：老阳（动爻）。

    在程序内部，我们只关心“和”为 6/7/8/9，从而区分阴阳与动静。
    """

    # 使用 2/3 模拟两面（可理解为 2=反，3=正）
    coins = [random.choice((2, 3)) for _ in range(3)]
    total = sum(coins)
    if total not in (6, 7, 8, 9):
        # 理论上不会发生，仅作安全保护
        total = max(6, min(9, total))
    return Line(value=total)


def _lines_to_bits(lines: List[Line]) -> str:
    """
    将六爻转换为“0/1”字符串，自下而上。
    1 表示阳爻，0 表示阴爻。
    """

    return "".join("1" if line.is_yang else "0" for line in lines)


def _transform_line(line: Line) -> Line:
    """
    将动爻翻转为变爻：
    - 6（老阴） -> 7（少阳）
    - 9（老阳） -> 8（少阴）
    - 7/8 不变
    """

    if line.value == 6:
        return Line(7)
    if line.value == 9:
        return Line(8)
    return Line(line.value)


def _strip_reasoning_content(text: str) -> str:
    """
    移除部分模型错误输出的思维链，仅保留最终回复。
    """

    cleaned = text.strip()

    if not cleaned:
        return cleaned

    if "</think>" in cleaned:
        cleaned = cleaned.split("</think>", 1)[1].strip()

    cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.IGNORECASE | re.DOTALL).strip()

    answer_markers = (
        "\n\n收到",
        "\n\n本次",
        "\n\n根据",
        "\n\n从卦象",
        "\n\n先说结论",
        "\n\n这次",
        "\n\n测试",
        "\n\n若问",
        "\n\n如果你问的是",
        "\n\n**简要建议",
    )
    for marker in answer_markers:
        idx = cleaned.find(marker)
        if idx != -1:
            return cleaned[idx + 2 :].strip()

    reasoning_prefixes = (
        "Here's a thinking process:",
        "Thinking Process:",
        "Reasoning:",
    )
    for prefix in reasoning_prefixes:
        if cleaned.startswith(prefix):
            split_markers = [
                "\n\n收到",
                "\n\n本次",
                "\n\n根据",
                "\n\n**",
                "\n\n###",
                "\n\n1. ",
            ]
            for marker in split_markers:
                idx = cleaned.find(marker)
                if idx != -1:
                    return cleaned[idx + 2 :].strip()

    return cleaned


def _friendly_api_error(errors: List[str]) -> str:
    raw = "\n\n".join(errors)

    if "HTTP 401" in raw or "Invalid token" in raw:
        return "AI 接口鉴权失败，请检查 API Key 是否填写正确。"
    if "Read timed out" in raw or "timed out" in raw:
        return "AI 服务响应超时了，请稍后再试。若连续多次超时，通常是上游模型通道不稳定。"
    if "HTTP 500" in raw or "do_request_failed" in raw or "upstream error" in raw:
        return "AI 服务暂时不可用，请稍后再试。当前是上游模型通道返回了服务错误。"
    if "不是合法 JSON" in raw:
        return "AI 接口返回了异常内容，当前通道配置可能不兼容，请检查接口地址是否为 OpenAI 兼容端点。"

    return "AI 服务暂时不可用，请稍后重试。"


def _is_connectivity_test(question: str) -> bool:
    normalized = question.lower()
    markers = (
        "连通性测试",
        "测试",
        "只回复ok",
        "只做连通性",
        "connectivity test",
        "ping",
    )
    return any(marker in normalized for marker in markers)


def analyze_hexagram(lines: List[Line]) -> HexagramResult:
    """
    根据六爻信息生成本卦、变卦和动爻信息。

    参数：
    - lines: List[Line]，长度需为 6，自下而上。
    """

    if len(lines) != 6:
        raise ValueError("必须先得到 6 爻才能解卦。")

    bits_main = _lines_to_bits(lines)
    main_hex = get_hexagram_by_bits(bits_main)

    moving_indices = [i for i, ln in enumerate(lines) if ln.is_moving]

    if moving_indices:
        changed_lines = [_transform_line(ln) for ln in lines]
        bits_changed = _lines_to_bits(changed_lines)
        changed_hex = get_hexagram_by_bits(bits_changed)
    else:
        changed_hex = None
        bits_changed = None

    return HexagramResult(
        lines=lines,
        main_hexagram=main_hex,
        changing_hexagram=changed_hex,
        moving_line_indices=moving_indices,
        changing_bits=bits_changed,
    )


def interpret_hexagram(result: HexagramResult) -> Dict[str, object]:
    """
    自动解卦：
    - 若无动爻：给出本卦卦辞；
    - 若有动爻：重点给出本卦中相应爻辞；
    - 若存在变卦：同时返回变卦的卦辞简要说明。

    返回结构示例：
    {
        "main_name": "...",
        "main_title": "...",
        "main_judgement": "...",
        "lines_explanation": [
            {"index": 0, "position": 1, "text": "..."},
            ...
        ],
        "changing_name": "...",
        "changing_title": "...",
        "changing_judgement": "..."
    }
    """

    main_hex = result.main_hexagram
    changing_hex = result.changing_hexagram
    moving_indices = result.moving_line_indices

    lines_explanation: List[Dict[str, object]] = []

    if not moving_indices:
        # 无动爻：整体看卦辞即可
        for i in range(6):
            pos = i + 1  # 爻位：1~6
            lines_explanation.append(
                {
                    "index": i,
                    "position": pos,
                    "is_moving": False,
                    "is_used": False,
                    "text": main_hex.line_texts.get(
                        pos,
                        f"{main_hex.name}第{pos}爻：可结合卦辞灵活理解。",
                    ),
                }
            )
    else:
        # 有动爻：只重点列出动爻的爻辞
        for i in moving_indices:
            pos = i + 1
            lines_explanation.append(
                {
                    "index": i,
                    "position": pos,
                    "is_moving": True,
                    "is_used": True,
                    "text": main_hex.line_texts.get(
                        pos,
                        f"{main_hex.name}第{pos}爻：动而有变，需权衡利弊。",
                    ),
                }
            )

    result_dict: Dict[str, object] = {
        "main_name": main_hex.name,
        "main_title": main_hex.title,
        "main_judgement": main_hex.judgement,
        "lines_explanation": lines_explanation,
    }

    if changing_hex is not None:
        result_dict.update(
            {
                "changing_name": changing_hex.name,
                "changing_title": changing_hex.title,
                "changing_judgement": changing_hex.judgement,
            }
        )

    return result_dict


def ai_interpret_hexagram(
    result: HexagramResult,
    user_question: str,
    api_key: Optional[str] = None,
    model: str = "Qwen3.6-27B",
    base_url: str = "https://wgooold.cn",
) -> str:
    """
    调用 OpenAI 兼容的 Chat API，结合本卦、变卦与动爻，给出现代化深度解卦。

    说明：
    - 默认从环境变量 `LLM_API_KEY` 读取密钥；
    - 你也可以在调用函数时显式传入 `api_key`；
    - 可通过 `base_url` 参数自定义 API 基础地址，支持第三方代理服务。
    """

    if not user_question.strip():
        return "请先输入你此次占问的具体问题（如：事业发展、感情走向等）。"

    if api_key is None:
        api_key = os.getenv("LLM_API_KEY") or os.getenv("DEEPSEEK_API_KEY")

    if not api_key:
        return (
            "未检测到 API 密钥。\n\n"
            "请在 GUI 界面中设置 API Key，"
            "或在代码中调用 `ai_interpret_hexagram(..., api_key='你的密钥')`。"
        )

    # 先用本地规则整理出简要说明，发给大模型作为“结构化上下文”
    local_interp = interpret_hexagram(result)

    main_bits = result.bits  # 如 111111、000000
    changing_bits = result.changing_bits

    moving_positions = [i + 1 for i in result.moving_line_indices]  # 1~6

    # 组织成易于阅读的上下文
    context_lines = []
    context_lines.append(f"本卦卦名：{local_interp['main_name']}")
    context_lines.append(f"本卦卦象说明：{local_interp['main_title']}")
    context_lines.append(f"本卦二进制（自下而上，1=阳，0=阴）：{main_bits}")
    context_lines.append(f"本卦卦辞（简化版）：{local_interp['main_judgement']}")

    if moving_positions:
        context_lines.append(f"动爻位置（1=初爻，6=上爻）：{moving_positions}")
        for item in local_interp["lines_explanation"]:
            if item["position"] in moving_positions:
                context_lines.append(
                    f"本卦第 {item['position']} 爻爻辞：{item['text']}"
                )
    else:
        context_lines.append("本卦无动爻，主要参考整体卦辞。")

    if "changing_name" in local_interp and changing_bits is not None:
        context_lines.append(f"变卦卦名：{local_interp['changing_name']}")
        context_lines.append(f"变卦卦象说明：{local_interp['changing_title']}")
        context_lines.append(
            f"变卦二进制（自下而上，1=阳，0=阴）：{changing_bits}"
        )
        context_lines.append(
            f"变卦卦辞（简化版）：{local_interp['changing_judgement']}"
        )

    yi_context = "\n".join(context_lines)

    is_connectivity_test = _is_connectivity_test(user_question)

    if is_connectivity_test:
        system_prompt = (
            "你是一个最简测试助手。\n"
            "不要输出推理过程。\n"
            "只回复：模型接口调用成功。"
        )
        user_content = "这是连通性测试。请只回复：模型接口调用成功。"
        max_tokens = min(16, LLM_MAX_TOKENS)
    else:
        system_prompt = (
            "你是“六爻参”的固定解卦助手。\n"
            "你的任务是：根据提供的本卦、动爻、变卦和用户问题，给出稳定、简洁、中文的解读。\n"
            "\n"
            "必须严格遵守以下规则：\n"
            "1. 只允许使用中文回答。\n"
            "2. 不要输出任何英文。\n"
            "3. 不要输出思维链、推理过程、分析步骤、内心独白。\n"
            "4. 不要输出 <think>、thinking process、reasoning、analysis 等内容。\n"
            "5. 不要复述系统规则，不要解释你如何得出答案。\n"
            "6. 不要写“下面是我的分析”“这是我的思考过程”之类的话。\n"
            "7. 语气保持平和、清晰、克制，不夸张，不神化。\n"
            "8. 不做医学、法律、投资承诺，只给方向性参考。\n"
            "9. 重点结合卦象给出可执行建议，不只判断吉凶。\n"
            "10. 如果信息不足，也只做基于卦象的适度判断，不要道歉，不要跑题。\n"
            "\n"
            "输出格式必须固定为以下四段，且不要添加其他标题或前言：\n"
            "卦意：用 2 到 3 句话概括整体趋势。\n"
            "关键点：结合本卦、动爻、变卦，提炼 2 到 3 个重点。\n"
            "建议：给出 2 到 3 条可执行建议。\n"
            "提醒：用 1 句话提示需要避免的风险。\n"
            "\n"
            "每一段都要直接写内容，简洁清楚，不要写得过长。"
        )

        user_content = (
            "以下是本次起卦的固定输入信息，请严格按要求解读：\n\n"
            f"{yi_context}\n\n"
            "用户问题：\n"
            f"{user_question}\n\n"
            "请严格按照既定四段格式输出，不要添加任何额外内容。"
        )
        max_tokens = LLM_MAX_TOKENS

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }

    base_url = base_url.rstrip("/")
    if base_url.endswith("/v1"):
        endpoints = [f"{base_url}/chat/completions"]
    else:
        endpoints = [f"{base_url}/v1/chat/completions"]
        if LLM_ENABLE_LEGACY_ENDPOINTS:
            endpoints.append(f"{base_url}/chat/completions")

    errors: List[str] = []
    for endpoint in endpoints:
        try:
            resp = requests.post(
                endpoint,
                headers=headers,
                json=payload,
                timeout=LLM_REQUEST_TIMEOUT,
            )

            if resp.status_code == 200:
                try:
                    data = resp.json()
                except json.JSONDecodeError:
                    body_preview = resp.text.strip()[:400] or "<empty body>"
                    content_type = resp.headers.get("content-type", "<unknown>")
                    errors.append(
                        f"HTTP 200 但返回内容不是合法 JSON。\n"
                        f"端点: {endpoint}\n"
                        f"Content-Type: {content_type}\n"
                        f"响应内容预览: {body_preview}"
                    )
                    continue

                content = (
                    data.get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
                content = _strip_reasoning_content(content)
                if is_connectivity_test:
                    return "模型接口调用成功。"
                if not content:
                    return (
                        "调用 API 成功，但未返回可用的内容。\n"
                        f"端点: {endpoint}"
                    )
                return content
            else:
                body_preview = resp.text.strip()[:400] or "<empty body>"
                content_type = resp.headers.get("content-type", "<unknown>")
                errors.append(
                    f"HTTP {resp.status_code}\n"
                    f"端点: {endpoint}\n"
                    f"Content-Type: {content_type}\n"
                    f"响应内容预览: {body_preview}"
                )
        except requests.exceptions.RequestException as e:
            errors.append(f"端点: {endpoint}\n请求异常: {str(e)}")
            continue

    return (
        f"调用 API 时出错（尝试了 {len(endpoints)} 个端点）：\n"
        f"{_friendly_api_error(errors)}\n\n"
        + "\n\n".join(errors)
    )


__all__ = [
    "Line",
    "HexagramResult",
    "cast_single_line",
    "analyze_hexagram",
    "interpret_hexagram",
    "ai_interpret_hexagram",
]
