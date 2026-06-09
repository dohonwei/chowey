const TRIGRAMS_BY_BITS = {
  "111": { name: "乾", meaning: "天", bits: "111" },
  "110": { name: "兑", meaning: "泽", bits: "110" },
  "101": { name: "离", meaning: "火", bits: "101" },
  "100": { name: "震", meaning: "雷", bits: "100" },
  "011": { name: "巽", meaning: "风", bits: "011" },
  "010": { name: "坎", meaning: "水", bits: "010" },
  "001": { name: "艮", meaning: "山", bits: "001" },
  "000": { name: "坤", meaning: "地", bits: "000" },
};

const HEXAGRAM_NAMES = {
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
};

function generateHexagramName(upper, lower) {
  const lookupKey = upper.bits + lower.bits;
  const fullName = HEXAGRAM_NAMES[lookupKey];

  if (!fullName) {
    return `${upper.name}${lower.name}卦`;
  }

  if (fullName.includes("为")) {
    return `${fullName.split("为")[0]}卦`;
  }

  if (fullName.length === 3) {
    return `${fullName.slice(-1)}卦`;
  }

  return `${fullName.slice(-2)}卦`;
}

function generateHexagramTitle(upper, lower) {
  return `${upper.meaning}在上，${lower.meaning}在下`;
}

function generateHexagramJudgement(upper, lower) {
  return `${upper.name}${lower.name}卦：上为${upper.meaning}，下为${lower.meaning}，象征着两种力量的互动与平衡，可据此联想到现实中的局势变化。`;
}

function generateLineTexts(upper, lower) {
  const base = `${upper.name}${lower.name}卦`;
  const meanings = {
    1: "初爻，多为事情萌芽、起步阶段，可顺势而为。",
    2: "二爻，代表内在调整与稳定基础，宜沉稳审慎。",
    3: "三爻，象征矛盾与摇摆，进退之间需权衡利弊。",
    4: "四爻，多与对外拓展、远景规划有关，需看清方向。",
    5: "五爻，常为卦中主爻，意味着关键人物或关键决策。",
    6: "上爻，事情发展至极处，有圆满也有转折之机。",
  };

  return {
    1: `${base}第1爻：${meanings[1]}`,
    2: `${base}第2爻：${meanings[2]}`,
    3: `${base}第3爻：${meanings[3]}`,
    4: `${base}第4爻：${meanings[4]}`,
    5: `${base}第5爻：${meanings[5]}`,
    6: `${base}第6爻：${meanings[6]}`,
  };
}

function getHexagramByBits(bits) {
  if (!/^[01]{6}$/.test(bits)) {
    throw new Error("bits 必须是 6 位 0/1 字符串。");
  }

  const lowerBits = bits.slice(0, 3);
  const upperBits = bits.slice(3);
  const lower = TRIGRAMS_BY_BITS[lowerBits];
  const upper = TRIGRAMS_BY_BITS[upperBits];

  if (!lower || !upper) {
    throw new Error("未找到对应卦象。");
  }

  return {
    upperTrigram: upper,
    lowerTrigram: lower,
    name: generateHexagramName(upper, lower),
    title: generateHexagramTitle(upper, lower),
    judgement: generateHexagramJudgement(upper, lower),
    lineTexts: generateLineTexts(upper, lower),
  };
}

module.exports = {
  getHexagramByBits,
};
