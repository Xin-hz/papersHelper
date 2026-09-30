<template>
  <div>
    <h1 style="margin: 0 0 0.5rem;">论文</h1>
    <p class="text-muted" style="margin: 0 0 1rem;">生成、润色、扩写、降重</p>
    <div class="tabs">
      <button v-for="t in tabs" :key="t.id" :class="{ active: tab === t.id }" @click="tab = t.id">{{ t.label }}</button>
    </div>
    <div class="card">
      <!-- 生成 -->
      <template v-if="tab === 'generate'">
        <label>论文标题 / 主题 *</label>
        <input v-model="form.title" type="text" placeholder="例如：幼儿园区域活动中教师指导策略研究" />
        <label>研究方向（可选）</label>
        <input v-model="form.direction" type="text" placeholder="如：游戏化教学、家园共育" />
        <label>字数要求（可选）</label>
        <input v-model="form.words" type="text" placeholder="如：3000字、5000字" />
        <label>可选大纲</label>
        <textarea v-model="form.outline" placeholder="一、引言 二、文献综述 三、研究方法 四、结果与讨论 五、结论"></textarea>
        <div class="checkbox-wrap">
          <input id="r1" v-model="form.use_rag" type="checkbox" />
          <label for="r1" style="margin:0">结合知识库</label>
        </div>
        <div class="docx-actions">
          <button class="btn" :disabled="loading || docxLoading" @click="submit">{{ submitLabel }}</button>
          <button class="btn btn-primary" :disabled="loading || docxLoading || !form.title.trim()" @click="generateDocx">
            {{ docxLoading ? docxLabel : '📄 生成图文排版 Word' }}
          </button>
        </div>
        <p v-if="docxLoading || docxMsg" :class="['msg', docxMsgType]">{{ docxLoading ? docxLabel : docxMsg }}</p>
        <div v-if="docxResult" class="card docx-result">
          <h2>文档已生成（约 {{ docxResult.words }} 字）</h2>
          <p class="text-muted">
            含 {{ docxResult.stats.charts }} 张图、{{ docxResult.stats.table }} 张表、参考文献 {{ docxResult.stats.refs }} 条
          </p>
          <div class="result-actions">
            <a class="btn btn-primary" :href="docxHref" :download="docxResult.filename">📥 下载 Word 文档</a>
          </div>
        </div>
      </template>
      <!-- 润色 -->
      <template v-if="tab === 'improve'">
        <label>待润色内容 *</label>
        <textarea v-model="form.content" placeholder="粘贴论文段落或全文"></textarea>
        <label>润色侧重点（可选）</label>
        <input v-model="form.focus" type="text" placeholder="如：学术性、语言流畅" />
      </template>
      <!-- 扩写 -->
      <template v-if="tab === 'expand'">
        <label>待扩写内容 *</label>
        <textarea v-model="form.content" placeholder="粘贴需要扩写的段落或全文"></textarea>
        <label>目标字数（可选）</label>
        <input v-model="form.target_words" type="text" placeholder="如：3000字、5000字" />
        <div class="checkbox-wrap">
          <input id="r2" v-model="form.use_rag" type="checkbox" />
          <label for="r2" style="margin:0">结合知识库</label>
        </div>
      </template>
      <!-- 降重 -->
      <template v-if="tab === 'reduce'">
        <label>待降重内容 *</label>
        <textarea v-model="form.content" placeholder="粘贴需要降重的段落"></textarea>
        <label>降重侧重点（可选）</label>
        <input v-model="form.focus" type="text" placeholder="如：同义替换、句式改写" />
      </template>
      <button v-if="tab !== 'generate'" class="btn" :disabled="loading" @click="submit">{{ submitLabel }}</button>
    </div>
    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
    <div v-if="result" class="card">
      <h2>结果（约 {{ result.length }} 字）
        <span class="result-actions">
          <button class="btn btn-secondary copy-btn" @click="copy(result)">复制</button>
          <button class="btn btn-secondary copy-btn" @click="download(result)">下载 .txt</button>
          <button v-if="tab === 'generate'" class="btn btn-secondary copy-btn" @click="sendTo('improve')">送去润色</button>
          <button v-if="tab === 'generate'" class="btn btn-secondary copy-btn" @click="sendTo('reduce')">送去降重</button>
        </span>
      </h2>
      <div class="result-box">{{ result }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, computed } from 'vue'
import { api, friendlyError } from '../api'

const tab = ref('generate')
const tabs = [
  { id: 'generate', label: '生成' },
  { id: 'improve', label: '润色' },
  { id: 'expand', label: '扩写' },
  { id: 'reduce', label: '降重' },
]
const form = reactive({
  title: '',
  outline: '',
  direction: '',
  words: '',
  content: '',
  focus: '',
  target_words: '',
  target_section: '',
  use_rag: true,
})
const loading = ref(false)
const result = ref('')
const msg = ref(null)

const submitLabel = computed(() => {
  if (!loading.value) return '提交'
  if (tab.value === 'generate') return '生成中…多阶段生成约需 5-10 分钟（网络与模型速度相关），请勿关闭页面'
  return '处理中…'
})

function showMsg(text, type = 'error') {
  msg.value = { text: friendlyError(text), type }
  setTimeout(() => { msg.value = null }, 5000)
}
function copy(text) {
  navigator.clipboard.writeText(text).then(() => showMsg('已复制', 'success')).catch(() => {})
}
function download(text) {
  const name = tab.value === 'generate' ? `${form.title || '论文'}.txt` : '结果.txt'
  const blob = new Blob([text], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = name.replace(/[\\/:*?"<>|]/g, '_')
  link.click()
  URL.revokeObjectURL(link.href)
}
// 把生成结果带入润色/降重标签页，接续处理
function sendTo(target) {
  form.content = result.value
  result.value = ''
  tab.value = target
  showMsg('已带入内容，可直接提交', 'success')
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// 图文排版 Word 生成
const docxLoading = ref(false)
const docxResult = ref(null)
const docxMsg = ref('')
const docxMsgType = ref('info')
const docxStart = ref(0)
const docxTimer = ref(null)
const elapsed = ref(0)
const docxLabel = computed(() =>
  `📄 排版生成中…约需 5-10 分钟（已进行 ${Math.floor(elapsed.value / 60)} 分 ${elapsed.value % 60} 秒），请勿关闭页面`
)
const docxHref = computed(() =>
  docxResult.value ? `/api/download/${encodeURIComponent(docxResult.value.filename)}` : ''
)

async function generateDocx() {
  if (!form.title.trim()) return showMsg('请填写标题')
  docxLoading.value = true
  docxResult.value = null
  docxMsg.value = ''
  elapsed.value = 0
  docxStart.value = Date.now()
  docxTimer.value = setInterval(() => { elapsed.value = Math.floor((Date.now() - docxStart.value) / 1000) }, 1000)
  try {
    const res = await fetch('/api/paper/generate_docx', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: form.title,
        direction: form.direction || undefined,
        use_rag: form.use_rag,
      }),
    })
    const data = await res.json()
    if (data.success) {
      docxResult.value = data
    } else {
      docxMsg.value = data.error || '生成失败，请重试'
      docxMsgType.value = 'error'
    }
  } catch (e) {
    docxMsg.value = '请求出错: ' + e.message
    docxMsgType.value = 'error'
  } finally {
    clearInterval(docxTimer.value)
    docxLoading.value = false
  }
}

async function submit() {
  if (tab.value === 'generate' && !form.title.trim()) return showMsg('请填写标题')
  if ((tab.value === 'improve' || tab.value === 'expand' || tab.value === 'reduce') && !form.content.trim()) return showMsg('请填写内容')
  loading.value = true
  result.value = ''
  try {
    let res
    if (tab.value === 'generate') res = await api.generatePaper({
      title: form.title,
      outline: form.outline || undefined,
      direction: form.direction || undefined,
      words: form.words || undefined,
      use_rag: form.use_rag,
    })
    else if (tab.value === 'improve') res = await api.improvePaper({ content: form.content, focus: form.focus || undefined })
    else if (tab.value === 'expand') res = await api.expandPaper({
      content: form.content,
      target_words: form.target_words || undefined,
      target_section: form.target_section || undefined,
      use_rag: form.use_rag,
    })
    else res = await api.reduceWeight({ content: form.content, focus: form.focus || undefined })
    if (res.success) result.value = res.content
    else showMsg(res.content || '请求失败')
  } catch (e) {
    showMsg(e.message || '请求失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.text-muted { color: var(--text-muted); }
.result-actions { display: inline-flex; gap: 0.5rem; margin-left: 0.75rem; flex-wrap: wrap; }
.docx-actions { display: flex; gap: 0.75rem; margin-top: 0.75rem; flex-wrap: wrap; }
.docx-result { margin-top: 1rem; }
.docx-result h2 { font-size: 1.05rem; margin: 0 0 0.4rem; }
.docx-result .result-actions { margin-left: 0; margin-top: 0.6rem; }
.msg.info { background: #eef; color: #334; border: 1px solid #ccd; }
</style>
