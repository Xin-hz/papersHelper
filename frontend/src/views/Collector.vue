<template>
  <div class="collector-page">
    <div class="page-header">
      <h1>📚 论文自动采集</h1>
      <p class="subtitle">搜索论文，一键下载并入库到知识库</p>
    </div>

    <!-- 搜索表单 -->
    <div class="search-section card">
      <h3>搜索论文</h3>
      <div class="form-group">
        <label>搜索关键词</label>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="例如：childhood education, early childhood development"
          @keyup.enter="handleSearch"
          class="input-field"
        />
      </div>

      <div class="form-row">
        <div class="form-group">
          <label>数据源</label>
          <div class="checkbox-group">
            <label v-for="source in sources" :key="source.value" class="checkbox-label">
              <input
                type="checkbox"
                v-model="selectedSources"
                :value="source.value"
                class="checkbox-input"
              />
              {{ source.label }}
            </label>
          </div>
        </div>

        <div class="form-group">
          <label>最大结果数</label>
          <input
            v-model.number="maxResults"
            type="number"
            min="1"
            max="50"
            class="input-field"
          />
        </div>
      </div>

      <div class="button-group">
        <button @click="handleSearch" :disabled="searching || !searchQuery.trim()" class="btn btn-primary">
          {{ searching ? '搜索中...' : '🔍 搜索论文' }}
        </button>
      </div>
    </div>

    <!-- 知识库统计 -->
    <div v-if="knowledgeStats" class="stats-section card">
      <h3>📊 知识库状态</h3>
      <div class="stats-grid">
        <div class="stat-item">
          <span class="stat-label">文档数量</span>
          <span class="stat-value">{{ knowledgeStats.document_count || 0 }}</span>
        </div>
        <div class="stat-item">
          <span class="stat-label">向量片段</span>
          <span class="stat-value">{{ knowledgeStats.vector_count || 0 }}</span>
        </div>
      </div>
    </div>

    <!-- 搜索结果 -->
    <div v-if="searchedPapers.length > 0" class="results-section card">
      <div class="results-header">
        <h3>搜索结果 ({{ searchedPapers.length }} 篇)</h3>
        <button @click="clearResults" class="btn btn-text">清空结果</button>
      </div>

      <div class="papers-list">
        <div v-for="(paper, index) in searchedPapers" :key="index" class="paper-item">
          <div class="paper-header">
            <h4>{{ paper.title }}</h4>
            <span class="paper-source">{{ getSourceLabel(paper.source) }}</span>
          </div>
          <div class="paper-meta">
            <span class="paper-authors">{{ paper.authors.join(', ') }}</span>
            <span v-if="paper.year" class="paper-year">{{ paper.year }}</span>
          </div>
          <p v-if="paper.abstract" class="paper-abstract">{{ truncate(paper.abstract, 200) }}</p>
          <div class="paper-actions">
            <span v-if="paper.pdf_available" class="badge badge-success">PDF 可用</span>
            <span v-else class="badge badge-warning">PDF 不可用</span>
            <button
              v-if="paper.pdf_available && paper.download_url"
              @click="downloadAndIngest(paper, index)"
              class="btn-download"
              :disabled="downloading === index"
            >
              {{ downloading === index ? '处理中...' : '📥 下载并入库' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 使用说明 -->
    <div class="info-section card">
      <h3>💡 使用说明</h3>
      <ul class="info-list">
        <li><strong>arXiv</strong>: 物理、数学、计算机等领域的免费预印本服务器（推荐）</li>
        <li><strong>DOAJ</strong>: 开放获取期刊目录</li>
        <li><strong>OpenAlex</strong>: 开放的学术文献索引</li>
        <li><strong>搜索技巧</strong>: 使用英文关键词搜索效果最佳</li>
	        <li><strong>采集流程</strong>: 搜索 → 点击"下载并入库" → 自动下载PDF → 向量化入库</li>
        <li><strong>注意事项</strong>: 首次使用会下载Embedding模型，请确保网络畅通</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = '' // 同源请求：dev 走 vite 代理，生产与后端同域

// 表单数据
const searchQuery = ref('')
const selectedSources = ref(['arxiv'])  // 默认只选arXiv
const maxResults = ref(20)

// 状态
const searching = ref(false)
const searchedPapers = ref([])
const downloading = ref(null)
const knowledgeStats = ref(null)

// 数据源选项
const sources = [
  { value: 'arxiv', label: 'arXiv (推荐)' },
  { value: 'doaj', label: 'DOAJ' },
  { value: 'openalex', label: 'OpenAlex' },
]

// 计算年份范围字符串
const getYearRange = () => {
  return null  // 简化，不使用年份过滤
}

// 搜索论文
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    alert('请输入搜索关键词')
    return
  }

  searching.value = true
  searchedPapers.value = []

  try {
    const response = await fetch(`${API_BASE}/api/papers/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: searchQuery.value.trim(),
        sources: selectedSources.value,
        max_results: maxResults.value,
        year_range: getYearRange(),
      }),
    })

    const data = await response.json()

    if (data.success && data.papers) {
      // 合并所有数据源的论文
      const allPapers = []
      for (const [source, papers] of Object.entries(data.papers)) {
        allPapers.push(...papers)
      }
      searchedPapers.value = allPapers
      console.log(`搜索到 ${allPapers.length} 篇论文`)

      // 加载知识库统计
      await loadKnowledgeStats()
    } else {
      alert('搜索失败，请稍后重试')
    }
  } catch (error) {
    console.error('搜索出错:', error)
    alert('搜索出错: ' + error.message)
  } finally {
    searching.value = false
  }
}

// 下载并入库
const downloadAndIngest = async (paper, index) => {
  if (!paper.download_url) {
    alert('该论文没有可用的下载链接')
    return
  }

  downloading.value = index

  try {
    // 调用后端API进行下载并入库
    const response = await fetch(`${API_BASE}/api/papers/download_and_ingest`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        title: paper.title,
        authors: paper.authors,
        year: paper.year,
        abstract: paper.abstract,
        doi: paper.doi,
        download_url: paper.download_url,
        source: paper.source,
        pdf_available: paper.pdf_available,
      }),
    })

    const data = await response.json()

    if (data.success) {
      alert(`✅ ${data.message || '下载并入库成功！'}`)
      // 刷新统计信息
      await loadKnowledgeStats()
    } else {
      alert(`❌ ${data.message || '下载并入库失败'}`)
    }
  } catch (error) {
    console.error('下载并入库失败:', error)
    alert('下载并入库失败: ' + error.message)
  } finally {
    downloading.value = null
  }
}

// 加载知识库统计
const loadKnowledgeStats = async () => {
  try {
    const response = await fetch(`${API_BASE}/api/knowledge/stats`)
    const data = await response.json()
    if (data.success) {
      knowledgeStats.value = data.stats
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

// 清空结果
const clearResults = () => {
  searchedPapers.value = []
}

// 工具函数
const truncate = (text, length) => {
  if (!text) return ''
  return text.length > length ? text.substring(0, length) + '...' : text
}

const getSourceLabel = (source) => {
  const sourceMap = {
    'arxiv': 'arXiv',
    'doaj': 'DOAJ',
    'openalex': 'OpenAlex',
  }
  return sourceMap[source] || source
}

// 页面加载时获取统计
loadKnowledgeStats()
</script>

<style scoped>
.collector-page {
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

.card {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1.5rem;
}

.card h3 {
  margin-top: 0;
  margin-bottom: 1rem;
  font-size: 1.1rem;
  color: var(--text);
}

.form-group {
  margin-bottom: 1rem;
}

.form-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
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

.checkbox-group {
  display: flex;
  flex-wrap: wrap;
  gap: 0.8rem;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.9rem;
}

.checkbox-input {
  cursor: pointer;
}

.button-group {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
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

.btn-text {
  background: transparent;
  color: var(--text-muted);
  padding: 0.4rem 0.8rem;
}

.btn-text:hover {
  color: var(--primary);
}

.stats-section {
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  margin-bottom: 1.5rem;
}

.stats-grid {
  display: flex;
  gap: 2rem;
}

.stat-item {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--text-muted);
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--primary);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.papers-list {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.paper-item {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 1rem;
  transition: border-color 0.2s;
}

.paper-item:hover {
  border-color: var(--primary);
}

.paper-header {
  display: flex;
  align-items: flex-start;
  gap: 0.8rem;
  margin-bottom: 0.5rem;
}

.paper-header h4 {
  flex: 1;
  margin: 0;
  font-size: 1rem;
  color: var(--text);
  line-height: 1.4;
}

.paper-source {
  padding: 0.2rem 0.6rem;
  background: rgba(15, 118, 110, 0.1);
  color: var(--primary);
  border-radius: var(--radius);
  font-size: 0.8rem;
  white-space: nowrap;
}

.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 1rem;
  margin-bottom: 0.5rem;
  font-size: 0.85rem;
  color: var(--text-muted);
}

.paper-abstract {
  color: var(--text-muted);
  font-size: 0.9rem;
  line-height: 1.5;
  margin: 0.5rem 0;
}

.paper-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.badge {
  padding: 0.2rem 0.6rem;
  border-radius: var(--radius);
  font-size: 0.8rem;
  font-weight: 500;
}

.badge-success {
  background: #d1fae5;
  color: #065f46;
}

.badge-warning {
  background: #fef3c7;
  color: #92400e;
}

.btn-download {
  padding: 0.3rem 0.8rem;
  background: var(--primary);
  color: white;
  border: none;
  border-radius: var(--radius);
  font-size: 0.85rem;
  cursor: pointer;
  transition: background 0.2s;
  margin-left: auto;
}

.btn-download:hover:not(:disabled) {
  background: var(--primary-hover);
}

.btn-download:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  padding: 0.5rem 0;
  font-size: 0.9rem;
  color: var(--text-muted);
  line-height: 1.5;
}

.info-list li strong {
  color: var(--text);
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .button-group {
    flex-direction: column;
  }

  .paper-header {
    flex-direction: column;
  }
}
</style>