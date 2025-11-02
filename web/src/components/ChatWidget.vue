<template>
  <div class="chat-entry">
    <transition name="fade">
      <button
        v-if="!isOpen"
        class="floating-button"
        type="button"
        @click="openChat"
      >
        <span class="icon">💬</span>
        <span class="label">与 GustoBot 对话</span>
      </button>
    </transition>

    <transition name="pop">
      <div v-if="isOpen" class="chat-panel">
        <header class="chat-header">
          <div class="header-content">
            <div class="title-row">
              <div class="title">GustoBot 智能助手</div>
              <div class="session-chip">
                {{ sessionId ? "会话ID：" + sessionId : "新会话" }}
              </div>
            </div>
            <div class="subtitle">
              <span class="status-dot"></span>
              在线 · 菜谱知识库
            </div>
          </div>
          <button class="close-btn" type="button" @click="closeChat">×</button>
        </header>

        <section ref="messageContainer" class="chat-body">
          <div class="suggestion-bar">
            <button
              v-for="(item, idx) in quickSuggestions"
              :key="idx"
              type="button"
              class="suggestion-chip"
              @click="sendSuggestion(item.prompt)"
            >
              <span class="chip-icon">⚡</span>
              <span>{{ item.label }}</span>
            </button>
          </div>
          <div v-if="messages.length === 0" class="empty-hint">
            <p>你好！我可以帮你查询菜谱知识、历史典故、文件分析等。</p>
            <ul>
              <li>直接输入问题，例如“佛跳墙的由来”。</li>
              <li>上传文件后问我“请分析上传的文件”。</li>
            </ul>
          </div>

          <div
            v-for="(message, index) in messages"
            :key="index"
            :class="['message', message.role]"
          >
            <div class="bubble">
              <p class="content" v-html="linkify(message.content)"></p>
              <div v-if="message.sources?.length" class="sources">
                <span class="sources-title">参考来源</span>
                <ul>
                  <li v-for="(source, sIdx) in message.sources" :key="sIdx">
                    {{ formatSource(source) }}
                  </li>
                </ul>
              </div>
              <div v-if="message.route" class="route">
                路由：{{ message.route }}
                <span v-if="message.routeLogic">（{{ message.routeLogic }}）</span>
              </div>
            </div>
          </div>

          <div v-if="isTyping" class="message assistant">
            <div class="bubble typing">
              <span class="dot"></span>
              <span class="dot"></span>
              <span class="dot"></span>
            </div>
          </div>
        </section>

        <footer class="chat-footer">
          <div class="upload-row">
            <label class="upload-button">
              <input type="file" class="hidden" @change="onFileSelected" />
              <span>📎 上传文件</span>
            </label>
            <div v-if="uploadStatus" class="upload-status">
              {{ uploadStatus }}
            </div>
            <button
              v-if="sessionId"
              type="button"
              class="reset-session"
              @click="resetSession"
            >
              开启新会话
            </button>
          </div>
          <form class="input-row" @submit.prevent="sendMessage">
            <textarea
              v-model="userInput"
              :placeholder="placeholder"
              :disabled="isTyping"
              rows="2"
              @keydown.enter.exact.prevent="sendMessage"
            />
            <button class="send-button" type="submit" :disabled="isTyping || !userInput.trim()">
              发送
            </button>
          </form>
        </footer>
      </div>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onMounted, onUnmounted, reactive, ref, watch } from "vue";
import axios from "axios";

interface ChatMessage {
  role: "user" | "assistant";
  content: string;
  route?: string | null;
  routeLogic?: string | null;
  sources?: Array<Record<string, unknown>>;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || "";

const defaultState = () => ({
  isOpen: false,
  isTyping: false,
  sessionId: "",
  userInput: "",
  messages: [] as ChatMessage[],
  uploadStatus: "",
  attachedFilePath: "",
  attachedFileName: ""
});

const state = reactive(defaultState());

const messageContainer = ref<HTMLElement | null>(null);

const isOpen = computed(() => state.isOpen);
const isTyping = computed(() => state.isTyping);
const sessionId = computed(() => state.sessionId);
const userInput = computed({
  get: () => state.userInput,
  set: (val: string) => {
    state.userInput = val;
  }
});
const messages = computed(() => state.messages);
const uploadStatus = computed(() => state.uploadStatus);

const placeholder = computed(() => {
  if (state.isTyping) return "正在生成回复...";
  if (state.attachedFileName) return `文件已上传：${state.attachedFileName}，请输入问题`;
  return "请输入您的问题，例如“佛跳墙的来历是什么？”";
});

const quickSuggestions = [
  {
    label: "推荐经典鲁菜",
    prompt: "请推荐几道经典鲁菜，并分别说明它们的特色。"
  },
  {
    label: "菜谱历史典故",
    prompt: "佛跳墙这道菜的历史典故是什么？"
  },
  {
    label: "上传文件后如何分析？",
    prompt: "我已经上传了一份菜谱文件，请帮我总结其中的亮点。"
  },
  {
    label: "知识库来源",
    prompt: "知识库里的历史菜谱来源有哪些？"
  }
] as const;

function openChat() {
  state.isOpen = true;
}

function closeChat() {
  state.isOpen = false;
}

defineExpose({
  openChat,
  closeChat
});
function resetSession() {
  state.sessionId = "";
  state.messages = [];
  state.uploadStatus = "";
  state.attachedFileName = "";
  state.attachedFilePath = "";
}

async function onFileSelected(event: Event) {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0];
  if (!file) return;

  state.uploadStatus = "正在上传...";
  try {
    const formData = new FormData();
    formData.append("file", file);
    const { data } = await axios.post(`${API_BASE}/api/v1/upload/file`, formData, {
      headers: { "Content-Type": "multipart/form-data" }
    });
    if (data?.success) {
      state.attachedFilePath = data.file_path;
      state.attachedFileName = data.original_name || file.name;
      state.uploadStatus = `已上传：${state.attachedFileName}`;
    } else {
      throw new Error(data?.detail || "上传失败");
    }
  } catch (error: unknown) {
    console.error("File upload failed", error);
    state.uploadStatus = "上传失败，请重试";
  } finally {
    // reset input to allow re-upload same file
    input.value = "";
  }
}

function sendSuggestion(prompt: string) {
  if (state.isTyping) return;
  state.userInput = prompt;
  void sendMessage();
}

async function sendMessage() {
  const message = state.userInput.trim();
  if (!message || state.isTyping) {
    return;
  }

  const userMessage: ChatMessage = { role: "user", content: message };
  state.messages.push(userMessage);
  state.userInput = "";
  state.isTyping = true;

  try {
    const payload: Record<string, unknown> = {
      message,
      session_id: state.sessionId || undefined,
      stream: false
    };

    if (state.attachedFilePath) {
      payload.file_path = state.attachedFilePath;
    }

    const { data } = await axios.post(`${API_BASE}/api/v1/chat`, payload);

    if (data?.message) {
      const assistantMessage: ChatMessage = {
        role: "assistant",
        content: data.message,
        route: data.route || null,
        routeLogic: data.route_logic || null,
        sources: data.sources || []
      };
      state.messages.push(assistantMessage);
    } else {
      state.messages.push({
        role: "assistant",
        content: "抱歉，未能获取到有效的响应。"
      });
    }

    if (data?.session_id) {
      state.sessionId = data.session_id;
    }

    // 一次性消费文件
    state.attachedFilePath = "";
    state.attachedFileName = "";
    state.uploadStatus = "";
  } catch (error: unknown) {
    console.error("Chat request failed", error);
    state.messages.push({
      role: "assistant",
      content: "请求出错了，请稍后重试。"
    });
  } finally {
    state.isTyping = false;
  }
}

function linkify(text: string): string {
  if (!text) return "";
  return text.replace(
    /(https?:\/\/[^\s]+)/g,
    '<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>'
  );
}

function formatSource(source: Record<string, unknown>): string {
  const docId = source.document_id || source.source || source.id || source.name;
  const name = source.name || source.title || "";
  if (name && docId && name !== docId) {
    return `${name} (${docId})`;
  }
  return String(docId || JSON.stringify(source));
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && state.isOpen) {
    closeChat();
  }
}

watch(
  () => state.messages.length,
  async () => {
    await nextTick();
    if (messageContainer.value) {
      messageContainer.value.scrollTop = messageContainer.value.scrollHeight;
    }
  }
);

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped lang="scss">
.chat-entry {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  font-size: 14px;
  color: #1f2937;
}

.floating-button {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 16px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #f97316, #ef4444);
  color: #fff;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 15px 30px rgba(249, 115, 22, 0.35);
  transition: transform 0.2s ease, box-shadow 0.2s ease;

  &:hover {
    transform: translateY(-2px);
    box-shadow: 0 20px 34px rgba(239, 68, 68, 0.4);
  }

  .icon {
    font-size: 18px;
  }
}

.chat-panel {
  width: clamp(320px, 30vw, 420px);
  height: clamp(460px, 50vh, 640px);
  display: flex;
  flex-direction: column;
  border-radius: 20px;
  background: #fffdfb;
  box-shadow: 0 28px 60px rgba(15, 23, 42, 0.18);
  overflow: hidden;
  border: 1px solid rgba(248, 187, 125, 0.35);
}

.chat-header {
  padding: 18px 20px;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  background: linear-gradient(135deg, #f97316, #ef4444);
  color: #fff;
  box-shadow: inset 0 -1px 0 rgba(255, 255, 255, 0.2);

  .header-content {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .title-row {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .title {
    font-size: 16px;
    font-weight: 600;
    letter-spacing: 0.5px;
  }

  .subtitle {
    font-size: 12px;
    opacity: 0.85;
    display: flex;
    align-items: center;
    gap: 6px;
  }

  .session-chip {
    padding: 2px 8px;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.16);
    font-size: 11px;
    font-weight: 500;
    backdrop-filter: blur(4px);
    max-width: 220px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .status-dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #fef3c7;
    box-shadow: 0 0 0 4px rgba(254, 243, 199, 0.25);
  }

  .close-btn {
    border: none;
    background: transparent;
    color: inherit;
    font-size: 24px;
    cursor: pointer;
    line-height: 1;
    transition: transform 0.2s ease, opacity 0.2s ease;

    &:hover {
      opacity: 0.8;
      transform: scale(1.05);
    }
  }
}

.chat-body {
  flex: 1;
  padding: 16px;
  overflow-y: auto;
  background: linear-gradient(180deg, rgba(255, 244, 230, 0.6), rgba(255, 251, 247, 0.95));
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.suggestion-bar {
  position: sticky;
  top: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding-bottom: 12px;
  margin-bottom: 4px;
  background: linear-gradient(180deg, rgba(255, 251, 247, 0.92), rgba(255, 251, 247, 0));
  z-index: 1;
}

.suggestion-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 10px;
  border-radius: 999px;
  border: 1px solid rgba(249, 115, 22, 0.45);
  background: rgba(255, 247, 237, 0.85);
  color: #9a3412;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;

  &:hover {
    background: linear-gradient(135deg, rgba(249, 115, 22, 0.15), rgba(239, 68, 68, 0.15));
    transform: translateY(-1px);
    box-shadow: 0 4px 10px rgba(239, 68, 68, 0.2);
  }

  .chip-icon {
    font-size: 14px;
  }
}

.empty-hint {
  padding: 18px;
  border-radius: 12px;
  background: rgba(254, 215, 170, 0.5);
  border: 1px dashed rgba(249, 115, 22, 0.4);
  color: #7c2d12;
  font-size: 13px;

  ul {
    padding-left: 18px;
    margin: 10px 0 0;
  }
}

.message {
  display: flex;
  align-items: flex-start;

  &.user {
    justify-content: flex-end;

    .bubble {
      background: linear-gradient(135deg, #f97316, #f97316 40%, #ef4444);
      color: #fff;
      border-bottom-right-radius: 4px;
      box-shadow: 0 12px 24px rgba(239, 68, 68, 0.25);
    }
  }

  &.assistant {
    .bubble {
      background: rgba(255, 255, 255, 0.92);
      color: #1f2937;
      border-bottom-left-radius: 4px;
      border: 1px solid rgba(248, 187, 125, 0.4);
      backdrop-filter: blur(4px);
    }
  }
}

.bubble {
  max-width: 80%;
  padding: 12px 14px;
  border-radius: 14px;
  line-height: 1.5;
  box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
  font-size: 13px;

  a {
    color: #f97316;
    text-decoration: none;

    &:hover {
      text-decoration: underline;
    }
  }
}

.sources {
  margin-top: 10px;
  padding: 12px;
  border-radius: 12px;
  background: rgba(254, 215, 170, 0.35);
  border: 1px dashed rgba(249, 115, 22, 0.45);

  .sources-title {
    font-size: 12px;
    font-weight: 600;
    color: #9a3412;
  }

  ul {
    margin: 6px 0 0;
    padding-left: 18px;
    font-size: 12px;
    color: #1f2937;
  }
}

.route {
  margin-top: 8px;
  font-size: 11px;
  color: #b45309;
}

.typing {
  display: inline-flex;
  align-items: center;
  gap: 4px;

  .dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #f97316;
    animation: pulse 1.2s infinite ease-in-out;

    &:nth-child(2) {
      animation-delay: 0.2s;
    }
    &:nth-child(3) {
      animation-delay: 0.4s;
    }
  }
}

@keyframes pulse {
  0%, 80%, 100% {
    opacity: 0.4;
    transform: translateY(0);
  }
  40% {
    opacity: 1;
    transform: translateY(-3px);
  }
}

.chat-footer {
  padding: 12px 16px 16px;
  background: #fff;
  border-top: 1px solid rgba(248, 187, 125, 0.35);
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.upload-row {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;

  .upload-button {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 10px;
    border-radius: 8px;
    background: rgba(254, 215, 170, 0.4);
    color: #c2410c;
    font-weight: 600;
    cursor: pointer;

    .hidden {
      display: none;
    }
  }

  .upload-status {
    color: #92400e;
  }

  .reset-session {
    margin-left: auto;
    border: none;
    background: transparent;
    color: #fb923c;
    cursor: pointer;
    font-size: 12px;

    &:hover {
      color: #ea580c;
    }
  }
}

.input-row {
  display: flex;
  gap: 10px;
  align-items: flex-end;

  textarea {
    flex: 1;
    resize: none;
    border: 1px solid rgba(148, 163, 184, 0.4);
    border-radius: 12px;
    padding: 10px 12px;
    font-family: inherit;
    font-size: 13px;
    outline: none;

    &:focus {
      border-color: #f97316;
      box-shadow: 0 0 0 3px rgba(249, 115, 22, 0.18);
    }
  }

  .send-button {
    border: none;
    border-radius: 12px;
    padding: 10px 16px;
    background: linear-gradient(135deg, #f97316, #ef4444);
    color: #fff;
    font-weight: 600;
    cursor: pointer;
    transition: opacity 0.2s ease;

    &:disabled {
      opacity: 0.6;
      cursor: not-allowed;
    }
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}
.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.pop-enter-active {
  animation: pop 0.24s ease forwards;
}
.pop-leave-active {
  animation: pop 0.2s ease reverse forwards;
}

@keyframes pop {
  0% {
    opacity: 0;
    transform: translateY(20px) scale(0.96);
  }
  100% {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}
</style>
