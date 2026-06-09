const { AI_FUNCTION_NAME } = require("../../utils/cloud-config");

Page({
  data: {
    lines: [],
    bits: "",
    changingBits: "",
    interpretation: null,
    userQuestion: "",
    aiLoading: false,
    aiText: "",
  },

  onShow() {
    const result = wx.getStorageSync("yijing_cast_result");
    if (!result) {
      return;
    }

    this.setData({
      lines: result.lines || [],
      bits: result.bits || "",
      changingBits: result.changingBits || "",
      interpretation: result.interpretation || null,
      aiText: "",
      aiLoading: false,
    });
  },

  onQuestionInput(e) {
    this.setData({
      userQuestion: e.detail.value,
    });
  },

  onAiExplain() {
    if (!this.data.userQuestion.trim()) {
      wx.showToast({
        title: "请先输入你的问题",
        icon: "none",
      });
      return;
    }

    if (!this.data.interpretation) {
      wx.showToast({
        title: "请先起卦",
        icon: "none",
      });
      return;
    }

    this.setData({
      aiLoading: true,
      aiText: "正在请求云端 AI 解卦，请稍候...",
    });

    const movingPositions = (this.data.interpretation.lines_explanation || [])
      .filter((item) => item.is_moving)
      .map((item) => item.position);

    wx.cloud.callFunction({
      name: AI_FUNCTION_NAME,
      data: {
        question: this.data.userQuestion.trim(),
        bits: this.data.bits,
        changingBits: this.data.changingBits || null,
        movingPositions,
        interpretation: this.data.interpretation,
      },
      success: ({ result }) => {
        if (!result || !result.ok) {
          this.setData({
            aiText: result?.message || "AI 解卦暂时不可用，请稍后再试。",
          });
          return;
        }

        this.setData({
          aiText: result.aiText,
        });
      },
      fail: () => {
        this.setData({
          aiText: "云函数调用失败，请确认云开发环境和函数已部署。",
        });
      },
      complete: () => {
        this.setData({
          aiLoading: false,
        });
      },
    });
  },
});
