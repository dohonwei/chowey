const state = {
  lines: [],
  interpretation: null,
  mode: "direct",
  coinDraft: [],
  manualValues: [7, 7, 7, 7, 7, 7],
};

const castButton = document.getElementById("castButton");
const coinCastButton = document.getElementById("coinCastButton");
const coinResetButton = document.getElementById("coinResetButton");
const manualAnalyzeButton = document.getElementById("manualAnalyzeButton");
const resetButton = document.getElementById("resetButton");
const aiButton = document.getElementById("aiButton");
const questionInput = document.getElementById("questionInput");
const linesContainer = document.getElementById("linesContainer");
const aiContainer = document.getElementById("aiContainer");
const statusBadge = document.getElementById("statusBadge");
const modeBadge = document.getElementById("modeBadge");
const coinProgressText = document.getElementById("coinProgressText");
const modeButtons = {
  direct: document.getElementById("modeDirect"),
  coins: document.getElementById("modeCoins"),
  manual: document.getElementById("modeManual"),
};
const modePanels = {
  direct: document.getElementById("directPanel"),
  coins: document.getElementById("coinsPanel"),
  manual: document.getElementById("manualPanel"),
};
const manualSelects = Array.from(document.querySelectorAll(".manual-select"));

const modeLabels = {
  direct: "直接起卦",
  coins: "铜钱起卦",
  manual: "手动输入",
};

function setStatus(text) {
  statusBadge.textContent = text;
  statusBadge.classList.remove("is-busy", "is-error");
  if (text.includes("正在")) {
    statusBadge.classList.add("is-busy");
  }
  if (text.includes("失败")) {
    statusBadge.classList.add("is-error");
  }
}

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, (char) => {
    const entities = {
      "&": "&amp;",
      "<": "&lt;",
      ">": "&gt;",
      '"': "&quot;",
      "'": "&#39;",
    };
    return entities[char];
  });
}

function valueToLineMeta(value) {
  const lineValue = Number(value);
  const isYang = lineValue === 7 || lineValue === 9;
  const isMoving = lineValue === 6 || lineValue === 9;
  return {
    value: lineValue,
    display_symbol: isYang ? "———" : "— —",
    yin_yang_label:
      lineValue === 6
        ? "老阴（动爻）"
        : lineValue === 7
          ? "少阳（静爻）"
          : lineValue === 8
            ? "少阴（静爻）"
            : "老阳（动爻）",
    is_moving: isMoving,
  };
}

function renderCoinDraft() {
  if (!state.coinDraft.length) {
    coinProgressText.textContent = "当前还未开始，请点击起第一爻。";
    if (!state.lines.length) {
      renderLines();
    }
    return;
  }

  const reversed = [...state.coinDraft]
    .map((value, index) => ({ ...valueToLineMeta(value), position: index + 1 }))
    .reverse();

  const draftCards = reversed
    .map(
      (line) => `
        <div class="line-card">
          <div class="line-main">
            <span class="line-position">第 ${line.position} 爻</span>
            <span class="line-symbol">${line.display_symbol}</span>
            <span class="line-label">${line.yin_yang_label}</span>
          </div>
          ${line.is_moving ? '<span class="moving-mark">动爻</span>' : ""}
        </div>
      `
    )
    .join("");

  if (state.coinDraft.length < 6) {
    coinProgressText.textContent = `已完成 ${state.coinDraft.length} / 6 爻，请继续点击起第 ${state.coinDraft.length + 1} 爻。`;
  } else {
    coinProgressText.textContent = "六爻已齐，正在生成卦象结果。";
  }

  linesContainer.className = "casting-result";
  linesContainer.innerHTML = `
    <div class="casting-result-grid">
      <div class="casting-result-column">
        <div class="casting-subtitle">铜钱起卦进度</div>
        <div class="line-stack">${draftCards}</div>
      </div>
      <div class="casting-result-column">
        <div class="reading-empty-inline">铜钱起卦进行中。累计满六爻后，会在这里自动展示本卦、变卦与动爻说明。</div>
      </div>
    </div>
  `;
}

function setMode(mode) {
  state.mode = mode;
  modeBadge.textContent = `当前：${modeLabels[mode]}`;

  Object.entries(modeButtons).forEach(([key, button]) => {
    button.classList.toggle("is-active", key === mode);
  });

  Object.entries(modePanels).forEach(([key, panel]) => {
    panel.classList.toggle("is-active", key === mode);
  });
}

function generateRandomLineValue() {
  const coins = Array.from({ length: 3 }, () => (Math.random() < 0.5 ? 2 : 3));
  return coins[0] + coins[1] + coins[2];
}

async function analyzeSelectedLines(values) {
  const response = await fetch("/analyze", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ lines: values.map(Number) }),
  });

  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || `HTTP ${response.status}`);
  }

  state.lines = data.lines || [];
  state.interpretation = data.interpretation || null;
  renderLines();
  renderInterpretation();
}

function renderLines() {
  if (!state.lines.length) {
    linesContainer.className = "lines-empty";
    linesContainer.textContent = "完成起卦后，这里会显示六爻、本卦、变卦与动爻说明。";
    return;
  }

  const reversed = [...state.lines]
    .map((line, index) => ({ ...line, position: index + 1 }))
    .reverse();

  const lineCards = reversed
    .map(
      (line) => `
        <div class="line-card">
          <div class="line-main">
            <span class="line-position">第 ${line.position} 爻</span>
            <span class="line-symbol">${escapeHtml(line.display_symbol)}</span>
            <span class="line-label">${escapeHtml(line.yin_yang_label)}</span>
          </div>
          ${line.is_moving ? '<span class="moving-mark">动爻</span>' : ""}
        </div>
      `
    )
    .join("");

  const interpretation = state.interpretation;
  let summaryBlock = "";

  if (interpretation) {
    const changingBlock = interpretation.changing_name
      ? `
        <div class="meta-block">
          <span class="meta-title">变卦</span>
          <div class="meta-text">卦名：${escapeHtml(interpretation.changing_name)}</div>
          <div class="meta-text">卦象：${escapeHtml(interpretation.changing_title)}</div>
          <div class="meta-text">卦辞：${escapeHtml(interpretation.changing_judgement)}</div>
        </div>
      `
      : `
        <div class="meta-block">
          <span class="meta-title">变卦</span>
          <div class="meta-text">本卦无动爻，因此不存在变卦。</div>
        </div>
      `;

    const explainList = interpretation.lines_explanation
      .map(
        (item) => `
          <div class="explain-item">
            <div class="explain-title">
              第 ${item.position} 爻 ${item.is_moving ? "· 动爻" : "· 参考"}
            </div>
            <div class="explain-text">${escapeHtml(item.text)}</div>
          </div>
        `
      )
      .join("");

    summaryBlock = `
      <div class="casting-reading">
        <div class="casting-subtitle">解卦说明</div>
        <div class="meta-row">
          <div class="meta-block">
            <span class="meta-title">本卦</span>
            <div class="meta-text">卦名：${escapeHtml(interpretation.main_name)}</div>
            <div class="meta-text">卦象：${escapeHtml(interpretation.main_title)}</div>
            <div class="meta-text">卦辞：${escapeHtml(interpretation.main_judgement)}</div>
          </div>
          ${changingBlock}
        </div>
        <div class="explain-list">${explainList}</div>
      </div>
    `;
  }

  linesContainer.className = "casting-result";
  linesContainer.innerHTML = `
    <div class="casting-result-grid">
      <div class="casting-result-column">
        <div class="casting-subtitle">六爻排盘</div>
        <div class="line-stack">${lineCards}</div>
      </div>
      <div class="casting-result-column">
        ${summaryBlock || '<div class="reading-empty-inline">起卦完成后，这里会展示本卦、变卦与动爻说明。</div>'}
      </div>
    </div>
  `;
}

function renderInterpretation() {
  renderLines();
}

function resetAll() {
  state.lines = [];
  state.interpretation = null;
  state.coinDraft = [];
  state.manualValues = [7, 7, 7, 7, 7, 7];
  questionInput.value = "";
  manualSelects.forEach((select, index) => {
    select.value = String(state.manualValues[index]);
  });
  aiContainer.className = "ai-empty";
  aiContainer.textContent = "输入问题后，AI 解读会显示在这里。";
  setStatus("等待起卦");
  renderLines();
  renderCoinDraft();
  coinCastButton.disabled = false;
}

async function castHexagram() {
  castButton.disabled = true;
  setStatus("正在起卦");
  aiContainer.className = "ai-empty";
  aiContainer.textContent = "输入问题后，AI 解读会显示在这里。";

  try {
    const response = await fetch("/cast", { method: "POST" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const data = await response.json();
    state.lines = data.lines || [];
    state.interpretation = data.interpretation || null;
    setStatus("起卦完成");
    renderLines();
    renderInterpretation();
  } catch (error) {
    setStatus("起卦失败");
    linesContainer.className = "lines-empty";
    linesContainer.textContent = `起卦失败，请稍后重试。${error.message ? `（${error.message}）` : ""}`;
  } finally {
    castButton.disabled = false;
  }
}

async function castByCoins() {
  if (state.coinDraft.length >= 6) {
    return;
  }

  state.coinDraft.push(generateRandomLineValue());
  renderCoinDraft();

  if (state.coinDraft.length < 6) {
    return;
  }

  coinCastButton.disabled = true;
  setStatus("正在起卦");
  try {
    await analyzeSelectedLines(state.coinDraft);
    setStatus("起卦完成");
  } catch (error) {
    setStatus("起卦失败");
    linesContainer.className = "lines-empty";
    linesContainer.textContent = `铜钱起卦失败，请稍后重试。${error.message ? `（${error.message}）` : ""}`;
  } finally {
    coinCastButton.disabled = false;
  }
}

function resetCoinDraft() {
  state.coinDraft = [];
  renderCoinDraft();
  if (!state.lines.length) {
    setStatus("等待起卦");
  }
}

async function castByManualInput() {
  manualAnalyzeButton.disabled = true;
  setStatus("正在起卦");

  try {
    await analyzeSelectedLines(state.manualValues);
    setStatus("起卦完成");
  } catch (error) {
    setStatus("起卦失败");
    linesContainer.className = "lines-empty";
    linesContainer.textContent = `手动起卦失败，请稍后重试。${error.message ? `（${error.message}）` : ""}`;
  } finally {
    manualAnalyzeButton.disabled = false;
  }
}

async function requestAiReading() {
  const question = questionInput.value.trim();
  if (!state.lines.length) {
    aiContainer.className = "ai-empty";
    aiContainer.textContent = "请先起卦，再进行解读。";
    return;
  }
  if (!question) {
    aiContainer.className = "ai-empty";
    aiContainer.textContent = "请先输入你想咨询的问题。";
    return;
  }

  aiButton.disabled = true;
  aiContainer.className = "ai-result";
  aiContainer.textContent = "正在生成解读，请稍候...";

  try {
    const response = await fetch("/ai", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        lines: state.lines.map((line) => line.value),
        question,
      }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.detail || `HTTP ${response.status}`);
    }

    aiContainer.className = "ai-result";
    aiContainer.textContent = data.ai_text || "未返回 AI 内容。";
  } catch (error) {
    aiContainer.className = "ai-result is-error";
    aiContainer.textContent = error.message || "AI 服务暂时不可用，请稍后重试。";
  } finally {
    aiButton.disabled = false;
  }
}

Object.entries(modeButtons).forEach(([mode, button]) => {
  button.addEventListener("click", () => setMode(mode));
});

manualSelects.forEach((select) => {
  select.addEventListener("change", (event) => {
    const index = Number(event.target.dataset.lineIndex);
    state.manualValues[index] = Number(event.target.value);
  });
});

castButton.addEventListener("click", castHexagram);
coinCastButton.addEventListener("click", castByCoins);
coinResetButton.addEventListener("click", resetCoinDraft);
manualAnalyzeButton.addEventListener("click", castByManualInput);
resetButton.addEventListener("click", resetAll);
aiButton.addEventListener("click", requestAiReading);

setMode("direct");
resetAll();
