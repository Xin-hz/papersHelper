<template>
  <div class="revise-page">
    <div class="page-header">
      <h1>🛠️ 改论文</h1>
      <p class="subtitle">粘贴文本或上传文件，然后优化、降重或生成评审报告</p>
    </div>

    <!-- 输入源 -->
    <div class="card">
      <div class="src-tabs">
        <button :class="['src-tab', { active: srcTab === 'paste' }]" @click="srcTab = 'paste'">📋 粘贴文本</button>
        <button :class="['src-tab', { active: srcTab === 'file' }]" @click="srcTab = 'file'">📁 上传文件</button>
      </div>

      <template v-if="srcTab === 'file'">
        <div class="file-row">
          <input ref="fileInput" type="file" accept=".txt,.md,.tex,.docx,.doc,.pdf" style="display: none" @change="handleFile" />
          <button class="btn" @click="$refs.fileInput.click()">选择文件</button>
          <span v-if="extracting" class="hint">提取文本中…</span>
          <span v-else-if="extractedName" class="hint">✅ 已提取 {{ extractedName }}（{{ content.length }} 字）</span>
          <span v-else class="hint">支持 .txt .md .tex .docx .doc .pdf（扫描版 PDF 无法提取）</span>
        </div>
      </template>

      <textarea
        v-model="content"
        class="textarea-field big"
        placeholder="粘贴论文全文，或从上方上传文件提取；从「写论文」跳转会自动带入正文"
      ></textarea>
      <p class="hint">当前 {{ content.length }} 字 · 可直接编辑</p>
    </div>

    <!-- 三个操作 -->
    <div class="ops-grid">
      <!-- 优化 -->
      <div class="card op-card">
        <h3>✨ 优化</h3>
        <p class="op-desc">输入你的修改意见，AI 按意见优化全文</p>
        <textarea v-model="opinion" class="textarea-field" rows="3" placeholder="例如：第二部分太单薄要扩充案例；结论不要口号化；语言再学术一点"></textarea>
        <button class="btn btn-primary" :disabled="busy || !content.trim() || !opinion.trim()" @click="optimize">
          {{ busy === 'optimize' ? '优化中…约1-3分钟' : '按意见优化' }}
        </button>
      </div>

      <!-- 降重 -->
      <div class="card op-card">
        <h3>🔁 降重</h3>
        <p class="op-desc">同义替换与句式改写降低重复率，数据与引用保持不变</p>
        <div class="intensity-row">
          <button v-for="opt in intensities" :key="opt.value"
                  :class="['int-btn', { active: intensity === opt.value }]"
                  @click="intensity = opt.value">{{ opt.label }}</button>
        </div>
        <button class="btn btn-primary" :disabled="busy || !content.trim()" @click="reduce">
          {{ busy === 'reduce' ? '降重中…约1-3分钟' : '开始降重' }}
        </button>
        <p class="hint">需要保留 Word 排版格式的整篇降重？<router-link to="/rewrite">用文件降重</router-link></p>
      </div>

      <!-- 评审 -->
      <div class="card op-card">
        <h3>📋 评审</h3>
        <p class="op-desc">按评选标准生成评审报告：分项打分、问题清单、修改建议</p>
        <button class="btn btn-primary" :disabled="busy || !content.trim()" @click="review">
          {{ busy === 'review' ? '评审中…约1-2分钟' : '生成评审报告' }}
        </button>
        <div v-if="report" class="report-box">{{ report }}</div>
      </div>
    </div>

    <!-- 工具栏 -->
    <div class="card toolbar" v-if="content">
      <button v-if="undoAvailable" class="btn" @click="undo">↩ 撤销上次处理</button>
      <button class="btn" @click="downloadTxt">📥 下载 .txt</button>
      <button class="btn" @click="copy">📋 复制全文</button>
    </div>

    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { api, friendlyError } from '../api'

const srcTab = ref('paste')
const content = ref('')
const busy = ref('') // '' | 'optimize' | 'reduce' | 'review'
const undoStack = ref([])
const report = ref('')

const msg = ref(null)
function showMsg(text, type = 'error') {
  msg.value = { text: friendlyError(text), type }
  setTimeout(() => { msg.value = null }, 5000)
}

onMounted(() => {
  const carried = sessionStorage.getItem('revise_content')
  if (carried) {
    content.value = carried
    sessionStorage.removeItem('revise_content')
    showMsg('已带入写论文的正文', 'success')
  }
})

// ---------- 文件提取 ----------
const fileInput = ref(null)
const extracting = ref(false)
const extractedName = ref('')

async function handleFile(e) {
  const file = e.target.files && e.target.files[0]
  if (!file) return
  extracting.value = true
  extractedName.value = ''
  try {
    const fd = new FormData()
    fd.append('file', file)
    const d = await fetch('/api/extract_text', { method: 'POST', body: fd }).then(r => r.json())
    if (d.success) {
      content.value = d.text
      extractedName.value = d.filename
      showMsg(`已提取 ${d.chars} 字`, 'success')
    } else {
      showMsg(d.error || '提取失败')
    }
  } catch (err) {
    showMsg('请求出错: ' + err.message)
  } finally {
    extracting.value = false
    if (fileInput.value) fileInput.value.value = ''
  }
}

// ---------- 优化 ----------
const opinion = ref('')

async function optimize() {
  busy.value = 'optimize'
  try {
    const d = await api.improvePaper({ content: content.value, focus: `按作者意见优化：${opinion.value}` })
    if (d.success && d.content) {
      undoStack.value.push(content.value)
      content.value = d.content
      showMsg('优化完成（可撤销）', 'success')
    } else {
      showMsg(d.content || '优化失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    busy.value = ''
  }
}

// ---------- 降重 ----------
const intensity = ref('medium')
const intensities = [
  { value: 'light', label: '轻度' },
  { value: 'medium', label: '中度' },
  { value: 'heavy', label: '重度' },
]
const intensityFocus = {
  light: '轻度：保守的同义替换与句式微调，保留约八成原文表达',
  medium: '中度：实质性改写，句式重构、主语变换、因果重述，保留约五成原文表达',
  heavy: '重度：彻底重组，调整论点顺序、论证逻辑改写、重新切分论述单元，保留约三成原文表达',
}

async function reduce() {
  busy.value = 'reduce'
  try {
    const d = await api.reduceWeight({ content: content.value, focus: intensityFocus[intensity.value] })
    if (d.success && d.content) {
      undoStack.value.push(content.value)
      content.value = d.content
      showMsg('降重完成（可撤销）', 'success')
    } else {
      showMsg(d.content || '降重失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    busy.value = ''
  }
}

// ---------- 评审 ----------
async function review() {
  busy.value = 'review'
  report.value = ''
  try {
    const d = await api.reviewPaper({ content: content.value })
    if (d.success) {
      report.value = d.report
      showMsg('评审报告已生成', 'success')
    } else {
      showMsg(d.error || '评审失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    busy.value = ''
  }
}

// ---------- 工具 ----------
const undoAvailable = computed(() => undoStack.value.length > 0)

function undo() {
  const last = undoStack.value.pop()
  if (last !== undefined) content.value = last
}

function downloadTxt() {
  const blob = new Blob([content.value], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = '论文_修改稿.txt'
  link.click()
  URL.revokeObjectURL(link.href)
}

function copy() {
  navigator.clipboard.writeText(content.value)
    .then(() => showMsg('已复制全文', 'success')).catch(() => {})
}
</script>

<style scoped>
.revise-page { display: flex; flex-direction: column; gap: 1.25rem; }
.page-header { text-align: center; }
.page-header h1 { font-size: 1.7rem; color: var(--primary); margin-bottom: 0.4rem; }
.subtitle { color: var(--text-muted); font-size: 0.92rem; }

.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.4rem; }

.src-tabs { display: flex; gap: 0.5rem; margin-bottom: 0.9rem; }
.src-tab { flex: 1; padding: 0.5rem 0.9rem; border: 1px solid var(--border); background: none; border-radius: var(--radius); font-size: 0.92rem; cursor: pointer; color: var(--text-muted); }
.src-tab.active { border-color: var(--primary); color: var(--primary); font-weight: 600; background: var(--bg); }

.file-row { display: flex; align-items: center; gap: 0.75rem; margin-bottom: 0.8rem; flex-wrap: wrap; }

.textarea-field { width: 100%; padding: 0.7rem 0.85rem; border: 1px solid var(--border); border-radius: var(--radius); font-size: 0.92rem; font-family: inherit; resize: vertical; box-sizing: border-box; line-height: 1.65; }
.textarea-field.big { min-height: 260px; }
.textarea-field:focus { outline: none; border-color: var(--primary); }

.ops-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 1rem; }
.op-card h3 { margin: 0 0 0.3rem; font-size: 1.05rem; }
.op-desc { color: var(--text-muted); font-size: 0.85rem; margin: 0 0 0.7rem; }
.op-card .btn { margin-top: 0.7rem; }

.intensity-row { display: flex; gap: 0.4rem; }
.int-btn { flex: 1; padding: 0.4rem 0; border: 1px solid var(--border); background: none; border-radius: var(--radius); font-size: 0.88rem; cursor: pointer; color: var(--text-muted); }
.int-btn.active { border-color: var(--primary); color: var(--primary); font-weight: 600; background: var(--bg); }

.report-box { margin-top: 0.9rem; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; white-space: pre-wrap; line-height: 1.65; font-size: 0.88rem; max-height: 420px; overflow-y: auto; }

.toolbar { display: flex; gap: 0.7rem; align-items: center; flex-wrap: wrap; }

.btn { padding: 0.55rem 1.05rem; border: 1px solid var(--border); background: var(--card); border-radius: var(--radius); font-size: 0.88rem; cursor: pointer; text-decoration: none; display: inline-block; }
.btn-primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { font-size: 0.82rem; color: var(--text-muted); }
.msg { padding: 0.8rem 1rem; border-radius: var(--radius); font-size: 0.9rem; }
.msg.error { background: #fee; color: #c33; border: 1px solid #fcc; }
.msg.success { background: #efe; color: #3c3; border: 1px solid #cfc; }
.msg.warning { background: #ffc; color: #963; border: 1px solid #fc9; }
</style>
