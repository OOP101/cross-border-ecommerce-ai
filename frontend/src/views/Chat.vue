<template>
  <div class="chat-page">
    <div class="chat-panel">
      <div class="chat-header">
        <el-icon><ChatDotRound /></el-icon>
        <span>跨境电商智能客服</span>
        <el-tag size="small" type="info" effect="plain">RAG + Agent</el-tag>
        <el-tag size="small" type="success" effect="plain">流式回答</el-tag>
      </div>

      <div ref="listRef" class="chat-list">
        <!-- 欢迎区 + 快捷指令卡片（仅在会话开始前展示） -->
        <div v-if="messages.length <= 1" class="welcome">
          <div class="welcome-title">您好，我是您的跨境电商 AI 助手 👋</div>
          <div class="welcome-sub">基于企业知识库实时作答，支持订单、物流、产品、售后与贸易术语咨询。点击下方卡片快速提问：</div>
          <div class="suggestion-grid">
            <div
              v-for="s in suggestions"
              :key="s.text"
              class="suggestion-card"
              @click="send(null, s.text)"
            >
              <div class="s-icon">{{ s.icon }}</div>
              <div class="s-body">
                <div class="s-title">{{ s.title }}</div>
                <div class="s-desc">{{ s.desc }}</div>
              </div>
            </div>
          </div>
        </div>

        <div v-for="(msg, i) in messages" :key="i" class="msg-row" :class="msg.role">
          <div class="avatar" :class="msg.role">
            {{ msg.role === 'user' ? '我' : 'AI' }}
          </div>
          <div class="bubble-wrap">
            <div class="bubble">{{ msg.role === 'assistant' && !msg.content ? '正在思考…' : msg.content }}</div>
            <div v-if="msg.intent" class="meta">
              <el-tag size="small" type="primary" effect="plain">意图：{{ intentLabel(msg.intent) }}</el-tag>
              <el-tag v-if="msg.need_human" size="small" type="danger" effect="plain">已转人工</el-tag>
            </div>
            <div v-if="msg.sources && msg.sources.length" class="sources">
              <el-collapse>
                <el-collapse-item :title="`知识来源（${msg.sources.length} 条，点击展开）`">
                  <div v-for="(s, j) in msg.sources" :key="j" class="source-item">
                    <div class="source-head">
                      <el-tag size="small" type="success" effect="plain">{{ s.source }}</el-tag>
                      <span class="score">相关度 {{ (s.score * 100).toFixed(1) }}%</span>
                    </div>
                    <p class="source-text">{{ s.text }}</p>
                  </div>
                </el-collapse-item>
              </el-collapse>
            </div>
          </div>
        </div>

        <div v-if="loading" class="typing">
          <span></span><span></span><span></span>
        </div>
      </div>

      <!-- 快捷输入 chips -->
      <div class="quick-chips">
        <span class="chips-label">快捷提问</span>
        <div class="chips-scroll">
          <el-tag
            v-for="s in suggestions"
            :key="s.text"
            class="chip"
            effect="plain"
            @click="send(null, s.text)"
          >{{ s.icon }} {{ s.title }}</el-tag>
        </div>
      </div>

      <div class="chat-input">
        <el-input
          v-model="input"
          type="textarea"
          :rows="2"
          resize="none"
          placeholder="请输入您的问题，例如：订单什么时候发货？支持哪些支付方式？（Enter 发送）"
          @keydown.enter.exact.prevent="send()"
        />
        <el-button type="primary" size="large" :loading="loading" @click="send()">发送</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, ref } from 'vue'
import { TOKEN_KEY } from '../api'

const API_BASE = import.meta.env.VITE_API_BASE || '/api/v1'

// 快捷指令卡片（与示例知识库对齐，点击即发送）
const suggestions = [
  { icon: '📦', title: '订单什么时候发货？', desc: '现货 24-48 小时内发货', text: '订单什么时候发货？' },
  { icon: '💳', title: '支持哪些支付方式？', desc: 'T/T、信用证、PayPal 等', text: '支持哪些支付方式？' },
  { icon: '🔢', title: 'MOQ 起订量是多少？', desc: '常规产品 100 件起', text: '最小起订量 MOQ 是多少？' },
  { icon: '🚢', title: 'FOB 和 CIF 的区别？', desc: '常用贸易术语解读', text: 'FOB 和 CIF 有什么区别？' },
  { icon: '↩️', title: '退换货流程', desc: '售后申请与处理时效', text: '退换货流程是怎样的？' },
  { icon: '📜', title: '产品国际认证', desc: 'CE、RoHS、FCC、FDA', text: '产品有哪些国际认证？' },
  { icon: '💡', title: 'LED 灯带规格', desc: '热销产品参数一览', text: '智能LED灯带是什么规格？' },
  { icon: '🏭', title: 'OEM 贴牌定制', desc: '可打客户 LOGO', text: '可以OEM贴牌定制吗？' },
]

const input = ref('')
const loading = ref(false)
const messages = ref([
  {
    role: 'assistant',
    content: '您好！我是多语言智能客服，可为您解答订单、物流、产品、售后等问题。',
  },
])
const listRef = ref(null)
const sessionId = ref('session-' + Date.now())

const intentMap = {
  order: '订单查询',
  after_sales: '售后处理',
  product: '产品咨询',
  translation: '翻译',
  human: '人工转接',
}

const intentLabel = (i) => intentMap[i] || i

const scrollBottom = async () => {
  await nextTick()
  if (listRef.value) listRef.value.scrollTop = listRef.value.scrollHeight
}

const send = async (evt, presetText) => {
  const text = (presetText ?? input.value).trim()
  if (!text || loading.value) return
  const history = messages.value.slice(-8).map((m) => ({ role: m.role, content: m.content }))
  messages.value.push({ role: 'user', content: text })
  if (!presetText) input.value = ''
  loading.value = true
  // 流式：先占位一条空回复，随 SSE delta 逐段填充
  const assistant = { role: 'assistant', content: '', intent: '', need_human: false, sources: [] }
  messages.value.push(assistant)
  await scrollBottom()
  try {
    const token = localStorage.getItem(TOKEN_KEY)
    const resp = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: JSON.stringify({ message: text, session_id: sessionId.value, history }),
    })
    if (!resp.ok || !resp.body) throw new Error(`HTTP ${resp.status}`)
    const reader = resp.body.getReader()
    const decoder = new TextDecoder('utf-8')
    let buf = ''
    for (;;) {
      const { value, done } = await reader.read()
      if (done) break
      buf += decoder.decode(value, { stream: true })
      const frames = buf.split('\n\n')
      buf = frames.pop()
      for (const frame of frames) {
        const lines = frame.split('\n')
        const event = (lines.find((l) => l.startsWith('event:')) || '').slice(6).trim()
        const dataLine = lines.find((l) => l.startsWith('data:'))
        if (!dataLine) continue
        const data = JSON.parse(dataLine.slice(5).trim())
        if (event === 'delta') {
          assistant.content += data.text
          await scrollBottom()
        } else if (event === 'meta') {
          assistant.intent = data.intent
          assistant.need_human = data.need_human
          assistant.sources = data.sources
        }
      }
    }
  } catch (e) {
    if (!assistant.content) assistant.content = '请求失败，请检查后端服务是否启动。'
  } finally {
    loading.value = false
    await scrollBottom()
  }
}
</script>

<style scoped>
.chat-page {
  height: calc(100vh - 100px);
  display: flex;
  justify-content: center;
}
.chat-panel {
  width: 100%;
  max-width: 880px;
  background: #fff;
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 18px rgba(0, 0, 0, 0.06);
  overflow: hidden;
}
.chat-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  border-bottom: 1px solid #f0f0f0;
  font-weight: 600;
}

/* ---- 欢迎区与快捷指令卡片 ---- */
.welcome {
  padding: 28px 12px 8px;
  text-align: center;
}
.welcome-title {
  font-size: 20px;
  font-weight: 700;
  color: #303133;
}
.welcome-sub {
  margin: 10px auto 22px;
  max-width: 560px;
  color: #909399;
  font-size: 13px;
  line-height: 1.6;
}
.suggestion-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
  text-align: left;
}
.suggestion-card {
  display: flex;
  gap: 10px;
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fafbfc;
}
.suggestion-card:hover {
  border-color: #409eff;
  background: #ecf5ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.15);
}
.s-icon {
  font-size: 22px;
  line-height: 1;
}
.s-title {
  font-size: 13px;
  font-weight: 600;
  color: #303133;
}
.s-desc {
  margin-top: 3px;
  font-size: 12px;
  color: #909399;
}

.chat-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.msg-row.user {
  flex-direction: row-reverse;
}
.avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 13px;
  color: #fff;
  flex-shrink: 0;
}
.avatar.user {
  background: #67c23a;
}
.avatar.assistant {
  background: #409eff;
}
.bubble-wrap {
  max-width: 75%;
}
.bubble {
  padding: 10px 14px;
  border-radius: 10px;
  background: #f4f4f5;
  color: #303133;
  line-height: 1.6;
  white-space: pre-wrap;
  word-break: break-word;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}
.msg-row.user .bubble {
  background: #409eff;
  color: #fff;
}
.meta {
  margin-top: 6px;
  display: flex;
  gap: 6px;
}
.sources {
  margin-top: 6px;
}
.source-item {
  padding: 6px 0;
}
.source-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.score {
  font-size: 12px;
  color: #909399;
}
.source-text {
  margin-top: 4px;
  font-size: 12px;
  color: #606266;
  line-height: 1.5;
}
.typing {
  display: flex;
  gap: 4px;
  padding: 0 20px 12px;
}
.typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c0c4cc;
  animation: blink 1.2s infinite ease-in-out;
}
.typing span:nth-child(2) {
  animation-delay: 0.2s;
}
.typing span:nth-child(3) {
  animation-delay: 0.4s;
}
@keyframes blink {
  0%,
  80%,
  100% {
    opacity: 0.3;
  }
  40% {
    opacity: 1;
  }
}

/* ---- 快捷输入 chips ---- */
.quick-chips {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px 0;
}
.chips-label {
  font-size: 12px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.chips-scroll {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 4px;
}
.chips-scroll::-webkit-scrollbar {
  height: 0;
}
.chip {
  cursor: pointer;
  flex-shrink: 0;
  transition: all 0.15s;
}
.chip:hover {
  color: #409eff;
  border-color: #409eff;
}

.chat-input {
  display: flex;
  gap: 10px;
  padding: 12px 20px 16px;
  border-top: 1px solid #f0f0f0;
  align-items: flex-end;
}
</style>
