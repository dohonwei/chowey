const cloud = require("wx-server-sdk");
const https = require("https");

cloud.init({ env: cloud.DYNAMIC_CURRENT_ENV });

const LLM_BASE_URL = "https://wgooold.cn";
const LLM_MODEL = "Qwen3.6-27B";
const LLM_TIMEOUT = 120000;

function stripReasoningContent(text) {
  let cleaned = String(text || "").trim();

  if (cleaned.includes("</think>")) {
    cleaned = cleaned.split("</think>").pop().trim();
  }

  cleaned = cleaned.replace(/<think>[\s\S]*?<\/think>/gi, "").trim();

  const prefixes = [
    "Here's a thinking process:",
    "Thinking Process:",
    "Reasoning:",
    "1. **Analyze User Input:**",
    "1. **Analyze",
    "1. Analyze User Input:",
    "1. Analyze",
  ];

  for (const prefix of prefixes) {
    if (!cleaned.startsWith(prefix)) {
      continue;
    }

    const markers = ["\n\n收到", "\n\n本次", "\n\n根据", "\n\n1. ", "\n\n**"];
    for (const marker of markers) {
      const index = cleaned.indexOf(marker);
      if (index !== -1) {
        return cleaned.slice(index + 2).trim();
      }
    }
  }

  return cleaned;
}

function fallbackStripReasoning(text) {
  let cleaned = stripReasoningContent(text);

  const preferredStart = cleaned.indexOf("解读如下");
  if (preferredStart !== -1) {
    cleaned = cleaned.slice(preferredStart).trim();
  }

  const paragraphMatch = cleaned.match(/\*?\(Paragraph\s+1:[\s\S]*$/i);
  if (paragraphMatch) {
    cleaned = paragraphMatch[0];
  }

  cleaned = cleaned
    .replace(/\*?\(Paragraph\s+\d+:[^)]+\)\*?/gi, "")
    .replace(/^\s*\d+\.\s+\*\*(Draft|Check|Analyze|Identify|Formulate|Constraint)[\s\S]*?(?=\n\n|\r\n\r\n|$)/gim, "")
    .trim();

  const finalMarkers = [
    "最终解读",
    "解读如下",
    "结论",
    "建议",
    "简要解读",
    "以下是",
  ];

  for (const marker of finalMarkers) {
    const index = cleaned.indexOf(marker);
    if (index > 0) {
      cleaned = cleaned.slice(index).trim();
      break;
    }
  }

  cleaned = cleaned.replace(/^#+\s*/gm, "");
  cleaned = cleaned.replace(/^\s*\d+\.\s+\*\*Structure Output[\s\S]*?(?=解读如下[:：]?)/i, "");
  cleaned = cleaned.replace(/^\s*\d+\.\s+\*\*(Analyze|Identify|Formulate|Check|Constraint)[\s\S]*$/i, "").trim();

  const blocks = cleaned
    .split(/\n\s*\n/)
    .map((block) => block.trim())
    .filter(Boolean);

  const chineseBlocks = blocks.filter((block) => {
    const chineseCount = (block.match(/[\u4e00-\u9fff]/g) || []).length;
    const englishSignal = /\b(Analyze|Draft|Check|Constraint|Question|Hexagram|Weather Context|Conclusion|Paragraph)\b/i.test(block);
    return chineseCount >= 12 && !englishSignal;
  });

  if (chineseBlocks.length > 0) {
    cleaned = chineseBlocks.join("\n\n").trim();
  }

  return cleaned;
}

function buildYiContext(event) {
  const lines = [];
  lines.push(`本卦卦名：${event.interpretation.main_name}`);
  lines.push(`本卦卦象说明：${event.interpretation.main_title}`);
  lines.push(`本卦二进制（自下而上，1=阳，0=阴）：${event.bits}`);
  lines.push(`本卦卦辞（简化版）：${event.interpretation.main_judgement}`);

  if (event.movingPositions.length > 0) {
    lines.push(`动爻位置（1=初爻，6=上爻）：${event.movingPositions.join(", ")}`);
    event.interpretation.lines_explanation.forEach((item) => {
      if (item.is_moving) {
        lines.push(`本卦第 ${item.position} 爻爻辞：${item.text}`);
      }
    });
  } else {
    lines.push("本卦无动爻，主要参考整体卦辞。");
  }

  if (event.interpretation.changing_name && event.changingBits) {
    lines.push(`变卦卦名：${event.interpretation.changing_name}`);
    lines.push(`变卦卦象说明：${event.interpretation.changing_title}`);
    lines.push(`变卦二进制（自下而上，1=阳，0=阴）：${event.changingBits}`);
    lines.push(`变卦卦辞（简化版）：${event.interpretation.changing_judgement}`);
  }

  return lines.join("\n");
}

function callModel(payload, apiKey) {
  return new Promise((resolve, reject) => {
    const body = JSON.stringify(payload);
    const request = https.request(
      `${LLM_BASE_URL}/v1/chat/completions`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
          "Content-Length": Buffer.byteLength(body),
        },
        timeout: LLM_TIMEOUT,
      },
      (response) => {
        let raw = "";

        response.on("data", (chunk) => {
          raw += chunk;
        });

        response.on("end", () => {
          if (response.statusCode !== 200) {
            reject(
              new Error(
                `模型接口异常：HTTP ${response.statusCode} ${raw.slice(0, 300)}`
              )
            );
            return;
          }

          try {
            const parsed = JSON.parse(raw);
            resolve(parsed);
          } catch (error) {
            reject(new Error(`模型返回了非 JSON 内容：${raw.slice(0, 300)}`));
          }
        });
      }
    );

    request.on("timeout", () => {
      request.destroy(new Error("模型调用超时，请稍后再试。"));
    });

    request.on("error", (error) => {
      reject(error);
    });

    request.write(body);
    request.end();
  });
}

exports.main = async (event) => {
  if (event && event.testOnly) {
    return {
      ok: true,
      aiText: "云函数已连通。",
    };
  }

  const apiKey = process.env.LLM_API_KEY;

  if (!apiKey) {
    return {
      ok: false,
      message: "云函数未配置 LLM_API_KEY 环境变量。",
    };
  }

  if (!event || !event.interpretation || !event.bits || !event.question) {
    return {
      ok: false,
      message: "云函数收到的解卦参数不完整。",
    };
  }

  const yiContext = buildYiContext(event);
  const payload = {
    model: LLM_MODEL,
    temperature: 0.6,
    max_tokens: 900,
    messages: [
      {
        role: "system",
        content:
          "你是一位精通《周易》的现代解卦专家。必须直接输出中文最终解读。禁止输出英文分析、思维链、推理过程、Analyze User Input、Constraint、Draft、Check 等内容。语言平和、简洁、可执行。",
      },
      {
        role: "user",
        content:
          `下面是本次起卦的结构化信息：\n\n${yiContext}\n\n` +
          `用户问题：${event.question}\n\n` +
          "请从整体卦象、动爻与变卦关系出发，给出清晰的趋势判断和建议，控制在 3 到 5 段。第一行必须是“解读如下：”。",
      },
    ],
  };

  try {
    const result = await callModel(payload, apiKey);
    const content = fallbackStripReasoning(
      result?.choices?.[0]?.message?.content || ""
    );

    if (!content) {
      return {
        ok: false,
        message: "模型调用成功，但未返回可用内容。",
      };
    }

    return {
      ok: true,
      aiText: content,
    };
  } catch (error) {
    return {
      ok: false,
      message: error.message || "AI 解卦失败。",
    };
  }
};
