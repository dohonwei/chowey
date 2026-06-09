const state = {
  lines: [],
  interpretation: null,
};

const castButton = document.getElementById("castButton");
const resetButton = document.getElementById("resetButton");
const aiButton = document.getElementById("aiButton");
const questionInput = document.getElementById("questionInput");
const linesContainer = document.getElementById("linesContainer");
const readingContainer = document.getElementById("readingContainer");
const aiContainer = document.getElementById("aiContainer");
const statusBadge = document.getElementById("statusBadge");

function setStatus(text) {
  statusBadge.textContent = text;
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

function renderLines() {
  if (!state.lines.length) {
    linesContainer.className = "lines-empty";
    linesContainer.textContent = "点击上方按钮后，这里会显示六爻。";
    return;
  }

  const reversed = [...state.lines]
    .map((line, index) => ({ ...line, position: index + 1 }))
    .reverse();

  linesContainer.className = "";
  linesContainer.innerHTML = reversed
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
}

function renderInterpretation() {
  const interpretation = state.interpretation;
  if (!interpretation) {
    readingContainer.className = "reading-empty";
    readingContainer.textContent = "起卦完成后，这里会展示本卦、变卦和爻辞。";
    return;
  }

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

  readingContainer.className = "";
  readingContainer.innerHTML = `
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
  `;
}

function resetAll() {
  state.lines = [];
  state.interpretation = null;
  questionInput.value = "";
  aiContainer.className = "ai-empty";
  aiContainer.textContent = "AI 结果会显示在这里。";
  setStatus("等待起卦");
  renderLines();
  renderInterpretation();
}

async function castHexagram() {
  castButton.disabled = true;
  setStatus("正在起卦");
  aiContainer.className = "ai-empty";
  aiContainer.textContent = "AI 结果会显示在这里。";

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
    linesContainer.textContent = `起卦失败：${error.message}`;
  } finally {
    castButton.disabled = false;
  }
}

async function requestAiReading() {
  const question = questionInput.value.trim();
  if (!state.lines.length) {
    aiContainer.className = "ai-empty";
    aiContainer.textContent = "请先起卦。";
    return;
  }
  if (!question) {
    aiContainer.className = "ai-empty";
    aiContainer.textContent = "请先输入你的问题。";
    return;
  }

  aiButton.disabled = true;
  aiContainer.className = "ai-result";
  aiContainer.textContent = "正在请求 AI 解卦，请稍候...";

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
    aiContainer.className = "ai-result";
    aiContainer.textContent = `AI 解卦失败：${error.message}`;
  } finally {
    aiButton.disabled = false;
  }
}

castButton.addEventListener("click", castHexagram);
resetButton.addEventListener("click", resetAll);
aiButton.addEventListener("click", requestAiReading);

resetAll();
