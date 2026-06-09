const { getHexagramByBits } = require("./yijing-data");

function createLine(value) {
  return {
    value,
    is_yang: value === 7 || value === 9,
    is_moving: value === 6 || value === 9,
    display_symbol: value === 7 || value === 9 ? "———" : "— —",
    yin_yang_label:
      value === 6
        ? "老阴（动爻）"
        : value === 7
          ? "少阳（静爻）"
          : value === 8
            ? "少阴（静爻）"
            : "老阳（动爻）",
  };
}

function castSingleLine() {
  const coins = Array.from({ length: 3 }, () => (Math.random() < 0.5 ? 2 : 3));
  const total = coins.reduce((sum, item) => sum + item, 0);
  return createLine(Math.min(9, Math.max(6, total)));
}

function transformLine(line) {
  if (line.value === 6) {
    return createLine(7);
  }
  if (line.value === 9) {
    return createLine(8);
  }
  return createLine(line.value);
}

function linesToBits(lines) {
  return lines.map((line) => (line.is_yang ? "1" : "0")).join("");
}

function analyzeHexagram(lines) {
  const bits = linesToBits(lines);
  const mainHexagram = getHexagramByBits(bits);
  const movingLineIndices = lines
    .map((line, index) => (line.is_moving ? index : -1))
    .filter((index) => index !== -1);

  let changingHexagram = null;
  let changingBits = null;

  if (movingLineIndices.length > 0) {
    const changedLines = lines.map(transformLine);
    changingBits = linesToBits(changedLines);
    changingHexagram = getHexagramByBits(changingBits);
  }

  return {
    bits,
    mainHexagram,
    changingHexagram,
    movingLineIndices,
    changingBits,
  };
}

function interpretHexagram(result) {
  const linesExplanation = [];

  if (result.movingLineIndices.length === 0) {
    for (let index = 0; index < 6; index += 1) {
      const position = index + 1;
      linesExplanation.push({
        index,
        position,
        is_moving: false,
        is_used: false,
        text:
          result.mainHexagram.lineTexts[position] ||
          `${result.mainHexagram.name}第${position}爻：可结合卦辞灵活理解。`,
      });
    }
  } else {
    result.movingLineIndices.forEach((index) => {
      const position = index + 1;
      linesExplanation.push({
        index,
        position,
        is_moving: true,
        is_used: true,
        text:
          result.mainHexagram.lineTexts[position] ||
          `${result.mainHexagram.name}第${position}爻：动而有变，需权衡利弊。`,
      });
    });
  }

  const interpretation = {
    main_name: result.mainHexagram.name,
    main_title: result.mainHexagram.title,
    main_judgement: result.mainHexagram.judgement,
    lines_explanation: linesExplanation,
  };

  if (result.changingHexagram) {
    interpretation.changing_name = result.changingHexagram.name;
    interpretation.changing_title = result.changingHexagram.title;
    interpretation.changing_judgement = result.changingHexagram.judgement;
  }

  return interpretation;
}

module.exports = {
  castSingleLine,
  analyzeHexagram,
  interpretHexagram,
};
