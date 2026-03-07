<template>
  <div>
    <h1 style="margin: 0 0 0.5rem;">知识库</h1>
    <p class="text-muted" style="margin: 0 0 1rem;">上传 PDF / DOCX / DOC 后即可进行智能问答；多选将逐个上传并显示进度，建议单次不超过 5 个</p>

    <div class="card">
      <h2>上传文件</h2>
      <input ref="fileRef" type="file" accept=".pdf,.docx,.doc" multiple @change="onFileChange" />
      <button class="btn" :disabled="uploading" style="margin-top:0.5rem" @click="upload">{{ uploadLabel }}</button>
      <div v-if="uploadProgress" class="text-muted" style="margin-top:0.5rem;font-size:0.9rem">{{ uploadProgress }}</div>
      <div v-if="uploadMsg" :class="['msg', uploadMsg.type]" style="margin-top:1rem">{{ uploadMsg.text }}</div>
    </div>

    <div class="card">
      <h2>知识库问答</h2>
      <label>输入问题</label>
      <textarea v-model="question" placeholder="例如：幼儿园游戏化教学有哪些常见策略？" rows="3"></textarea>
      <label>检索条数（可选）</label>
      <input v-model.number="topK" type="number" min="1" max="20" style="width:80px" />
      <button class="btn" :disabled="loading" @click="ask">{{ loading ? '查询中…' : '提问' }}</button>
    </div>
    <div v-if="askMsg" :class="['msg', askMsg.type]">{{ askMsg.text }}</div>
    <div v-if="answer !== null" class="card">
      <h2>回答 <button class="btn btn-secondary copy-btn" @click="copy(answer)">复制</button></h2>
      <div class="result-box">{{ answer }}</div>
      <details v-if="sources.length" class="sources-list">
        <summary>引用来源 ({{ sources.length }})</summary>
        <ul>
          <li v-for="(s, i) in sources" :key="i">{{ s.slice(0, 150) }}{{ s.length > 150 ? '…' : '' }}</li>
        </ul>
      </details>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { api } from '../api'

const fileRef = ref(null)
let selectedFiles = []
function onFileChange(e) {
  selectedFiles = e.target.files ? Array.from(e.target.files) : []
}

const uploading = ref(false)
const uploadMsg = ref(null)
const uploadProgress = ref('')
const uploadLabel = ref('上传')

async function upload() {
  if (!selectedFiles.length) return (uploadMsg.value = { text: '请先选择文件', type: 'error' })
  uploading.value = true
  uploadMsg.value = null
  uploadProgress.value = ''
  let totalChunks = 0
  let okCount = 0
  const total = selectedFiles.length
  for (let i = 0; i < total; i++) {
    uploadProgress.value = `正在上传 ${i + 1}/${total}…`
    uploadLabel.value = `上传中 ${i + 1}/${total}`
    try {
      const res = await api.uploadKnowledge([selectedFiles[i]])
      if (res.success) {
        okCount += 1
        const m = res.message || ''
        const n = m.match(/共\s*(\d+)\s*个片段/)
        if (n) totalChunks += parseInt(n[1], 10)
      }
    } catch (_) {}
  }
  uploadProgress.value = ''
  uploadLabel.value = '上传'
  uploading.value = false
  if (okCount === total) {
    uploadMsg.value = { text: `共成功上传 ${okCount} 个文件，累计 ${totalChunks} 个片段`, type: 'success' }
  } else if (okCount > 0) {
    uploadMsg.value = { text: `成功 ${okCount}/${total} 个文件，共 ${totalChunks} 个片段`, type: 'success' }
  } else {
    uploadMsg.value = { text: '上传失败，请检查格式与网络', type: 'error' }
  }
  if (fileRef.value) fileRef.value.value = ''
  selectedFiles = []
}

const question = ref('')
const topK = ref(5)
const loading = ref(false)
const answer = ref(null)
const sources = ref([])
const askMsg = ref(null)

function copy(text) {
  navigator.clipboard.writeText(text).then(() => { askMsg.value = { text: '已复制', type: 'success' }; setTimeout(() => { askMsg.value = null }, 2000) }).catch(() => {})
}

async function ask() {
  if (!question.value.trim()) return (askMsg.value = { text: '请输入问题', type: 'error' })
  loading.value = true
  answer.value = null
  sources.value = []
  askMsg.value = null
  try {
    const res = await api.askKnowledge({
      question: question.value,
      top_k: topK.value ?? undefined,
    })
    if (res.success) {
      answer.value = res.answer
      sources.value = res.sources || []
    } else askMsg.value = { text: res.answer || '查询失败', type: 'error' }
  } catch (e) {
    askMsg.value = { text: e.message || '查询失败', type: 'error' }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.text-muted { color: var(--text-muted); }
</style>
