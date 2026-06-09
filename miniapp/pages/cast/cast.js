const {
  castSingleLine,
  analyzeHexagram,
  interpretHexagram,
} = require("../../utils/yijing-logic");

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

function buildLinesReversed(lines) {
  return [...lines]
    .map((item, idx) => ({
      ...item,
      position: idx + 1,
    }))
    .reverse();
}

Page({
  data: {
    castMode: "single",
    casting: false,
    castingLineIndex: 0,
    castProgress: 0,
    castHint: "请选择起卦方式",
    castSlots: [],
    lines: [],
    linesReversed: [],
    bits: "",
    changingBits: "",
    interpretation: null,
  },

  onChooseMode(e) {
    this.setData({
      castMode: e.currentTarget.dataset.mode,
    });
  },

  onReset() {
    this.setData({
      casting: false,
      castingLineIndex: 0,
      castProgress: 0,
      castHint: "请选择起卦方式",
      castSlots: [],
      lines: [],
      linesReversed: [],
      bits: "",
      changingBits: "",
      interpretation: null,
    });
  },

  async onCast() {
    if (this.data.casting) {
      return;
    }

    this.setData({
      casting: true,
      castHint: "起卦中",
      castSlots: Array.from({ length: 6 }, () => null),
      castingLineIndex: 0,
      castProgress: 0,
      lines: [],
      linesReversed: [],
      bits: "",
      changingBits: "",
      interpretation: null,
    });

    const lines = [];
    if (this.data.castMode === "all") {
      for (let i = 0; i < 6; i += 1) {
        lines.push(castSingleLine());
      }
      await sleep(240);
      this.setData({
        castSlots: lines,
        castProgress: 100,
        castingLineIndex: 6,
      });
    } else {
      for (let i = 0; i < 6; i += 1) {
        this.setData({
          castingLineIndex: i + 1,
          castHint: `正在生成第 ${i + 1} 爻`,
        });
        await sleep(220);
        const line = castSingleLine();
        lines.push(line);
        this.setData({
          castSlots: lines.slice(),
          castProgress: Math.round(((i + 1) / 6) * 100),
        });
        await sleep(150);
      }
    }

    const result = analyzeHexagram(lines);
    const interpretation = interpretHexagram(result);

    this.setData({
      casting: false,
      castHint: "起卦完成",
      lines,
      linesReversed: buildLinesReversed(lines),
      bits: result.bits,
      changingBits: result.changingBits || "",
      interpretation,
      castProgress: 100,
      castingLineIndex: 6,
    });
  },

  onGoRead() {
    if (!this.data.lines.length) {
      wx.showToast({
        title: "请先起卦",
        icon: "none",
      });
      return;
    }

    wx.setStorageSync("yijing_cast_result", {
      lines: this.data.lines,
      bits: this.data.bits,
      changingBits: this.data.changingBits,
      interpretation: this.data.interpretation,
    });

    wx.navigateTo({
      url: "/pages/read/read",
    });
  },
});
