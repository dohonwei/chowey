"""
周易 64 卦数据与八卦编码。

说明：
- 为了方便程序使用，这里采用“程序友好”的自动生成数据库：
  - 先定义 8 个基本卦（八卦）的三爻二进制编码与含义；
  - 再把上卦、下卦两两组合，自动生成 64 卦的基础信息和简单卦辞、爻辞。
- 并没有完全使用传统卦名（如“乾为天”“地雷复”等），
  但保证 8×8 组合齐全，逻辑清晰，便于扩展与替换为权威文本。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass(frozen=True)
class Trigram:
    """三爻卦（八卦）的基本信息。"""

    name: str          # 名称，如“乾”
    meaning: str       # 象义，如“天”
    bits: str          # 例如 '111'，从下到上三爻阴阳编码（1=阳，0=阴）


@dataclass
class Hexagram:
    """六爻卦（64 卦）的信息。"""

    upper_trigram: Trigram
    lower_trigram: Trigram
    name: str          # 卦名（此处采用“上卦名+下卦名”的组合名）
    title: str         # 简短题目或别名，如“天在上，地在下”
    judgement: str     # 卦辞（简化版）
    line_texts: Dict[int, str]  # 爻辞，key 为 1~6（1 为初爻，6 为上爻）


# 八卦的二进制编码（自下而上：1=阳爻，0=阴爻）
# 该编码方式在不少易学资料和计算机实现中很常见：
# 乾 111、兑 110、离 101、震 100、巽 011、坎 010、艮 001、坤 000
TRIGRAMS_BY_BITS: Dict[str, Trigram] = {
    "111": Trigram("乾", "天", "111"),
    "110": Trigram("兑", "泽", "110"),
    "101": Trigram("离", "火", "101"),
    "100": Trigram("震", "雷", "100"),
    "011": Trigram("巽", "风", "011"),
    "010": Trigram("坎", "水", "010"),
    "001": Trigram("艮", "山", "001"),
    "000": Trigram("坤", "地", "000"),
}

# 64 卦传统名称映射（按照《周易》传统卦名）
# key 为六爻二进制编码（自下而上），value 为传统卦名
HEXAGRAM_NAMES: Dict[str, str] = {
    "111111": "乾为天",
    "000000": "坤为地",
    "010100": "水雷屯",
    "001010": "山水蒙",
    "010111": "水天需",
    "111010": "天水讼",
    "000010": "地水师",
    "010000": "水地比",
    "011111": "风天小畜",
    "111110": "天泽履",
    "000111": "地天泰",
    "111000": "天地否",
    "111101": "天火同人",
    "101111": "火天大有",
    "000001": "地山谦",
    "100000": "雷地豫",
    "110100": "泽雷随",
    "001011": "山风蛊",
    "000110": "地泽临",
    "011000": "风地观",
    "101100": "火雷噬嗑",
    "001101": "山火贲",
    "001000": "山地剥",
    "000100": "地雷复",
    "111100": "天雷无妄",
    "001111": "山天大畜",
    "001100": "山雷颐",
    "110011": "泽风大过",
    "010010": "坎为水",
    "101101": "离为火",
    "110001": "泽山咸",
    "100011": "雷风恒",
    "111001": "天山遁",
    "100111": "雷天大壮",
    "101000": "火地晋",
    "000101": "地火明夷",
    "011101": "风火家人",
    "101110": "火泽睽",
    "010001": "水山蹇",
    "100010": "雷水解",
    "001110": "山泽损",
    "011100": "风雷益",
    "110111": "泽天夬",
    "111011": "天风姤",
    "110000": "泽地萃",
    "000011": "地风升",
    "010011": "水风井",
    "011010": "风水涣",
    "110010": "泽水困",
    "010110": "水泽节",
    "110101": "泽火革",
    "100101": "雷火丰",
    "101001": "火山旅",
    "011011": "巽为风",
    "110110": "兑为泽",
    "011001": "风山渐",
    "100110": "雷泽归妹",
    "100100": "震为雷",
    "001001": "艮为山",
    "011110": "风泽中孚",
    "100001": "雷山小过",
    "101010": "水火既济",
    "010101": "火水未济",
}


def _generate_hexagram_name(upper: Trigram, lower: Trigram, bits: str) -> str:
    """
    生成传统卦名（简化格式，如"大壮卦"）。

    优先从 HEXAGRAM_NAMES 中查找传统名称，然后提取核心卦名。
    如果找不到则使用上下卦组合名称作为后备。
    """
    # 构造用于查字典的 Key（上卦在前，下卦在后）
    lookup_key = upper.bits + lower.bits

    if lookup_key in HEXAGRAM_NAMES:
        full_name = HEXAGRAM_NAMES[lookup_key]
        # 从完整名称中提取核心卦名
        # 规则：
        # 1. 如果包含"为"，如"乾为天" -> "乾卦"
        # 2. 否则，提取最后2-3个字作为核心名称，如"雷天大壮" -> "大壮卦"
        if "为" in full_name:
            # 如"乾为天" -> "乾卦"，"坎为水" -> "坎卦"
            core = full_name.split("为")[0]
            return f"{core}卦"
        else:
            # 如"雷天大壮" -> "大壮卦"，"水火既济" -> "既济卦"
            # 核心名称通常是最后2个字（如"大壮"、"既济"、"小畜"）
            # 但有些是3个字（如"小过"），有些是1个字（如"泰"、"否"）
            # 简单策略：取最后2个字，如果只有3个字则取最后1个字
            if len(full_name) == 3:
                core = full_name[-1]
            elif len(full_name) == 4:
                core = full_name[-2:]
            else:
                # 5个字或更多，取最后2个字
                core = full_name[-2:]
            return f"{core}卦"
    # 后备方案：使用上下卦组合
    return f"{upper.name}{lower.name}卦"


def _generate_hexagram_title(upper: Trigram, lower: Trigram) -> str:
    """生成简短题目。"""

    return f"{upper.meaning}在上，{lower.meaning}在下"


def _generate_hexagram_judgement(upper: Trigram, lower: Trigram) -> str:
    """
    生成简短卦辞说明。

    这里使用现代化、通俗的说明文字，方便程序演示；
    如需严谨研究，可替换为《易经》原文或权威注解。
    """

    return (
        f"{upper.name}{lower.name}卦：上为{upper.meaning}，下为{lower.meaning}，"
        f"象征着两种力量的互动与平衡，可据此联想到现实中的局势变化。"
    )


def _generate_line_texts(upper: Trigram, lower: Trigram) -> Dict[int, str]:
    """
    为 1~6 爻生成简易爻辞。

    为了保证程序可运行，使用模板化语句。
    你可以在此处替换为更专业、细致的爻辞内容。
    """

    texts: Dict[int, str] = {}
    base = f"{upper.name}{lower.name}卦"

    meanings = {
        1: "初爻，多为事情萌芽、起步阶段，可顺势而为。",
        2: "二爻，代表内在调整与稳定基础，宜沉稳审慎。",
        3: "三爻，象征矛盾与摇摆，进退之间需权衡利弊。",
        4: "四爻，多与对外拓展、远景规划有关，需看清方向。",
        5: "五爻，常为卦中主爻，意味着关键人物或关键决策。",
        6: "上爻，事情发展至极处，有圆满也有转折之机。",
    }

    for i in range(1, 7):
        texts[i] = f"{base}第{i}爻：{meanings[i]}"

    return texts


def _build_hexagram(upper_bits: str, lower_bits: str) -> Hexagram:
    """根据上下卦的三爻二进制编码构建一个六爻卦对象。"""

    upper = TRIGRAMS_BY_BITS[upper_bits]
    lower = TRIGRAMS_BY_BITS[lower_bits]
    # 组合成六爻二进制编码（自下而上：下卦在前，上卦在后）
    bits = lower_bits + upper_bits
    name = _generate_hexagram_name(upper, lower, bits)
    title = _generate_hexagram_title(upper, lower)
    judgement = _generate_hexagram_judgement(upper, lower)
    line_texts = _generate_line_texts(upper, lower)

    return Hexagram(
        upper_trigram=upper,
        lower_trigram=lower,
        name=name,
        title=title,
        judgement=judgement,
        line_texts=line_texts,
    )


# 64 卦总表：key 为 (upper_bits, lower_bits) 这样的 6 位编码切分
# 也可以用 (upper_name, lower_name) 等形式作为 key，这里选择 bits 便于算法处理。
HEXAGRAMS_BY_BITS: Dict[Tuple[str, str], Hexagram] = {}

for upper_bits in TRIGRAMS_BY_BITS:
    for lower_bits in TRIGRAMS_BY_BITS:
        HEXAGRAMS_BY_BITS[(upper_bits, lower_bits)] = _build_hexagram(
            upper_bits, lower_bits
        )


def get_hexagram_by_bits(bits: str) -> Hexagram:
    """
    根据六爻阴阳编码字符串获取 Hexagram。

    参数：
    - bits: 长度 6 的字符串，如 '101010'，从下到上分别表示 1~6 爻。
    """

    if len(bits) != 6 or any(ch not in "01" for ch in bits):
        raise ValueError("bits 必须是由 0/1 组成的 6 位字符串（自下而上）。")

    lower_bits = bits[:3]
    upper_bits = bits[3:]

    if upper_bits not in TRIGRAMS_BY_BITS or lower_bits not in TRIGRAMS_BY_BITS:
        raise KeyError(f"未找到对应的八卦组合：upper={upper_bits}, lower={lower_bits}")

    return HEXAGRAMS_BY_BITS[(upper_bits, lower_bits)]


__all__ = [
    "Trigram",
    "Hexagram",
    "TRIGRAMS_BY_BITS",
    "HEXAGRAMS_BY_BITS",
    "get_hexagram_by_bits",
]



