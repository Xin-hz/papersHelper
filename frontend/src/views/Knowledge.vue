<template>
  <div class="knowledge-page">
    <div class="page-header">
      <h1>📚 知识库</h1>
      <p class="subtitle">上传文档、基于知识库问答、采集论文补充资料</p>
    </div>

    <!-- 页签：问答与文档 / 论文采集 -->
    <div class="ktabs card">
      <button :class="['ktab', { active: ktab === 'main' }]" @click="ktab = 'main'">💬 问答与文档</button>
      <button :class="['ktab', { active: ktab === 'collect' }]" @click="ktab = 'collect'">📄 论文采集</button>
    </div>

    <template v-if="ktab === 'main'">
    <!-- 知识库问答 -->
    <div class="card qa-card">
      <h3>💬 知识库问答</h3>
      <p class="text-muted">基于已上传的文档回答，回答下方会标注引用来源</p>

      <div class="form-group">
        <label>你的问题</label>
        <textarea
          v-model="question"
          class="textarea-field"
          rows="2"
          placeholder="例如：大班体育游戏可以怎么设计？低结构材料有哪些投放策略？"
          @keydown.ctrl.enter="ask"
        ></textarea>
        <p class="enter-hint">多行输入，写完点"提问"（Ctrl+Enter 也可提交）</p>
      </div>

      <div class="button-group">
        <button @click="ask" :disabled="asking || !question.trim()" class="btn btn-primary">
          {{ asking ? '🤔 思考中...' : '💬 提问' }}
        </button>
      </div>

      <div v-if="answer" class="answer-section">
        <h4>回答</h4>
        <div class="answer-content">{{ answer }}</div>

        <div v-if="qaSources.length > 0" class="qa-sources">
          <h4>引用来源（{{ qaSources.length }}）</h4>
          <div v-for="(s, i) in qaSources" :key="i" class="qa-source-item">
            <div class="qa-source-title">
              📄 {{ s.title }}
              <span v-if="s.year" class="qa-source-year">{{ s.year }}</span>
            </div>
            <div v-if="s.authors && s.authors.length" class="qa-source-authors">
              {{ s.authors.join('、') }}
            </div>
            <div class="qa-source-snippet">{{ s.snippet }}</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传文档 -->
    <div class="card upload-card">
      <h3>📤 上传文档</h3>
      <p class="text-muted">支持 .pdf / .docx / .doc，单次最多 5 个文件，上传后自动切片入库</p>

      <div class="upload-row">
        <input
          type="file"
          ref="fileInput"
          multiple
          accept=".pdf,.docx,.doc"
          style="display: none"
          @change="handleFileSelect"
        />
        <button @click="$refs.fileInput.click()" class="btn">📄 选择文件</button>
        <button
          @click="upload"
          :disabled="uploading || uploadFiles.length === 0"
          class="btn btn-primary"
        >
          {{ uploading ? '⏳ 入库中（可能需要1-2分钟）...' : '📤 上传并入库' }}
        </button>
      </div>

      <div v-if="uploadFiles.length > 0" class="file-list">
        <div v-for="(f, i) in uploadFiles" :key="i" class="file-item">
          <span>📄 {{ f.name }}</span>
          <button @click="removeFile(i)" class="btn btn-text">✕</button>
        </div>
      </div>

      <div v-if="uploadMsg" :class="['msg', uploadMsg.type]">
        {{ uploadMsg.text }}
      </div>
    </div>

    <!-- 知识库统计信息 -->
    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-icon">📄</div>
        <div class="stat-content">
          <h3>文档数量</h3>
          <p class="stat-value" :class="{ loading: statsLoading }">
            {{ statsLoading ? '加载中...' : stats.document_count || 0 }}
          </p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">💾</div>
        <div class="stat-content">
          <h3>数据库大小</h3>
          <p class="stat-value" :class="{ loading: statsLoading }">
            {{ statsLoading ? '加载中...' : formatSize(stats.db_size_bytes || 0) }}
          </p>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-icon">🔍</div>
        <div class="stat-content">
          <h3>向量片段数</h3>
          <p class="stat-value" :class="{ loading: statsLoading }">
            {{ statsLoading ? '加载中...' : stats.vector_count || 0 }}
          </p>
        </div>
      </div>
    </div>

    <!-- 刷新按钮 -->
    <div class="action-bar">
      <button @click="loadStats" :disabled="statsLoading" class="btn btn-primary">
        {{ statsLoading ? '🔄 刷新中...' : '🔄 刷新统计' }}
      </button>
    </div>

    <!-- 检索验证 -->
    <div class="card search-card">
      <h3>🔍 检索验证</h3>
      <p class="text-muted">输入关键词验证文档是否正确入库</p>

      <div class="search-form">
        <div class="form-group">
          <label>检索关键词</label>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="例如：游戏化教学、区域活动、家园共育"
            class="input-field"
            @keyup.enter="search"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>返回结果数</label>
            <input
              v-model.number="topK"
              type="number"
              min="1"
              max="20"
              class="input-field"
            />
          </div>
          <div class="form-group">
            <label>&nbsp;</label>
            <button
              @click="search"
              :disabled="searchLoading || !searchQuery.trim()"
              class="btn btn-primary"
            >
              {{ searchLoading ? '🔍 检索中...' : '🔍 检索验证' }}
            </button>
          </div>
        </div>
      </div>

      <div v-if="searchMsg" :class="['msg', searchMsg.type]">
        {{ searchMsg.text }}
      </div>

      <!-- 检索结果 -->
      <div v-if="searchResults.length > 0" class="results-section">
        <h4>检索结果 ({{ searchResults.length }})</h4>
        <div class="results-list">
          <div
            v-for="(result, index) in searchResults"
            :key="index"
            class="result-item"
          >
            <div class="result-header">
              <span class="result-rank">第 {{ index + 1 }} 条</span>
              <span class="result-score">相似度: {{ (result.score * 100).toFixed(1) }}%</span>
            </div>
            <div class="result-content">{{ result.content }}</div>
            <div class="result-meta" v-if="result.metadata">
              <span class="result-source">📄 {{ result.metadata.source || '未知来源' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div v-else-if="searchQuery && !searchLoading && searchResults.length === 0" class="no-results">
        <p>❌ 未找到相关内容，请确认知识库是否包含相关文档</p>
      </div>
    </div>
    </template>

    <!-- 论文采集（并入知识库作为补充资料入口） -->
    <Collector v-if="ktab === 'collect'" />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import Collector from './Collector.vue'

const ktab = ref('main')

const API_BASE = '' // 同源请求：dev 走 vite 代理，生产与后端同域

// 知识库问答
const question = ref('')
const asking = ref(false)
const answer = ref('')
const qaSources = ref([])

async function ask() {
  if (!question.value.trim()) return
  asking.value = true
  answer.value = ''
  qaSources.value = []
  try {
    const response = await fetch(`${API_BASE}/api/ask_knowledge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question: question.value })
    })
    const data = await response.json()
    if (data.success) {
      answer.value = data.answer
      qaSources.value = data.sources || []
    } else {
      answer.value = data.answer || '查询失败，请稍后重试'
    }
  } catch (error) {
    answer.value = '请求出错: ' + error.message
  } finally {
    asking.value = false
  }
}

// 上传文档
const fileInput = ref(null)
const uploadFiles = ref([])
const uploading = ref(false)
const uploadMsg = ref(null)

function handleFileSelect(e) {
  const list = Array.from(e.target.files || [])
  uploadFiles.value = list.slice(0, 5)
  if (list.length > 5) uploadMsg.value = { text: '单次最多 5 个文件，已只取前 5 个', type: 'warning' }
  else uploadMsg.value = null
}

function removeFile(index) {
  uploadFiles.value.splice(index, 1)
}

async function upload() {
  if (uploadFiles.value.length === 0) return
  uploading.value = true
  uploadMsg.value = null
  try {
    const fd = new FormData()
    uploadFiles.value.forEach((f) => fd.append('files', f))
    const response = await fetch(`${API_BASE}/api/upload_knowledge`, { method: 'POST', body: fd })
    const data = await response.json().catch(() => ({}))
    if (response.ok && data.success) {
      uploadMsg.value = { text: data.message || '上传成功', type: 'success' }
      uploadFiles.value = []
      if (fileInput.value) fileInput.value.value = ''
      loadStats()
    } else {
      uploadMsg.value = { text: data.detail || data.message || '上传失败', type: 'error' }
    }
  } catch (error) {
    uploadMsg.value = { text: '上传出错: ' + error.message, type: 'error' }
  } finally {
    uploading.value = false
  }
}

// 统计信息
const stats = ref({
  document_count: 0,
  db_size_bytes: 0,
  vector_count: 0
})
const statsLoading = ref(false)

// 检索相关
const searchQuery = ref('')
const topK = ref(5)
const searchLoading = ref(false)
const searchResults = ref([])
const searchMsg = ref(null)

// 格式化文件大小
function formatSize(bytes) {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

// 加载统计信息
async function loadStats() {
  statsLoading.value = true
  try {
    const response = await fetch(`${API_BASE}/api/knowledge/stats`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' }
    })

    if (response.ok) {
      const data = await response.json()
      if (data.success) {
        stats.value = data.stats
      } else {
        console.error('获取统计信息失败:', data.message)
      }
    } else {
      console.error('请求失败:', response.status)
    }
  } catch (error) {
    console.error('加载统计信息出错:', error)
  } finally {
    statsLoading.value = false
  }
}

// 检索验证
async function search() {
  if (!searchQuery.value.trim()) {
    searchMsg.value = { text: '请输入检索关键词', type: 'error' }
    return
  }

  searchLoading.value = true
  searchResults.value = []
  searchMsg.value = null

  try {
    const response = await fetch(`${API_BASE}/api/knowledge/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchQuery.value,
        top_k: topK.value || 5
      })
    })

    const data = await response.json()

    if (data.success) {
      searchResults.value = data.results || []
      if (searchResults.value.length === 0) {
        searchMsg.value = { text: '未找到相关内容', type: 'warning' }
      }
    } else {
      searchMsg.value = { text: data.message || '检索失败', type: 'error' }
    }
  } catch (error) {
    console.error('检索出错:', error)
    searchMsg.value = { text: '检索出错: ' + error.message, type: 'error' }
  } finally {
    searchLoading.value = false
  }
}

// 页面加载时获取统计信息
onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.ktabs { display: flex; gap: 0.5rem; padding: 0.7rem 0.9rem; }
.ktab { flex: 1; padding: 0.55rem 0.9rem; border: 1px solid var(--border); background: none; border-radius: var(--radius); font-size: 0.92rem; cursor: pointer; color: var(--text-muted); }
.ktab.active { border-color: var(--primary); color: var(--primary); font-weight: 600; background: var(--bg); }

.enter-hint {
  margin: 0.3rem 0 0;
  font-size: 0.8rem;
  color: var(--text-muted);
}
.knowledge-page {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.page-header {
  text-align: center;
}

.page-header h1 {
  font-size: 1.8rem;
  color: var(--primary);
  margin-bottom: 0.5rem;
}

.subtitle {
  color: var(--text-muted);
  font-size: 0.95rem;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.stat-card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  transition: transform 0.2s, box-shadow 0.2s;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-icon {
  font-size: 2.5rem;
  width: 60px;
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--bg);
  border-radius: 50%;
}

.stat-content h3 {
  margin: 0 0 0.5rem 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  font-weight: 500;
}

.stat-value {
  margin: 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--primary);
}

.stat-value.loading {
  color: var(--text-muted);
  font-size: 1rem;
}

.action-bar {
  display: flex;
  justify-content: center;
  gap: 1rem;
}

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.textarea-field {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-family: inherit;
  resize: vertical;
}

.textarea-field:focus {
  outline: none;
  border-color: var(--primary);
}

.button-group {
  display: flex;
  gap: 0.75rem;
}

.answer-section {
  margin-top: 1.25rem;
  padding-top: 1.25rem;
  border-top: 1px solid var(--border);
}

.answer-section h4,
.qa-sources h4 {
  margin: 0 0 0.75rem 0;
  font-size: 0.95rem;
  color: var(--text);
}

.answer-content {
  background: var(--bg);
  border-radius: var(--radius);
  padding: 1rem;
  line-height: 1.7;
  white-space: pre-wrap;
  color: var(--text);
}

.qa-sources {
  margin-top: 1.25rem;
}

.qa-source-item {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 0.75rem 1rem;
  margin-bottom: 0.5rem;
}

.qa-source-title {
  font-weight: 600;
  color: var(--primary);
  font-size: 0.9rem;
}

.qa-source-year {
  color: var(--text-muted);
  font-weight: 400;
  margin-left: 0.4rem;
}

.qa-source-authors {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 0.15rem;
}

.qa-source-snippet {
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-top: 0.35rem;
  line-height: 1.5;
}

.upload-row {
  display: flex;
  gap: 0.75rem;
  align-items: center;
}

.btn-text {
  border: none;
  background: none;
  padding: 0.2rem 0.4rem;
  color: var(--text-muted);
}

.file-list {
  margin-top: 0.75rem;
  display: flex;
  flex-direction: column;
  gap: 0.4rem;
}

.file-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg);
  border-radius: var(--radius);
  padding: 0.5rem 0.8rem;
  font-size: 0.9rem;
}

.card h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: var(--text);
}

.text-muted {
  color: var(--text-muted);
  font-size: 0.9rem;
  margin-bottom: 1rem;
}

.search-form {
  margin-bottom: 1rem;
}

.form-group {
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 2fr;
  gap: 1rem;
}

.form-group label {
  display: block;
  margin-bottom: 0.5rem;
  font-weight: 500;
  font-size: 0.9rem;
  color: var(--text);
}

.input-field {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  transition: border-color 0.2s;
}

.input-field:focus {
  outline: none;
  border-color: var(--primary);
}

.btn {
  padding: 0.7rem 1.2rem;
  border: none;
  border-radius: var(--radius);
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.2s;
  font-weight: 500;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-primary {
  background: var(--primary);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  background: var(--primary-hover);
}

.msg {
  padding: 0.8rem 1rem;
  border-radius: var(--radius);
  margin-bottom: 1rem;
  font-size: 0.9rem;
}

.msg.error {
  background: #fee;
  color: #c33;
  border: 1px solid #fcc;
}

.msg.success {
  background: #efe;
  color: #3c3;
  border: 1px solid #cfc;
}

.msg.warning {
  background: #ffc;
  color: #963;
  border: 1px solid #fc9;
}

.results-section {
  margin-top: 1.5rem;
  padding-top: 1.5rem;
  border-top: 1px solid var(--border);
}

.results-section h4 {
  margin: 0 0 1rem 0;
  font-size: 1rem;
  color: var(--text);
}

.results-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.result-item {
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  transition: all 0.2s;
}

.result-item:hover {
  border-color: var(--primary);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
}

.result-rank {
  font-weight: 600;
  color: var(--primary);
}

.result-score {
  color: var(--text-muted);
}

.result-content {
  line-height: 1.6;
  color: var(--text);
  margin-bottom: 0.5rem;
  white-space: pre-wrap;
}

.result-meta {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.no-results {
  text-align: center;
  padding: 2rem;
  color: var(--text-muted);
  background: var(--bg);
  border-radius: var(--radius);
  margin-top: 1rem;
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .action-bar {
    flex-direction: column;
  }
}
</style>