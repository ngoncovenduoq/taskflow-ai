"use strict";

// This frontend uses only the existing FastAPI endpoints, on the same origin.
// Chat messages are intentionally kept in memory, not localStorage.

const $ = (selector) => document.querySelector(selector);

const form = $("#chat-form");
const textarea = $("#message-input");
const sendButton = $("#send-button");
const resetButton = $("#reset-chat");
const messageList = $("#messages");
const chatScroll = $("#chat-scroll");
const welcome = $("#welcome");
const charCount = $("#char-count");
const formatter = new Intl.NumberFormat("vi-VN");
const usagePanel = $("#usage-panel");
const insightsToggle = $("#toggle-insights");
const insightsStorageKey = "taskflow:token-panel-open-v3";

let requestInFlight = false;

function readInsightsPreference() {
  // Persist the UI choice only; chat content and prompts are never stored.
  try {
    return window.localStorage.getItem(insightsStorageKey) === "true";
  } catch (_) {
    return false;
  }
}

function setInsightsVisible(visible, persist = false) {
  const show = visible === true;
  usagePanel.hidden = !show;
  insightsToggle.setAttribute("aria-expanded", String(show));
  insightsToggle.setAttribute("aria-label", show ? "Đóng thẻ token và chi phí" : "Mở thẻ token và chi phí");
  $("#toggle-insights-label").textContent = show ? "Đóng token" : "Token";

  if (persist) {
    try { window.localStorage.setItem(insightsStorageKey, String(show)); } catch (_) { /* Storage may be blocked. */ }
  }
}

function setText(selector, text) {
  const element = $(selector);
  if (element) element.textContent = String(text);
}

function numberOrDash(value) {
  return typeof value === "number" && Number.isFinite(value)
    ? formatter.format(value)
    : "—";
}

function costOrDash(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return "—";
  return "$" + value.toFixed(8);
}

function formatRoute(route) {
  const names = {
    general: "general",
    writing: "writing",
    research_write: "research + writing",
  };
  return typeof route === "string" ? (names[route] || route) : "—";
}

function scrollToLatest() {
  requestAnimationFrame(() => {
    chatScroll.scrollTop = chatScroll.scrollHeight;
  });
}

function createMessage(role, message, options = {}) {
  const row = document.createElement("article");
  row.className = `message is-${role}${options.error ? " is-error" : ""}${options.thinking ? " is-thinking" : ""}`;

  const avatar = document.createElement("div");
  avatar.className = "message-avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = role === "user" ? "Q" : "✦";

  const body = document.createElement("div");
  body.className = "message-body";

  const label = document.createElement("div");
  label.className = "message-label";
  label.textContent = role === "user" ? "Bạn" : "TaskFlow AI";

  const text = document.createElement("div");
  text.className = "message-text";
  // textContent prevents model/user text from being interpreted as HTML.
  text.textContent = message;

  body.append(label, text);
  if (options.meta) {
    const meta = document.createElement("div");
    meta.className = "message-meta";
    meta.textContent = options.meta;
    body.append(meta);
  }

  row.append(avatar, body);
  messageList.append(row);
  scrollToLatest();
  return { row, text };
}

function setLoading(busy) {
  requestInFlight = busy;
  sendButton.disabled = busy;
  resetButton.disabled = busy;
  setText("#send-button span", busy ? "Đợi..." : "Gửi");
  sendButton.setAttribute("aria-busy", String(busy));
}

function updateTextareaHeight() {
  textarea.style.height = "auto";
  textarea.style.height = Math.min(textarea.scrollHeight, 190) + "px";
  charCount.textContent = `${textarea.value.length} / 6000`;
}

function setPrompt(prompt) {
  if (requestInFlight) return;
  textarea.value = prompt;
  updateTextareaHeight();
  textarea.focus();
}

function renderModels(models) {
  const container = $("#model-list");
  container.replaceChildren();

  if (!Array.isArray(models) || models.length === 0) {
    const empty = document.createElement("div");
    empty.className = "empty-models";
    empty.textContent = "Chưa có dữ liệu sử dụng";
    container.append(empty);
    return;
  }

  for (const model of models) {
    const card = document.createElement("div");
    card.className = "model-item";

    const icon = document.createElement("span");
    icon.className = "model-orb";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = "✦";

    const text = document.createElement("span");
    text.className = "model-text";
    const title = document.createElement("strong");
    title.textContent = model && typeof model.model === "string" ? model.model : "Model không xác định";
    const detail = document.createElement("small");
    detail.textContent = `${numberOrDash(model?.total_tokens)} tokens · ${costOrDash(model?.estimated_cost_usd)}`;
    text.append(title, detail);
    card.append(icon, text);
    container.append(card);
  }
}

function renderUsage(usage) {
  const hasUsage = usage && usage.usage_available === true;
  setText("#last-tokens-overview", hasUsage ? numberOrDash(usage.total_tokens) : "—");
  setText("#total-tokens", hasUsage ? numberOrDash(usage.total_tokens) : "—");
  setText("#input-tokens", hasUsage ? numberOrDash(usage.input_tokens) : "—");
  setText("#output-tokens", hasUsage ? numberOrDash(usage.output_tokens) : "—");
  setText("#reasoning-tokens", hasUsage ? numberOrDash(usage.reasoning_tokens) : "—");
  setText("#duration-ms", typeof usage?.duration_ms === "number" ? `${(usage.duration_ms / 1000).toFixed(2)}s` : "—");
  setText("#estimated-cost", hasUsage ? costOrDash(usage.estimated_cost_usd) : "—");
  setText("#route-value", formatRoute(usage?.route));
  setText("#cost-note", usage?.estimated_cost_usd == null
    ? "Chưa có đủ dữ liệu giá để ước tính. Kiểm tra chi phí thực tế trên OpenRouter."
    : "Ước tính theo bảng giá tham khảo; số tiền OpenRouter thực tế tính có thể khác.");
  renderModels(hasUsage ? usage.by_model : []);
}

function addActivity(message, succeeded) {
  const container = $("#activity-feed");
  const empty = container.querySelector(".activity-empty");
  if (empty) empty.remove();

  const row = document.createElement("div");
  row.className = "activity-row";
  const marker = document.createElement("span");
  marker.className = succeeded ? "activity-marker success" : "activity-marker error";
  marker.textContent = succeeded ? "✓" : "!";
  const text = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = message.length > 55 ? `${message.slice(0, 55)}…` : message;
  const meta = document.createElement("small");
  meta.textContent = `${succeeded ? "Hoàn thành" : "Có lỗi"} · ${new Intl.DateTimeFormat("vi-VN", { hour: "2-digit", minute: "2-digit" }).format(new Date())}`;
  text.append(title, meta);
  row.append(marker, text);
  container.prepend(row);

  // Keep only the latest three activities in this tab.
  while (container.children.length > 3) container.lastElementChild.remove();
}

async function checkHealth() {
  const dot = $("#status-dot");
  const status = $("#api-status");
  dot.className = "status-dot is-checking";
  status.textContent = "Đang kiểm tra...";

  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 5000);
  try {
    const response = await fetch("/health", {
      signal: controller.signal,
      cache: "no-store",
    });
    if (!response.ok) throw new Error("Health check failed");
    const data = await response.json();
    if (!data || data.status !== "ok") throw new Error("Unexpected health response");
    dot.className = "status-dot is-online";
    status.textContent = "Đã kết nối";
  } catch (_) {
    dot.className = "status-dot is-offline";
    status.textContent = "Không kết nối";
  } finally {
    clearTimeout(timeout);
  }
}

function httpErrorMessage(status, data) {
  const messages = {
    400: "Yêu cầu chưa hợp lệ. Hãy kiểm tra nội dung và thử lại.",
    402: "Tài khoản mô hình có thể đã hết credit. Hãy kiểm tra OpenRouter.",
    413: "Nội dung quá dài. Hãy rút gọn yêu cầu.",
    422: "Yêu cầu không hợp lệ. Nội dung cần từ 1 đến 6000 ký tự.",
    429: "Dịch vụ đang giới hạn tốc độ. Hãy thử lại sau ít phút.",
    500: "Đã xảy ra lỗi máy chủ. Hãy kiểm tra Terminal backend.",
    503: "Dịch vụ AI đang tạm thời không khả dụng.",
    504: "Yêu cầu đã quá thời gian chờ. Bạn có thể thử lại.",
  };
  const detail = typeof data?.detail === "string" ? data.detail : "";
  return detail || messages[status] || `Yêu cầu thất bại (HTTP ${status}).`;
}

async function sendMessage(message) {
  if (requestInFlight) return;
  const trimmed = message.trim();
  if (!trimmed || trimmed.length > 6000) return;

  welcome.hidden = true;
  createMessage("user", trimmed);
  textarea.value = "";
  updateTextareaHeight();
  setLoading(true);
  const thinking = createMessage("assistant", "Đang xử lý yêu cầu...", { thinking: true });

  const controller = new AbortController();
  // Client-side timeout does not guarantee cancellation of upstream model work.
  const timeout = setTimeout(() => controller.abort(), 120000);
  try {
    const response = await fetch("/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: trimmed }),
      signal: controller.signal,
    });

    let data = null;
    try { data = await response.json(); } catch (_) { /* An error page may not be JSON. */ }
    if (!response.ok) throw new Error(httpErrorMessage(response.status, data));
    if (!data || typeof data.response !== "string") {
      throw new Error("Phản hồi từ server không đúng định dạng. Cần có trường 'response'.");
    }

    thinking.row.classList.remove("is-thinking");
    thinking.text.textContent = data.response.trim() || "AI không trả về nội dung văn bản.";
    renderUsage(data.usage);
    addActivity(trimmed, true);
  } catch (error) {
    thinking.row.classList.remove("is-thinking");
    thinking.row.classList.add("is-error");
    thinking.text.textContent = error?.name === "AbortError"
      ? "Giao diện đã ngừng chờ sau 120 giây. Yêu cầu trên server có thể vẫn đang xử lý và phát sinh chi phí."
      : error instanceof TypeError
        ? "Không kết nối được tới server. Hãy kiểm tra FastAPI đang chạy."
        : (error?.message || "Đã xảy ra lỗi không xác định.");
    addActivity(trimmed, false);
  } finally {
    clearTimeout(timeout);
    setLoading(false);
    scrollToLatest();
    textarea.focus();
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  void sendMessage(textarea.value);
});

textarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
    event.preventDefault();
    if (!requestInFlight) form.requestSubmit();
  }
});

textarea.addEventListener("input", updateTextareaHeight);

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    if (button.classList.contains("nav-item")) {
      document.querySelectorAll(".nav-item").forEach((item) => {
        item.classList.remove("is-active");
        item.removeAttribute("aria-current");
      });
      button.classList.add("is-active");
      button.setAttribute("aria-current", "page");
    }
    setPrompt(button.dataset.prompt || "");
  });
});

resetButton.addEventListener("click", () => {
  if (requestInFlight) return;
  messageList.replaceChildren();
  welcome.hidden = false;
  textarea.value = "";
  updateTextareaHeight();
  renderUsage(null);
  $("#activity-feed").replaceChildren();
  const emptyActivity = document.createElement("div");
  emptyActivity.className = "activity-empty";
  emptyActivity.textContent = "Chưa có yêu cầu nào trong phiên này.";
  $("#activity-feed").append(emptyActivity);
  textarea.focus();
});

$("#refresh-status").addEventListener("click", () => { void checkHealth(); });
insightsToggle.addEventListener("click", () => {
  setInsightsVisible(insightsToggle.getAttribute("aria-expanded") !== "true", true);
  if (insightsToggle.getAttribute("aria-expanded") === "true") {
    usagePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
  }
});

$("#nav-usage").addEventListener("click", () => {
  setInsightsVisible(true, true);
  usagePanel.scrollIntoView({ behavior: "smooth", block: "nearest" });
});

$("#quick-search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const input = $("#quick-search-input");
  if (!input.value.trim()) return;
  setPrompt(input.value.trim());
  input.value = "";
});

const greetingHour = new Date().getHours();
setText("#dashboard-greeting", `${greetingHour < 11 ? "Chào buổi sáng" : greetingHour < 18 ? "Chào buổi chiều" : "Chào buổi tối"}, Quân!`);
setText("#calendar-date", new Intl.DateTimeFormat("vi-VN", { weekday: "long", day: "2-digit", month: "2-digit", year: "numeric" }).format(new Date()));

setInsightsVisible(readInsightsPreference());
updateTextareaHeight();
void checkHealth();
