/**
 * SOFA Ana Uygulama Mantığı
 * Sekme geçişleri + Chat / Media / Privacy modülleriyle API iletişimi.
 */

// ---------- Sekme (Tab) Yönetimi ----------
const tabButtons = document.querySelectorAll(".nav-btn");
const panels = {
  chat: document.getElementById("panel-chat"),
  media: document.getElementById("panel-media"),
  music: document.getElementById("panel-music"),
  privacy: document.getElementById("panel-privacy"),
};

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");

    Object.entries(panels).forEach(([key, panel]) => {
      if (!panel) return;
      const isActive = key === btn.dataset.tab;
      panel.hidden = !isActive;
      panel.classList.toggle("active", isActive);
    });

    if (btn.dataset.tab === "privacy") {
      loadPrivacyStatus();
    }
  });
});

// ---------- Chat Modülü ----------
const chatWindow = document.getElementById("chat-window");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const chatError = document.getElementById("chat-error");

const chatHistory = [];

function appendMessage(role, text) {
  const el = document.createElement("div");
  el.className = `chat-msg ${role}`;
  el.textContent = text;
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return el;
}

function showTypingIndicator() {
  const el = document.createElement("div");
  el.className = "chat-msg assistant typing-indicator";
  el.innerHTML = '<span class="dot"></span><span class="dot"></span><span class="dot"></span>';
  chatWindow.appendChild(el);
  chatWindow.scrollTop = chatWindow.scrollHeight;
  return el;
}

chatForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const text = chatInput.value.trim();
  if (!text) return;

  chatError.hidden = true;
  appendMessage("user", text);
  chatHistory.push({ role: "user", content: text });
  chatInput.value = "";
  chatInput.disabled = true;

  const typingEl = showTypingIndicator();

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ messages: chatHistory }),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Sunucu hatası (HTTP ${response.status})`);
    }

    const data = await response.json();
    typingEl.remove();
    appendMessage("assistant", data.reply);
    chatHistory.push({ role: "assistant", content: data.reply });
  } catch (err) {
    typingEl.remove();
    chatError.textContent = `Hata: ${err.message}`;
    chatError.hidden = false;
    appendMessage("system", "Yanıt alınamadı, lütfen tekrar deneyin.");
  } finally {
    chatInput.disabled = false;
    chatInput.focus();
  }
});

// ---------- Media Modülü ----------
const mediaPromptInput = document.getElementById("media-prompt");
const mediaGenerateBtn = document.getElementById("media-generate-btn");
const mediaGenerateResult = document.getElementById("media-generate-result");
const mediaError = document.getElementById("media-error");

mediaGenerateBtn.addEventListener("click", async () => {
  const prompt = mediaPromptInput.value.trim();
  if (!prompt) return;

  mediaError.hidden = true;
  mediaGenerateBtn.disabled = true;
  mediaGenerateResult.textContent = "Üretiliyor...";

  try {
    const response = await fetch("/api/media/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Sunucu hatası (HTTP ${response.status})`);
    }

    const data = await response.json();
    mediaGenerateResult.innerHTML = "";
    const img = document.createElement("img");
    img.src = `data:image/png;base64,${data.image_base64}`;
    mediaGenerateResult.appendChild(img);
  } catch (err) {
    mediaError.textContent = `Hata: ${err.message}`;
    mediaError.hidden = false;
    mediaGenerateResult.textContent = "";
  } finally {
    mediaGenerateBtn.disabled = false;
  }
});

const watermarkFileInput = document.getElementById("watermark-file");
const watermarkRemoveBtn = document.getElementById("watermark-remove-btn");
const watermarkResult = document.getElementById("watermark-result");

watermarkRemoveBtn.addEventListener("click", async () => {
  const file = watermarkFileInput.files[0];
  if (!file) {
    mediaError.textContent = "Lütfen önce bir görsel seçin.";
    mediaError.hidden = false;
    return;
  }

  mediaError.hidden = true;
  watermarkRemoveBtn.disabled = true;
  watermarkResult.textContent = "İşleniyor...";

  try {
    const formData = new FormData();
    formData.append("file", file);

    const response = await fetch("/api/media/watermark/remove", {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Sunucu hatası (HTTP ${response.status})`);
    }

    const data = await response.json();
    watermarkResult.innerHTML = "";
    const img = document.createElement("img");
    img.src = `data:image/png;base64,${data.image_base64}`;
    watermarkResult.appendChild(img);
  } catch (err) {
    mediaError.textContent = `Hata: ${err.message}`;
    mediaError.hidden = false;
    watermarkResult.textContent = "";
  } finally {
    watermarkRemoveBtn.disabled = false;
  }
});

// ---------- Music Creator Modülü ----------
const musicPromptInput = document.getElementById("music-prompt");
const musicGenerateBtn = document.getElementById("music-generate-btn");
const musicResult = document.getElementById("music-result");
const musicError = document.getElementById("music-error");

musicGenerateBtn.addEventListener("click", async () => {
  const prompt = musicPromptInput.value.trim();
  if (!prompt) return;

  musicError.hidden = true;
  musicGenerateBtn.disabled = true;
  musicResult.textContent = "Üretiliyor...";

  try {
    const response = await fetch("/api/music/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt }),
    });

    if (!response.ok) {
      const detail = await response.json().catch(() => ({}));
      throw new Error(detail.detail || `Sunucu hatası (HTTP ${response.status})`);
    }

    const data = await response.json();
    musicResult.innerHTML = "";
    const note = document.createElement("p");
    note.className = "panel-hint";
    note.textContent = data.message;
    musicResult.appendChild(note);
    const audio = document.createElement("audio");
    audio.controls = true;
    const mime = data.audio_format === "wav" ? "audio/wav" : "audio/mpeg";
    audio.src = `data:${mime};base64,${data.audio_base64}`;
    musicResult.appendChild(audio);
  } catch (err) {
    musicError.textContent = `Hata: ${err.message}`;
    musicError.hidden = false;
    musicResult.textContent = "";
  } finally {
    musicGenerateBtn.disabled = false;
  }
});

// ---------- Privacy Modülü ----------
const privacyStatusText = document.getElementById("privacy-status-text");
const privacyWipeBtn = document.getElementById("privacy-wipe-btn");
const privacyWipeResult = document.getElementById("privacy-wipe-result");

async function loadPrivacyStatus() {
  try {
    const response = await fetch("/api/privacy/status");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    privacyStatusText.textContent = `${data.message} (Geçici dosya sayısı: ${data.temp_files_cleared})`;
  } catch (err) {
    privacyStatusText.textContent = `Durum alınamadı: ${err.message}`;
  }
}

privacyWipeBtn.addEventListener("click", async () => {
  privacyWipeBtn.disabled = true;
  privacyWipeResult.textContent = "Temizleniyor...";

  try {
    const response = await fetch("/api/privacy/wipe", { method: "POST" });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    privacyWipeResult.textContent = `${data.files_removed} geçici dosya silindi.`;
    loadPrivacyStatus();
  } catch (err) {
    privacyWipeResult.textContent = `Hata: ${err.message}`;
  } finally {
    privacyWipeBtn.disabled = false;
  }
});
