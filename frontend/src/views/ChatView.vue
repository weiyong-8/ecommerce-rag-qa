<template>
  <div class="chat-layout">
    <!-- 左: 会话列表 -->
    <div class="side">
      <div class="side-header">
        <el-button type="primary" class="new-btn" @click="newChat">＋ 新建对话</el-button>
      </div>
      <div v-loading="convLoading" class="conv-list">
        <div
          v-for="c in conversations"
          :key="c.id"
          class="conv-item"
          :class="{ active: c.id === currentId }"
          @click="openConversation(c)"
        >
          <div class="conv-title">{{ c.title }}</div>
          <div class="conv-meta">
            <span>{{ formatTime(c.updated_at) }}</span>
            <span class="conv-actions" @click.stop>
              <el-button link size="small" @click="renameConv(c)">改名</el-button>
              <el-button link size="small" type="danger" @click="removeConv(c)">删除</el-button>
            </span>
          </div>
        </div>
        <el-empty
          v-if="!convLoading && !conversations.length"
          description="暂无会话,点击上方新建"
          :image-size="70"
        />
      </div>
    </div>

    <!-- 右: 消息区 -->
    <div class="main">
      <div ref="msgArea" class="msg-area">
        <el-empty
          v-if="!messages.length"
          description="向知识库提问吧,回答会标注引用的知识片段"
        />
        <div v-for="(m, i) in messages" :key="i" class="msg-row" :class="m.role">
          <div class="bubble">
            <div v-if="m.role === 'assistant'" class="md" v-html="renderMd(m.content)"></div>
            <div v-else class="plain">{{ m.content }}</div>
            <!-- 引用片段卡片 -->
            <div v-if="m.role === 'assistant' && m.sources?.length" class="sources">
              <div class="src-label">📎 参考的知识库片段</div>
              <div v-for="s in m.sources" :key="s.index" class="src-item">
                <div class="src-head">
                  <el-tag size="small" type="info">[{{ s.index }}]</el-tag>
                  <span class="src-name">{{ s.doc_name }}</span>
                  <span v-if="s.headers" class="src-headers">{{ s.headers }}</span>
                </div>
                <p class="src-text">{{ s.text }}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="input-area">
        <el-input
          v-model="question"
          type="textarea"
          :rows="3"
          resize="none"
          placeholder="输入商品相关问题,如: 星耀 X9 Pro 支持多少瓦快充?(Enter 发送,Shift+Enter 换行)"
          @keydown.enter.exact.prevent="send"
        />
        <el-button
          type="primary"
          class="send-btn"
          :loading="streaming"
          :disabled="!question.trim() || !currentId"
          @click="send"
        >
          {{ streaming ? '回答中…' : '发 送' }}
        </el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { nextTick, onMounted, reactive, ref } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { marked } from 'marked'
import DOMPurify from 'dompurify'
import {
  createConversation,
  deleteConversation,
  listConversations,
  listMessages,
  renameConversation,
  streamAsk,
} from '../api/chat'

const conversations = ref([])
const currentId = ref(null)
const messages = ref([])
const question = ref('')
const streaming = ref(false)
const convLoading = ref(false)
const msgArea = ref(null)

function renderMd(text) {
  return DOMPurify.sanitize(marked.parse(text || ''))
}

function formatTime(s) {
  if (!s) return ''
  return s.replace('T', ' ').slice(5, 16)
}

function scrollToBottom() {
  nextTick(() => {
    if (msgArea.value) msgArea.value.scrollTop = msgArea.value.scrollHeight
  })
}

async function refreshConversations() {
  convLoading.value = true
  try {
    conversations.value = await listConversations()
  } catch (e) {
    ElMessage.error('会话列表加载失败')
  } finally {
    convLoading.value = false
  }
}

async function newChat() {
  try {
    const conv = await createConversation({ title: '新对话' })
    await refreshConversations()
    openConversation(conv)
  } catch (e) {
    ElMessage.error('新建会话失败')
  }
}

async function openConversation(c) {
  currentId.value = c.id
  messages.value = await listMessages(c.id)
  scrollToBottom()
}

async function renameConv(c) {
  let title
  try {
    const { value } = await ElMessageBox.prompt('输入新的会话名称', '会话改名', {
      inputValue: c.title,
      confirmButtonText: '保存',
      cancelButtonText: '取消',
    })
    title = value
  } catch {
    return
  }
  try {
    await renameConversation(c.id, { title: title.trim() || c.title })
    await refreshConversations()
  } catch (e) {
    ElMessage.error('改名失败')
  }
}

async function removeConv(c) {
  try {
    await ElMessageBox.confirm(`确认删除会话《${c.title}》及其全部聊天记录?`, '删除确认', {
      type: 'warning',
      confirmButtonText: '删除',
      cancelButtonText: '取消',
    })
  } catch {
    return
  }
  try {
    await deleteConversation(c.id)
    if (currentId.value === c.id) {
      currentId.value = null
      messages.value = []
    }
    await refreshConversations()
  } catch (e) {
    ElMessage.error('删除失败')
  }
}

async function send() {
  const q = question.value.trim()
  if (!q || !currentId.value || streaming.value) return
  question.value = ''
  messages.value.push({ role: 'user', content: q })
  const assistant = reactive({ role: 'assistant', content: '', sources: [] })
  messages.value.push(assistant)
  streaming.value = true
  scrollToBottom()
  try {
    await streamAsk(currentId.value, q, {
      onToken: (t) => {
        assistant.content += t
        scrollToBottom()
      },
      onSources: (s) => {
        assistant.sources = s
      },
      onDone: () => {
        // 首次提问后标题可能被后端自动更新,刷新列表
        refreshConversations()
      },
      onError: (msg) => {
        assistant.content = `⚠️ ${msg}`
      },
    })
  } catch (e) {
    assistant.content = `⚠️ 请求失败: ${e.message || e}`
  } finally {
    streaming.value = false
    scrollToBottom()
  }
}

onMounted(refreshConversations)
</script>

<style scoped>
.chat-layout {
  display: flex;
  height: calc(100vh - 120px);
  gap: 16px;
}
.side {
  width: 260px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}
.side-header {
  padding: 12px;
  border-bottom: 1px solid #e4e7ed;
}
.new-btn {
  width: 100%;
}
.conv-list {
  flex: 1;
  overflow-y: auto;
}
.conv-item {
  padding: 10px 12px;
  cursor: pointer;
  border-bottom: 1px solid #f2f3f5;
}
.conv-item:hover {
  background: #f5f7fa;
}
.conv-item.active {
  background: #ecf5ff;
  border-left: 3px solid #409eff;
}
.conv-title {
  font-size: 14px;
  color: #303133;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.conv-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 4px;
  font-size: 12px;
  color: #909399;
}
.main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fff;
  border-radius: 6px;
  border: 1px solid #e4e7ed;
  overflow: hidden;
}
.msg-area {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}
.msg-row {
  display: flex;
  margin-bottom: 16px;
}
.msg-row.user {
  justify-content: flex-end;
}
.bubble {
  max-width: 78%;
  padding: 10px 14px;
  border-radius: 8px;
  font-size: 14px;
  line-height: 1.7;
}
.msg-row.user .bubble {
  background: #409eff;
  color: #fff;
}
.msg-row.assistant .bubble {
  background: #f4f4f5;
  color: #303133;
}
.plain {
  white-space: pre-wrap;
}
.sources {
  margin-top: 10px;
  border-top: 1px dashed #dcdfe6;
  padding-top: 8px;
}
.src-label {
  font-size: 12px;
  color: #909399;
  margin-bottom: 6px;
}
.src-item {
  background: #fff;
  border-radius: 4px;
  padding: 8px 10px;
  margin-bottom: 6px;
}
.src-head {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}
.src-name {
  font-size: 13px;
  font-weight: 600;
}
.src-headers {
  font-size: 12px;
  color: #909399;
}
.src-text {
  margin: 0;
  font-size: 12px;
  color: #606266;
  max-height: 72px;
  overflow-y: auto;
}
.input-area {
  display: flex;
  gap: 12px;
  padding: 14px;
  border-top: 1px solid #e4e7ed;
  align-items: flex-end;
}
.send-btn {
  height: 60px;
  width: 110px;
}
.md :deep(p) {
  margin: 4px 0;
}
.md :deep(ul),
.md :deep(ol) {
  padding-left: 20px;
  margin: 4px 0;
}
.md :deep(code) {
  background: rgba(0, 0, 0, 0.06);
  padding: 1px 5px;
  border-radius: 3px;
}
</style>
