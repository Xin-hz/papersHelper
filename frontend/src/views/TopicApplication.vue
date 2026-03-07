<template>
  <div>
    <h1 style="margin: 0 0 0.5rem;">课题申报</h1>
    <p class="text-muted" style="margin: 0 0 1rem;">填写课题名称与研究方向，生成教育科研课题申报书（评职称用）</p>
    <div class="card">
      <label>课题名称 *</label>
      <input v-model="form.topic" type="text" placeholder="例如：幼儿园游戏化教学的实践研究" />
      <label>研究方向（可选）</label>
      <input v-model="form.direction" type="text" placeholder="如：游戏化教学、家园共育" />
      <div class="checkbox-wrap">
        <input id="rag" v-model="form.use_rag" type="checkbox" />
        <label for="rag" style="margin:0">结合知识库</label>
      </div>
      <button class="btn" :disabled="loading" @click="submit">{{ loading ? '生成中…' : '生成课题申报书' }}</button>
    </div>
    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
    <div v-if="result" class="card">
      <h2>课题申报书 <button class="btn btn-secondary copy-btn" @click="copy(result)">复制</button></h2>
      <div class="result-box">{{ result }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

const form = reactive({ topic: '', direction: '', use_rag: true })
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
  if (!form.topic.trim()) return showMsg('请填写课题名称')
  loading.value = true
  result.value = ''
  try {
    const res = await api.topicApplication({
      topic: form.topic,
      direction: form.direction || undefined,
      use_rag: form.use_rag,
    })
    if (res.success) result.value = res.content
    else showMsg(res.content || '生成失败')
  } catch (e) {
    showMsg(e.message || '生成失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.text-muted { color: var(--text-muted); }
</style>
