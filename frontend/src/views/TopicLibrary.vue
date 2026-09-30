<template>
  <div class="topics-page">
    <div class="page-header">
      <h1>💡 论文选题库</h1>
      <p class="subtitle">基于浙江省教育教学论文评选 2024-2025 年度 {{ facets.total || '...' }} 条幼教获奖选题，帮你找方向、定题目</p>
    </div>

    <!-- AI 选题助手 -->
    <div class="card suggest-card">
      <h3>🤖 AI 选题助手</h3>
      <p class="text-muted">说说你的方向或兴趣，AI 结合获奖趋势给你推荐选题（含理由和切入场景）</p>

      <div class="form-row">
        <div class="form-group grow">
          <label>研究方向 / 兴趣</label>
          <input
            v-model="suggestForm.direction"
            type="text"
            placeholder="例如：户外自主游戏、师幼互动、幼小衔接、低结构材料"
            class="input-field"
            @keyup.enter="suggest"
          />
        </div>
        <div class="form-group">
          <label>年龄段（可选）</label>
          <select v-model="suggestForm.age_group" class="input-field">
            <option value="">不限</option>
            <option>小班</option>
            <option>中班</option>
            <option>大班</option>
            <option>混龄</option>
          </select>
        </div>
      </div>

      <div class="form-group">
        <label>园所 / 学段情况（可选）</label>
        <input
          v-model="suggestForm.background"
          type="text"
          placeholder="例如：乡镇中心幼儿园，中班，正在做种植园地课程"
          class="input-field"
        />
      </div>

      <button @click="suggest" :disabled="suggesting || !suggestForm.direction.trim()" class="btn btn-primary">
        {{ suggesting ? '🤔 结合获奖趋势分析中（约半分钟）...' : '💡 给我推荐选题' }}
      </button>

      <div v-if="suggestion" class="suggestion-result">
        <div class="answer-content">{{ suggestion }}</div>
        <div v-if="referenced.length" class="ref-block">
          <div class="ref-title">参考的获奖选题（{{ referenced.length }}）</div>
          <span v-for="(r, i) in referenced" :key="i" class="ref-tag">
            《{{ r.title }}》{{ r.city }}·{{ r.award }}·{{ r.year }}
          </span>
        </div>
      </div>
      <div v-else-if="suggestError" class="msg error">{{ suggestError }}</div>
    </div>

    <!-- 筛选检索 -->
    <div class="card search-card">
      <h3>🔍 获奖选题检索</h3>
      <div class="form-row">
        <div class="form-group grow">
          <label>关键词</label>
          <input
            v-model="query.keyword"
            type="text"
            placeholder="标题 / 单位 / 作者，如：游戏、课程故事、鄞州"
            class="input-field"
            @keyup.enter="search"
          />
        </div>
        <div class="form-group">
          <label>年份</label>
          <select v-model="query.year" class="input-field" @change="resetPage">
            <option value="">全部</option>
            <option v-for="y in facets.years" :key="y">{{ y }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>奖级</label>
          <select v-model="query.award" class="input-field" @change="resetPage">
            <option value="">全部</option>
            <option v-for="a in facets.awards" :key="a">{{ a }}</option>
          </select>
        </div>
        <div class="form-group">
          <label>地市</label>
          <select v-model="query.city" class="input-field" @change="resetPage">
            <option value="">全部</option>
            <option v-for="c in facets.cities" :key="c">{{ c }}</option>
          </select>
        </div>
      </div>
      <div class="search-actions">
        <button @click="search" :disabled="loading" class="btn btn-primary">
          {{ loading ? '检索中...' : '🔍 检索' }}
        </button>
        <button @click="reset" class="btn">重置</button>
        <span v-if="total >= 0" class="total-hint">共 {{ total }} 条选题</span>
      </div>

      <!-- 结果列表 -->
      <div v-if="items.length" class="topic-list">
        <div v-for="(t, i) in items" :key="offset + i" class="topic-item">
          <div class="topic-title">
            <span :class="['award-badge', awardClass(t.award)]">{{ t.award }}</span>
            《{{ t.title }}》
          </div>
          <div class="topic-meta">
            <span>📍 {{ t.city }}</span>
            <span>📅 {{ t.year }}</span>
            <span>🏫 {{ t.unit }}</span>
            <span v-if="t.authors">✍️ {{ t.authors }}</span>
          </div>
        </div>
      </div>
      <div v-else-if="!loading && total === 0" class="no-results">未找到符合条件的选题，换个关键词试试</div>

      <!-- 分页 -->
      <div v-if="total > pageSize" class="pager">
        <button :disabled="offset === 0 || loading" @click="prev" class="btn">上一页</button>
        <span class="page-info">{{ page }} / {{ pageCount }}</span>
        <button :disabled="offset + pageSize >= total || loading" @click="next" class="btn">下一页</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API_BASE = '' // 同源请求：dev 走 vite 代理，生产与后端同域

const facets = ref({ years: [], awards: [], cities: [], total: 0 })
const query = ref({ keyword: '', year: '', award: '', city: '' })
const items = ref([])
const total = ref(-1)
const loading = ref(false)
const pageSize = 50
const offset = ref(0)

const page = computed(() => Math.floor(offset.value / pageSize) + 1)
const pageCount = computed(() => Math.ceil(total.value / pageSize) || 1)

function awardClass(award) {
  return { 一等奖: 'gold', 二等奖: 'silver', 三等奖: 'bronze' }[award] || ''
}

async function loadFacets() {
  try {
    const res = await fetch(`${API_BASE}/api/topics/facets`)
    const data = await res.json()
    if (data.success) facets.value = data
  } catch (e) {
    console.error('加载筛选项失败', e)
  }
}

async function search() {
  loading.value = true
  try {
    const res = await fetch(`${API_BASE}/api/topics/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ ...query.value, limit: pageSize, offset: offset.value })
    })
    const data = await res.json()
    if (data.success) {
      items.value = data.items
      total.value = data.total
    }
  } catch (e) {
    console.error('检索失败', e)
  } finally {
    loading.value = false
  }
}

function reset() {
  query.value = { keyword: '', year: '', award: '', city: '' }
  offset.value = 0
  search()
}

// 改筛选条件时回到第 1 页，避免停在高页码看到空结果
function resetPage() {
  offset.value = 0
  search()
}

function prev() { offset.value = Math.max(0, offset.value - pageSize); search() }
function next() { offset.value += pageSize; search() }

// AI 选题建议
const suggestForm = ref({ direction: '', background: '', age_group: '' })
const suggesting = ref(false)
const suggestion = ref('')
const referenced = ref([])
const suggestError = ref('')

async function suggest() {
  if (!suggestForm.value.direction.trim()) return
  suggesting.value = true
  suggestion.value = ''
  referenced.value = []
  suggestError.value = ''
  try {
    const res = await fetch(`${API_BASE}/api/topics/suggest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(suggestForm.value)
    })
    const data = await res.json()
    if (data.success) {
      suggestion.value = data.suggestion
      referenced.value = data.referenced || []
    } else {
      suggestError.value = data.error || '生成失败，请重试'
    }
  } catch (e) {
    suggestError.value = '请求出错: ' + e.message
  } finally {
    suggesting.value = false
  }
}

onMounted(() => {
  loadFacets()
  search()
})
</script>

<style scoped>
.topics-page { display: flex; flex-direction: column; gap: 1.5rem; }
.page-header { text-align: center; }
.page-header h1 { font-size: 1.8rem; color: var(--primary); margin-bottom: 0.5rem; }
.subtitle { color: var(--text-muted); font-size: 0.95rem; }

.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; }
.card h3 { margin: 0 0 0.5rem; font-size: 1.1rem; color: var(--text); }
.text-muted { color: var(--text-muted); font-size: 0.9rem; margin-bottom: 1rem; }

.form-row { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 0.8rem; }
.form-row .grow { grid-column: span 2; }
.form-group { margin-bottom: 0.8rem; }
.form-group label { display: block; margin-bottom: 0.4rem; font-weight: 500; font-size: 0.85rem; }
.input-field {
  width: 100%; padding: 0.55rem 0.75rem; border: 1px solid var(--border);
  border-radius: var(--radius); font-size: 0.92rem; box-sizing: border-box;
}
.input-field:focus { outline: none; border-color: var(--primary); }

.btn {
  padding: 0.6rem 1.1rem; border: 1px solid var(--border); background: var(--card);
  border-radius: var(--radius); font-size: 0.9rem; cursor: pointer; transition: all 0.2s;
}
.btn-primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }

.suggestion-result { margin-top: 1.25rem; }
.answer-content {
  background: var(--bg); border-radius: var(--radius); padding: 1rem;
  line-height: 1.7; white-space: pre-wrap; color: var(--text); max-height: 420px; overflow-y: auto;
}
.ref-block { margin-top: 0.8rem; }
.ref-title { font-size: 0.85rem; color: var(--text-muted); margin-bottom: 0.4rem; }
.ref-tag {
  display: inline-block; background: var(--bg); border: 1px solid var(--border);
  border-radius: 999px; padding: 0.2rem 0.7rem; font-size: 0.8rem; margin: 0.2rem 0.3rem 0.2rem 0; color: var(--text-muted);
}

.search-actions { display: flex; align-items: center; gap: 0.75rem; margin: 0.5rem 0 1rem; }
.total-hint { font-size: 0.88rem; color: var(--text-muted); }

.topic-list { display: flex; flex-direction: column; gap: 0.6rem; }
.topic-item {
  background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 0.75rem 1rem; transition: border-color 0.2s;
}
.topic-item:hover { border-color: var(--primary); }
.topic-title { font-size: 0.95rem; line-height: 1.5; color: var(--text); }
.award-badge {
  display: inline-block; font-size: 0.75rem; border-radius: 999px; padding: 0.1rem 0.55rem; margin-right: 0.5rem; color: #fff;
}
.award-badge.gold { background: #d4a017; }
.award-badge.silver { background: #8a959e; }
.award-badge.bronze { background: #b0734c; }
.topic-meta { display: flex; flex-wrap: wrap; gap: 0.9rem; font-size: 0.8rem; color: var(--text-muted); margin-top: 0.35rem; }

.no-results { text-align: center; padding: 2rem; color: var(--text-muted); background: var(--bg); border-radius: var(--radius); }

.pager { display: flex; align-items: center; justify-content: center; gap: 1rem; margin-top: 1rem; }
.page-info { font-size: 0.9rem; color: var(--text-muted); }

.msg.error { background: #fee; color: #c33; border: 1px solid #fcc; border-radius: var(--radius); padding: 0.8rem 1rem; margin-top: 1rem; font-size: 0.9rem; }

@media (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
  .form-row .grow { grid-column: span 1; }
}
</style>
