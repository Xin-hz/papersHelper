<template>
  <div>
    <h1 style="margin: 0 0 0.5rem;">教学案例生成</h1>
    <p class="text-muted" style="margin: 0 0 1rem;">填写活动名称、年龄段与活动目标，生成完整教学案例</p>
    <div class="card">
      <label>活动名称 *</label>
      <input v-model="form.topic" type="text" placeholder="例如：区域活动中幼儿争抢材料" />
      <label>年龄段</label>
      <input v-model="form.age" type="text" placeholder="如：大班、中班、小班" />
      <label>活动目标</label>
      <textarea v-model="form.goal" rows="3" placeholder="如：能友好协商、愿意轮流使用材料…"></textarea>
      <div class="checkbox-wrap">
        <input id="rag" v-model="form.use_rag" type="checkbox" />
        <label for="rag" style="margin:0">结合知识库</label>
      </div>
      <button class="btn" :disabled="loading" @click="submit">{{ loading ? '生成中…' : '生成教学案例' }}</button>
    </div>
    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
    <div v-if="result" class="card">
      <h2>教学案例 <button class="btn btn-secondary copy-btn" @click="copy(result)">复制</button></h2>
      <div class="result-box">{{ result }}</div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { api } from '../api'

const form = reactive({ topic: '', age: '', goal: '', use_rag: true })
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
  if (!form.topic.trim()) return showMsg('请填写案例主题')
  loading.value = true
  result.value = ''
  try {
    const res = await api.generateTeachingCase({
      topic: form.topic,
      age: form.age || undefined,
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
