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
      <button class="btn" :disabled="loading" @click="submit">{{ loading ? '处理中…' : '提交' }}</button>
    </div>
    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
    <div v-if="result" class="card">
      <h2>结果 <button class="btn btn-secondary copy-btn" @click="copy(result)">复制</button></h2>
      <div class="result-box">{{ result }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

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

function showMsg(text, type = 'error') {
  msg.value = { text, type }
  setTimeout(() => { msg.value = null }, 5000)
}
function copy(text) {
  navigator.clipboard.writeText(text).then(() => showMsg('已复制', 'success')).catch(() => {})
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
</style>
