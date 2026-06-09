"""
基于 Streamlit 的周易起卦与解卦小应用。

运行方式：
1. 安装依赖（至少需要 streamlit）：
   pip install streamlit
2. 在本目录下运行：
   streamlit run app.py
"""

from __future__ import annotations

from typing import List

import streamlit as st

from logic import (
    Line,
    cast_single_line,
    analyze_hexagram,
    interpret_hexagram,
    ai_interpret_hexagram,
)


def _init_session_state() -> None:
    """初始化会话状态。"""

    if "lines" not in st.session_state:
        st.session_state.lines: List[Line] = []


def _reset_hexagram() -> None:
    """重新起卦。"""

    st.session_state.lines = []


def _cast_next_line() -> None:
    """掷下一爻（自下而上）。"""

    if len(st.session_state.lines) < 6:
        st.session_state.lines.append(cast_single_line())


def _render_lines(lines: List[Line]) -> None:
    """
    图形化显示当前六爻（以及不足六爻时的已得爻）。
    按照“上爻在上、初爻在下”的排序展示。
    """

    if not lines:
        st.info("尚未起卦，请点击「掷下一爻」开始。")
        return

    st.subheader("当前卦象（自上而下展示）")
    for idx, line in reversed(list(enumerate(lines))):
        pos = idx + 1  # 爻位（1=初爻）
        label = line.yin_yang_label
        st.write(f"第 {pos} 爻：{line.display_symbol}  （{label}）")


def main() -> None:
    st.set_page_config(page_title="周易起卦与解卦", page_icon="✨", layout="centered")

    # 移除密码保护，直接进入应用
    if "authed" not in st.session_state:
        st.session_state.authed = True

    # 简单密码保护：仅输入正确密码才能继续使用
    # PASSWORD = "dokoei"
    # if "authed" not in st.session_state:
    #     st.session_state.authed = False

    # if not st.session_state.authed:
    #     st.title("周易起卦与解卦（受密码保护）")
    #     pwd = st.text_input("请输入访问密码：", type="password")
    #     if st.button("进入"):
    #         if pwd == PASSWORD:
    #             st.session_state.authed = True
    #             st.experimental_rerun()
    #         else:
    #             st.error("密码错误，请重试。")
    #     st.stop()

    st.title("周易起卦与解卦小工具")
    st.caption("使用三枚铜钱法模拟起卦，自动展示本卦、动爻与变卦的简要解读。")

    _init_session_state()

    with st.sidebar:
        st.header("操作")
        st.button("掷下一爻", on_click=_cast_next_line, type="primary")
        st.button("重新起卦", on_click=_reset_hexagram)

        if len(st.session_state.lines) < 6:
            st.markdown(
                f"当前已起 **{len(st.session_state.lines)}** 爻，还差 "
                f"**{6 - len(st.session_state.lines)}** 爻。"
            )
        else:
            st.markdown("六爻已成，可在主区域查看解卦结果。")

    lines: List[Line] = st.session_state.lines

    # 实时显示已得卦象
    _render_lines(lines)

    if len(lines) == 6:
        st.markdown("---")
        st.subheader("解卦结果（本卦 & 变卦）")

        result = analyze_hexagram(lines)
        interpretation = interpret_hexagram(result)

        col1, col2 = st.columns(2)

        # 本卦信息
        with col1:
            st.markdown("**本卦**")
            st.write(f"卦名：{interpretation['main_name']}")
            st.write(f"卦象：{interpretation['main_title']}")
            st.write("卦辞：")
            st.info(interpretation["main_judgement"])

        # 变卦信息（如有）
        with col2:
            if "changing_name" in interpretation:
                st.markdown("**变卦**")
                st.write(f"卦名：{interpretation['changing_name']}")
                st.write(f"卦象：{interpretation['changing_title']}")
                st.write("卦辞：")
                st.info(interpretation["changing_judgement"])
            else:
                st.markdown("**变卦**")
                st.info("本卦无动爻，因此不存在变卦。")

        # 动爻或爻辞详细列表
        st.markdown("### 爻辞解读")
        lines_explanation = interpretation["lines_explanation"]
        if not lines_explanation:
            st.write("（暂无爻辞信息）")
        else:
            for item in lines_explanation:
                pos = item["position"]
                text = item["text"]
                is_moving = item["is_moving"]
                tag = "【动爻】" if is_moving else "【参考】"
                st.markdown(f"- **第 {pos} 爻{tag}**：{text}")

        # -------------------------
        # AI 解卦（DeepSeek）
        # -------------------------
        st.markdown("---")
        st.subheader("AI 深度解卦（DeepSeek）")

        st.markdown(
            "请在下方简单描述你此次占问的主题，例如："
            "“目前的事业发展前景如何？”、“这段感情是否值得继续？” 等。"
        )

        user_question = st.text_area(
            "你的提问（必填）",
            placeholder="例如：我想问最近半年内的事业发展与职位晋升的可能性……",
        )

        if st.button(
            "向 DeepSeek 请求 AI 解卦",
            type="primary",
            disabled=not user_question.strip(),
        ):
            with st.spinner("正在向 DeepSeek 请求解卦，请稍候……"):
                ai_text = ai_interpret_hexagram(
                    result,
                    user_question,
                )
            st.markdown("#### DeepSeek 解卦说明")
            st.markdown(ai_text)


if __name__ == "__main__":
    main()
