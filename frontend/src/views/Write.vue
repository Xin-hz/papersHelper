<template>
  <div class="write-page">
    <div class="page-header">
      <h1>✍️ 写论文</h1>
      <p class="subtitle">借鉴获奖选题 → 检索资料 → 定提纲 → 补充素材正式撰写，一条流程走完</p>
    </div>

    <!-- 步骤条 -->
    <div class="stepper card">
      <div
        v-for="(s, i) in steps"
        :key="s.key"
        :class="['step', { active: step === i + 1, done: stepDone(i + 1) }]"
        @click="step = i + 1"
      >
        <span class="step-num">{{ stepDone(i + 1) && step !== i + 1 ? '✓' : i + 1 }}</span>
        <span class="step-label">{{ s.label }}</span>
      </div>
    </div>

    <!-- ① 选题：借鉴获奖案例 -->
    <div v-if="step === 1" class="card step-card">
      <h3>① 选题 <span class="sub-h">借鉴往届获奖案例</span></h3>
      <div class="form-group">
        <label>论文标题 / 主题 *</label>
        <input v-model="title" type="text" class="input-field" placeholder="例如：大班户外自主游戏中教师观察与支持策略研究" />
      </div>
      <div class="form-row">
        <div class="form-group">
          <label>研究方向（可选）</label>
          <input v-model="direction" type="text" class="input-field" placeholder="如：户外自主游戏、低结构材料" />
        </div>
        <div class="form-group">
          <label>预计字数（可选）</label>
          <input v-model="words" type="text" class="input-field" placeholder="如：3000字（评选上限4000字）" />
        </div>
      </div>

      <div class="sub-box">
        <div class="sub-title">从获奖选题库找参考（2024-2025 浙江 1459 条）</div>
        <div class="inline-row">
          <input v-model="topicKw" type="text" class="input-field" placeholder="关键词，如：自主游戏、材料投放、课程故事"
                 @keyup.enter="searchTopics" />
          <button class="btn" :disabled="topicSearching" @click="searchTopics">{{ topicSearching ? '搜索中…' : '搜索' }}</button>
        </div>
        <div v-if="topicResults.length" class="topic-hits">
          <div v-for="(t, i) in topicResults" :key="i" class="topic-hit" @click="adoptTopic(t)">
            <span :class="['badge', awardClass(t.award)]">{{ t.award }}</span>
            <span class="hit-title">《{{ t.title }}》</span>
            <span class="hit-meta">{{ t.city }} · {{ t.year }} · {{ t.unit }}</span>
          </div>
          <p class="hint">点击带入标题参考，建议改写为自己的题目</p>
        </div>
      </div>

      <div class="sub-box">
        <div class="sub-title">让 AI 结合获奖趋势推荐选题</div>
        <div class="inline-row">
          <input v-model="suggestDir" type="text" class="input-field" placeholder="你的方向/兴趣，如：户外游戏 材料投放"
                 @keyup.enter="suggest" />
          <button class="btn" :disabled="suggesting" @click="suggest">{{ suggesting ? '分析中…约1分钟' : '推荐选题' }}</button>
        </div>
        <div v-if="suggestTitles.length" class="chips">
          <button v-for="(t, i) in suggestTitles" :key="i" class="chip" @click="adoptSuggested(t)">《{{ t }}》</button>
        </div>
        <details v-if="suggestionText" class="suggest-detail">
          <summary>查看完整推荐理由</summary>
          <div class="suggest-text">{{ suggestionText }}</div>
        </details>
      </div>

      <button class="btn btn-primary" :disabled="!title.trim()" @click="step = 2">下一步：检索资料 →</button>
    </div>

    <!-- ② 资料：基于选题检索知识库 -->
    <div v-if="step === 2" class="card step-card">
      <h3>② 资料 <span class="sub-h">基于选题检索知识库</span></h3>
      <p class="brief">选题：《{{ title || '（未填写）' }}》<a class="edit-link" @click="step = 1">修改</a></p>

      <div class="inline-row">
        <input v-model="refKw" type="text" class="input-field" placeholder="检索词（默认用选题自动检索）" @keyup.enter="searchRefs" />
        <button class="btn" :disabled="refSearching" @click="searchRefs">{{ refSearching ? '检索中…' : '🔍 检索知识库' }}</button>
      </div>

      <div v-if="refHits.length" class="ref-list">
        <label v-for="(r, i) in refHits" :key="i" class="ref-item">
          <input type="checkbox" v-model="r.checked" />
          <div class="ref-body">
            <div class="ref-source">📄 {{ r.source }} <span class="ref-score">相关度 {{ (r.score * 100).toFixed(0) }}%</span></div>
            <div class="ref-snippet">{{ r.snippet }}</div>
          </div>
        </label>
      </div>
      <div v-else-if="!refSearching && refSearched" class="no-results">
        知识库中没有相关资料——可去 <router-link to="/knowledge">知识库</router-link> 上传你的文档，或用"论文采集"补充
      </div>

      <p class="hint">勾选的资料将作为写作素材（已选 {{ checkedRefs.length }}/{{ refHits.length }} 条）；不检索也可继续，撰写时会自动检索。</p>
      <div class="step-nav">
        <button class="btn" @click="step = 1">← 上一步</button>
        <button class="btn btn-primary" @click="step = 3">下一步：生成提纲 →</button>
      </div>
    </div>

    <!-- ③ 提纲 -->
    <div v-if="step === 3" class="card step-card">
      <h3>③ 提纲 <span class="sub-h">生成后可自由修改</span></h3>
      <p class="brief">基于选题与选定资料生成提纲，改到你满意再正式撰写</p>
      <button class="btn" :disabled="outlineLoading" @click="genOutline">
        {{ outlineLoading ? '生成中…约1分钟' : (outline ? '🔄 重新生成提纲' : '📝 生成提纲') }}
      </button>
      <textarea v-model="outline" class="textarea-field" rows="9" placeholder="点上方按钮生成，或直接手动编写：每行一章，如「一、研究背景与问题提出」"></textarea>
      <p class="hint">每行一章（4-6 章为宜），正文将严格按此提纲撰写</p>
      <div class="step-nav">
        <button class="btn" @click="step = 2">← 上一步</button>
        <button class="btn btn-primary" :disabled="!outline.trim()" @click="step = 4">下一步：正式撰写 →</button>
      </div>
    </div>

    <!-- ④ 撰写与导出 -->
    <div v-if="step === 4" class="card step-card">
      <h3>④ 撰写 <span class="sub-h">补充真实素材后正式编写</span></h3>
      <p class="brief">提纲 {{ outlineLines }} 章 · 素材 {{ checkedRefs.length }} 条<a class="edit-link" @click="step = 3">改提纲</a><a class="edit-link" @click="step = 2">改素材</a></p>

      <div class="form-group">
        <label>补充真实素材（强烈建议：班级情况、幼儿人数、真实数据、你经历过的案例——写进去才不像 AI 空文）</label>
        <textarea v-model="notes" class="textarea-field" rows="4" placeholder="例如：我带的小班有 28 人；上学期开展了娃娃家游戏，观察到幼儿常争抢仿真餐具；我们 10 月投放了纸箱和布料，乐乐用纸箱当了烤箱……"></textarea>
      </div>
      <label class="checkbox-wrap">
        <input v-model="useRag" type="checkbox" /> 结合知识库（参考文献取自知识库真实文献）
      </label>

      <div class="gen-actions">
        <button class="btn" :disabled="anyBusy" @click="quickGenerate">
          {{ generating ? '撰写中…约5-10分钟' : '⚡ 撰写正文（纯文本）' }}
        </button>
        <button class="btn btn-primary" :disabled="anyBusy" @click="genDocx">
          {{ docxLoading ? docxLabel : '📄 撰写并排版成图文 Word' }}
        </button>
      </div>
      <p v-if="docxLoading" class="hint">{{ docxLabel }}</p>

      <div v-if="docxResult" class="docx-ok">
        ✅ 图文 Word 已生成（约 {{ docxResult.words }} 字）
        <a class="btn btn-primary" :href="docxHref" :download="docxResult.filename">📥 下载</a>
      </div>

      <div v-if="content" class="result-area">
        <div class="result-head">
          <span>正文约 {{ content.length }} 字</span>
          <span class="result-actions">
            <button class="btn btn-sm" @click="downloadTxt">📥 .txt</button>
            <button class="btn btn-sm" @click="copy">📋 复制</button>
            <button class="btn btn-sm btn-primary" @click="goRevise">去改论文（优化/降重/评审）→</button>
          </span>
        </div>
        <div class="result-box">{{ content }}</div>
      </div>
    </div>

    <div v-if="msg" :class="['msg', msg.type]">{{ msg.text }}</div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { api, friendlyError } from '../api'

const router = useRouter()
const steps = [
  { key: 'topic', label: '选题' },
  { key: 'refs', label: '资料' },
  { key: 'outline', label: '提纲' },
  { key: 'write', label: '撰写' },
]
const step = ref(1)

// 全程携带的状态
const title = ref('')
const direction = ref('')
const words = ref('')
const useRag = ref(true)
const notes = ref('')
const outline = ref('')
const content = ref('')
const docxResult = ref(null)

const outlineLines = computed(() => outline.value.split('\n').filter(l => l.trim()).length)

function stepDone(n) {
  if (n === 1) return !!title.value.trim()
  if (n === 2) return refSearched.value
  if (n === 3) return !!outline.value.trim()
  return !!content.value || !!docxResult.value
}

const msg = ref(null)
function showMsg(text, type = 'error') {
  msg.value = { text: friendlyError(text), type }
  setTimeout(() => { msg.value = null }, 5000)
}

// ---------- ① 选题 ----------
const topicKw = ref('')
const topicSearching = ref(false)
const topicResults = ref([])

async function searchTopics() {
  if (!topicKw.value.trim()) return
  topicSearching.value = true
  try {
    const d = await api.topicsSearch({ keyword: topicKw.value.trim(), limit: 8, offset: 0 })
    topicResults.value = d.items || []
    if (!topicResults.value.length) showMsg('没搜到相关获奖选题，换个关键词试试', 'warning')
  } catch (e) {
    showMsg('检索失败: ' + e.message)
  } finally {
    topicSearching.value = false
  }
}

function adoptTopic(t) {
  title.value = t.title
  if (!direction.value) direction.value = topicKw.value.trim()
  showMsg('已带入标题参考，建议结合自己班级情况改写', 'success')
}

const awardClass = (a) => ({ 一等奖: 'gold', 二等奖: 'silver', 三等奖: 'bronze' }[a] || '')

const suggestDir = ref('')
const suggesting = ref(false)
const suggestionText = ref('')
const suggestTitles = ref([])

async function suggest() {
  if (!suggestDir.value.trim()) return
  suggesting.value = true
  suggestionText.value = ''
  suggestTitles.value = []
  try {
    const d = await api.topicsSuggest({ direction: suggestDir.value.trim() })
    if (d.success) {
      suggestionText.value = d.suggestion
      suggestTitles.value = [...new Set([...d.suggestion.matchAll(/《([^》]{6,40})》/g)].map(m => m[1]))].slice(0, 6)
    } else {
      showMsg(d.error || '推荐失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    suggesting.value = false
  }
}

function adoptSuggested(t) {
  title.value = t
  showMsg('已采用推荐题目', 'success')
}

// ---------- ② 资料 ----------
const refKw = ref('')
const refSearching = ref(false)
const refSearched = ref(false)
const refHits = ref([]) // {source, snippet, score, checked}

async function searchRefs() {
  refSearching.value = true
  try {
    const query = refKw.value.trim() || title.value
    if (!query) return showMsg('请先在第①步填写选题')
    const d = await fetch('/api/knowledge/search', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query, top_k: 8 }),
    }).then(r => r.json())
    if (d.success) {
      refHits.value = (d.results || []).map(r => ({
        source: (r.metadata && r.metadata.source) || '未知来源',
        snippet: r.content.slice(0, 180),
        score: r.score,
        checked: true,
      }))
      refSearched.value = true
      if (!refHits.value.length) showMsg('知识库暂无相关资料，可先去上传文档', 'warning')
    } else {
      showMsg(d.message || '检索失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    refSearching.value = false
  }
}

const checkedRefs = computed(() => refHits.value.filter(r => r.checked))
const refsText = computed(() =>
  checkedRefs.value.map(r => `【${r.source}】${r.snippet}`).join('\n\n')
)

// ---------- ③ 提纲 ----------
const outlineLoading = ref(false)

async function genOutline() {
  if (!title.value.trim()) return showMsg('请先在第①步填写选题')
  outlineLoading.value = true
  try {
    const d = await api.generateOutline({
      title: title.value,
      direction: direction.value || undefined,
      use_rag: useRag.value,
      extra_context: checkedRefs.value.length ? refsText.value : undefined,
    })
    if (d.success) {
      outline.value = d.outline
      showMsg('提纲已生成，可直接修改', 'success')
    } else {
      showMsg(d.error || '生成失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    outlineLoading.value = false
  }
}

// ---------- ④ 撰写 ----------
const generating = ref(false)
const docxLoading = ref(false)
const elapsed = ref(0)
const docxTimer = ref(null)
const anyBusy = computed(() => generating.value || docxLoading.value)
const docxLabel = computed(() =>
  `生成中…约需 5-10 分钟（已进行 ${Math.floor(elapsed.value / 60)} 分 ${elapsed.value % 60} 秒），请勿关闭页面`
)
const docxHref = computed(() =>
  docxResult.value ? `/api/download/${encodeURIComponent(docxResult.value.filename)}` : ''
)

async function quickGenerate() {
  if (!title.value.trim()) return showMsg('请先填写选题')
  generating.value = true
  try {
    const d = await api.generatePaper({
      title: title.value,
      outline: outline.value || undefined,
      direction: direction.value || undefined,
      words: words.value || undefined,
      use_rag: useRag.value,
      extra_context: checkedRefs.value.length ? refsText.value : undefined,
      notes: notes.value || undefined,
    })
    if (d.success) {
      content.value = d.content
      showMsg('撰写完成', 'success')
    } else {
      showMsg(d.content || '生成失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    generating.value = false
  }
}

async function genDocx() {
  if (!title.value.trim()) return showMsg('请先填写选题')
  docxLoading.value = true
  docxResult.value = null
  elapsed.value = 0
  const start = Date.now()
  docxTimer.value = setInterval(() => { elapsed.value = Math.floor((Date.now() - start) / 1000) }, 1000)
  try {
    const d = await api.generateDocx({
      title: title.value,
      direction: direction.value || undefined,
      use_rag: useRag.value,
    })
    if (d.success) {
      docxResult.value = d
      showMsg('图文 Word 已生成', 'success')
    } else {
      showMsg(d.error || '生成失败')
    }
  } catch (e) {
    showMsg('请求出错: ' + e.message)
  } finally {
    clearInterval(docxTimer.value)
    docxLoading.value = false
  }
}

// ---------- 导出与流转 ----------
function downloadTxt() {
  const name = `${title.value || '论文'}.txt`.replace(/[\\/:*?"<>|]/g, '_')
  const blob = new Blob([content.value], { type: 'text/plain;charset=utf-8' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = name
  link.click()
  URL.revokeObjectURL(link.href)
}

function copy() {
  navigator.clipboard.writeText(content.value)
    .then(() => showMsg('已复制全文', 'success')).catch(() => {})
}

function goRevise() {
  sessionStorage.setItem('revise_content', content.value)
  router.push('/revise')
}
</script>

<style scoped>
.write-page { display: flex; flex-direction: column; gap: 1.25rem; }
.page-header { text-align: center; }
.page-header h1 { font-size: 1.7rem; color: var(--primary); margin-bottom: 0.4rem; }
.subtitle { color: var(--text-muted); font-size: 0.92rem; }

.stepper { display: flex; gap: 0.5rem; padding: 0.9rem 1.1rem; flex-wrap: wrap; }
.step { display: flex; align-items: center; gap: 0.45rem; padding: 0.4rem 0.9rem; border-radius: 999px; cursor: pointer; border: 1px solid var(--border); color: var(--text-muted); flex: 1; justify-content: center; min-width: 110px; transition: all 0.2s; }
.step.active { border-color: var(--primary); color: var(--primary); font-weight: 600; background: var(--bg); }
.step.done { color: var(--text); }
.step-num { display: inline-flex; align-items: center; justify-content: center; width: 1.35rem; height: 1.35rem; border-radius: 50%; border: 1px solid currentColor; font-size: 0.8rem; }

.card { background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); padding: 1.5rem; }
.step-card h3 { margin: 0 0 0.9rem; font-size: 1.1rem; }
.sub-h { font-size: 0.82rem; color: var(--text-muted); font-weight: 400; margin-left: 0.4rem; }
.brief { color: var(--text-muted); font-size: 0.92rem; margin: 0 0 0.9rem; }
.edit-link { color: var(--primary); cursor: pointer; margin-left: 0.5rem; font-size: 0.85rem; }

.form-group { margin-bottom: 0.8rem; }
.form-group label { display: block; margin-bottom: 0.35rem; font-size: 0.85rem; font-weight: 500; }
.form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
.input-field { width: 100%; padding: 0.55rem 0.75rem; border: 1px solid var(--border); border-radius: var(--radius); font-size: 0.92rem; box-sizing: border-box; }
.input-field:focus { outline: none; border-color: var(--primary); }
.checkbox-wrap { display: flex; align-items: center; gap: 0.45rem; font-size: 0.9rem; margin: 0.6rem 0 1rem; }

.sub-box { border: 1px dashed var(--border); border-radius: var(--radius); padding: 0.9rem 1rem; margin-bottom: 1rem; background: var(--bg); }
.sub-title { font-size: 0.88rem; font-weight: 600; margin-bottom: 0.5rem; }
.inline-row { display: flex; gap: 0.6rem; }
.inline-row .input-field { flex: 1; }

.topic-hits { margin-top: 0.7rem; display: flex; flex-direction: column; gap: 0.4rem; }
.topic-hit { display: flex; align-items: center; gap: 0.55rem; padding: 0.45rem 0.7rem; background: var(--card); border: 1px solid var(--border); border-radius: var(--radius); cursor: pointer; font-size: 0.87rem; }
.topic-hit:hover { border-color: var(--primary); }
.badge { font-size: 0.72rem; color: #fff; border-radius: 999px; padding: 0.08rem 0.5rem; flex-shrink: 0; }
.badge.gold { background: #d4a017; }
.badge.silver { background: #8a959e; }
.badge.bronze { background: #b0734c; }
.hit-title { flex: 1; }
.hit-meta { color: var(--text-muted); font-size: 0.78rem; flex-shrink: 0; }

.chips { display: flex; flex-wrap: wrap; gap: 0.45rem; margin-top: 0.6rem; }
.chip { border: 1px solid var(--primary); color: var(--primary); background: none; border-radius: 999px; padding: 0.3rem 0.8rem; font-size: 0.85rem; cursor: pointer; }
.chip:hover { background: var(--primary); color: #fff; }
.suggest-detail { margin-top: 0.6rem; font-size: 0.85rem; }
.suggest-detail summary { cursor: pointer; color: var(--text-muted); }
.suggest-text { white-space: pre-wrap; line-height: 1.65; margin-top: 0.5rem; max-height: 320px; overflow-y: auto; }

.ref-list { margin-top: 0.8rem; display: flex; flex-direction: column; gap: 0.5rem; max-height: 420px; overflow-y: auto; }
.ref-item { display: flex; gap: 0.6rem; padding: 0.6rem 0.75rem; background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); cursor: pointer; }
.ref-item:hover { border-color: var(--primary); }
.ref-body { flex: 1; min-width: 0; }
.ref-source { font-size: 0.85rem; font-weight: 600; }
.ref-score { color: var(--text-muted); font-weight: 400; font-size: 0.78rem; margin-left: 0.4rem; }
.ref-snippet { font-size: 0.82rem; color: var(--text-muted); margin-top: 0.25rem; line-height: 1.5; }
.no-results { padding: 1rem; text-align: center; color: var(--text-muted); background: var(--bg); border-radius: var(--radius); margin-top: 0.8rem; }

.textarea-field { width: 100%; padding: 0.7rem 0.85rem; border: 1px solid var(--border); border-radius: var(--radius); font-size: 0.92rem; font-family: inherit; resize: vertical; box-sizing: border-box; line-height: 1.65; margin-top: 0.6rem; }
.textarea-field:focus { outline: none; border-color: var(--primary); }

.gen-actions { display: flex; gap: 0.75rem; flex-wrap: wrap; margin: 0.6rem 0; }
.docx-ok { display: flex; align-items: center; gap: 0.75rem; margin: 0.8rem 0; font-size: 0.92rem; flex-wrap: wrap; }

.result-area { margin-top: 1.2rem; }
.result-head { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.6rem; margin-bottom: 0.5rem; font-size: 0.9rem; color: var(--text-muted); }
.result-actions { display: inline-flex; gap: 0.5rem; flex-wrap: wrap; }
.result-box { background: var(--bg); border: 1px solid var(--border); border-radius: var(--radius); padding: 1rem; white-space: pre-wrap; line-height: 1.7; max-height: 420px; overflow-y: auto; font-size: 0.9rem; }

.step-nav { display: flex; justify-content: space-between; margin-top: 1.2rem; gap: 0.75rem; }

.btn { padding: 0.6rem 1.1rem; border: 1px solid var(--border); background: var(--card); border-radius: var(--radius); font-size: 0.9rem; cursor: pointer; text-decoration: none; display: inline-block; }
.btn-primary { background: var(--primary); color: #fff; border-color: var(--primary); }
.btn-sm { padding: 0.35rem 0.8rem; font-size: 0.84rem; }
.btn:disabled { opacity: 0.5; cursor: not-allowed; }
.hint { font-size: 0.82rem; color: var(--text-muted); margin: 0.45rem 0; }
.msg { padding: 0.8rem 1rem; border-radius: var(--radius); font-size: 0.9rem; }
.msg.error { background: #fee; color: #c33; border: 1px solid #fcc; }
.msg.success { background: #efe; color: #3c3; border: 1px solid #cfc; }
.msg.warning { background: #ffc; color: #963; border: 1px solid #fc9; }

@media (max-width: 640px) {
  .form-row { grid-template-columns: 1fr; }
  .step { min-width: 40%; }
}
</style>
