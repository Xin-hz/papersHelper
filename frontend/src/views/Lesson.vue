<template>
  <div>
    <h1 style="margin: 0 0 0.5rem;">教案生成</h1>
    <p class="text-muted" style="margin: 0 0 1rem;">填写课程名称、适合年龄与课程目标，生成完整教案</p>
    <div class="card">
      <label>课程名称 *</label>
      <input v-model="form.topic" type="text" placeholder="例如：认识四季" />
      <label>适合年龄</label>
      <select v-model="form.grade">
        <option value="">请选择</option>
        <option value="小班">小班</option>
        <option value="中班">中班</option>
        <option value="大班">大班</option>
      </select>
      <label>课程目标</label>
      <textarea v-model="form.goal" rows="3" placeholder="如：初步感知四季特征，愿意用语言表达…"></textarea>
      <div class="checkbox-wrap">
        <input id="rag" v-model="form.use_rag" type="checkbox" />
        <label for="rag" style="margin:0">结合知识库</label>
      </div>
      <button class="btn" :disabled="loading" @click="submit">{{ loading ? '生成中…' : '生成教案' }}</button>
    </div>
    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
    <div v-if="result" class="card">
      <h2>教案 <button class="btn btn-secondary copy-btn" @click="copy(result)">复制</button></h2>
      <div class="result-box">{{ result }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api, friendlyError } from '../api'

const form = reactive({ topic: '', grade: '', goal: '', use_rag: true })
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
  if (!form.topic.trim()) return showMsg('请填写教学主题')
  loading.value = true
  result.value = ''
  try {
    const res = await api.generateLessonPlan({
      topic: form.topic,
      grade: form.grade || undefined,
      goal: form.goal || undefined,
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
