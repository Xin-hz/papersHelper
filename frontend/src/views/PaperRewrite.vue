<template>
  <div class="paper-rewrite-page">
    <div class="page-header">
      <h1>✍️ 论文降重助手</h1>
      <p class="subtitle">上传论文，AI智能降重，保持原意</p>
    </div>

    <!-- 上传区域 -->
    <div class="upload-section card">
      <h3>📤 上传论文</h3>
      <div class="upload-area"
           @drop.prevent="handleDrop"
           @dragover.prevent
           @dragenter.prevent>
        <input
          type="file"
          ref="fileInput"
          @change="handleFileSelect"
          accept=".txt,.md,.tex,.docx,.doc,.pdf"
          style="display: none"
        />
        <div class="upload-placeholder" @click="$refs.fileInput.click()">
          <div class="upload-icon">📁</div>
          <p>拖拽文件到这里或点击上传</p>
          <p class="file-formats">支持格式: .txt .md .tex .docx .doc .pdf</p>
        </div>
      </div>

      <div v-if="selectedFile" class="file-info">
        <div class="file-name">📄 {{ selectedFile.name }}</div>
        <div class="file-size">{{ formatFileSize(selectedFile.size) }}</div>
        <button @click="clearFile" class="btn btn-text">清除</button>
      </div>
    </div>

    <!-- 降重设置 -->
    <div class="settings-section card">
      <h3>⚙️ 降重设置</h3>

      <div class="form-group">
        <label>降重力度</label>
        <div class="intensity-options">
          <label
            v-for="option in intensityOptions"
            :key="option.value"
            class="intensity-option"
            :class="{ active: intensity === option.value }"
          >
            <input
              type="radio"
              :value="option.value"
              v-model="intensity"
            />
            <div class="option-content">
              <div class="option-title">{{ option.label }}</div>
              <div class="option-desc">{{ option.desc }}</div>
            </div>
          </label>
        </div>
      </div>

      <div class="form-group">
        <label class="checkbox-label">
          <input type="checkbox" v-model="generateDiff" />
          生成对照报告 (显示原文与改写对比)
        </label>
      </div>

      <button
        @click="handleRewrite"
        :disabled="!selectedFile || rewriting"
        class="btn btn-primary btn-large"
      >
        {{ rewriting ? '处理中...' : '🚀 开始降重' }}
      </button>
    </div>

    <!-- 处理结果 -->
    <div v-if="result" class="result-section card">
      <h3>📊 处理结果</h3>

      <div v-if="result.success" class="success-result">
        <div class="success-item">
          <span class="success-icon">✅</span>
          <div>
            <div class="success-title">降重完成</div>
            <div class="success-desc">
              输出文件: <strong>{{ result.output_filename }}</strong>
            </div>
            <div v-if="result.stats" class="success-desc">
              共 {{ result.stats.total }} 段：改写 {{ result.stats.rewritten }} 段、
              受保护跳过 {{ result.stats.skipped }} 段、校验回退 {{ result.stats.reverted }} 段
            </div>
          </div>
        </div>

        <div v-if="result.diff_file" class="success-item">
          <span class="success-icon">📋</span>
          <div>
            <div class="success-title">对照报告已生成</div>
            <div class="success-desc">
              报告文件: <strong>{{ getFileName(result.diff_file) }}</strong>
            </div>
          </div>
        </div>

        <div class="result-actions">
          <button @click="downloadResult" class="btn btn-secondary">
            📥 下载结果
          </button>
          <button @click="clearResult" class="btn btn-text">
            清空结果
          </button>
        </div>
      </div>

      <div v-else class="error-result">
        <div class="error-icon">❌</div>
        <div class="error-message">{{ result.error }}</div>
      </div>
    </div>

    <!-- 使用说明 -->
    <div class="info-section card">
      <h3>💡 使用说明</h3>
      <ul class="info-list">
        <li><strong>轻度降重</strong>: 同义词替换、句式微调，保留原文约80%</li>
        <li><strong>中度降重</strong>: 句式重构、概念转换，保留原文约50% (推荐)</li>
        <li><strong>重度降重</strong>: 结构重组、逻辑变换，保留原文约30%</li>
        <li><strong>保护内容</strong>: 公式、引用、数据、代码块等会被原样保留</li>
        <li><strong>支持格式</strong>: 文本文件、Markdown、LaTeX、Word文档、PDF</li>
        <li><strong>注意事项</strong>: 输出文件会保存在原文件同目录下</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const API_BASE = '' // 同源请求：dev 走 vite 代理，生产与后端同域

// 状态
const selectedFile = ref(null)
const intensity = ref('medium')
const generateDiff = ref(false)
const rewriting = ref(false)
const result = ref(null)

// 强度选项
const intensityOptions = [
  {
    value: 'light',
    label: '轻度',
    desc: '同义词替换、句式微调'
  },
  {
    value: 'medium',
    label: '中度',
    desc: '句式重构、概念转换 (推荐)'
  },
  {
    value: 'heavy',
    label: '重度',
    desc: '结构重组、逻辑变换'
  }
]

// 文件选择
const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
  }
}

// 拖拽上传
const handleDrop = (event) => {
  const file = event.dataTransfer.files[0]
  if (file) {
    selectedFile.value = file
  }
}

// 清除文件
const clearFile = () => {
  selectedFile.value = null
  result.value = null
}

// 格式化文件大小
const formatFileSize = (bytes) => {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// 获取文件名
const getFileName = (path) => {
  return path.split('/').pop()
}

// 执行降重
const handleRewrite = async () => {
  if (!selectedFile.value) {
    alert('请先选择文件')
    return
  }

  rewriting.value = true
  result.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    formData.append('intensity', intensity.value)
    formData.append('generate_diff', generateDiff.value)

    const response = await fetch(`${API_BASE}/api/paper/rewrite`, {
      method: 'POST',
      body: formData
    })

    const data = await response.json()
    result.value = data

    if (data.success) {
      // 自动下载结果
      downloadResult()
    }
  } catch (error) {
    result.value = {
      success: false,
      error: '处理失败: ' + error.message
    }
  } finally {
    rewriting.value = false
  }
}

// 下载结果
const downloadResult = async () => {
  if (result.value?.success && result.value?.output_filename) {
    try {
      const link = document.createElement('a')
      link.href = `${API_BASE}/api/download/${encodeURIComponent(result.value.output_filename)}`
      link.download = result.value.output_filename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
    } catch (error) {
      console.error('下载失败:', error)
      alert('下载失败，请重试')
    }
  }
}

// 清空结果
const clearResult = () => {
  result.value = null
}
</script>

<style scoped>
.paper-rewrite-page {
  max-width: 800px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  text-align: center;
  margin-bottom: 30px;
}

.page-header h1 {
  font-size: 2.5rem;
  color: #2c3e50;
  margin-bottom: 10px;
}

.subtitle {
  color: #7f8c8d;
  font-size: 1.1rem;
}

.card {
  background: white;
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card h3 {
  margin-top: 0;
  color: #2c3e50;
  font-size: 1.3rem;
  margin-bottom: 16px;
}

/* 上传区域 */
.upload-area {
  border: 2px dashed #ddd;
  border-radius: 8px;
  padding: 40px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
}

.upload-area:hover {
  border-color: #3498db;
  background: #f8f9fa;
}

.upload-icon {
  font-size: 3rem;
  margin-bottom: 10px;
}

.upload-placeholder p {
  margin: 8px 0;
  color: #7f8c8d;
}

.file-formats {
  font-size: 0.9rem;
  color: #95a5a6;
}

.file-info {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  margin-top: 16px;
}

.file-name {
  font-weight: 500;
  color: #2c3e50;
}

.file-size {
  color: #7f8c8d;
  font-size: 0.9rem;
}

/* 强度选项 */
.intensity-options {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-top: 12px;
}

.intensity-option {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.intensity-option:hover {
  border-color: #3498db;
}

.intensity-option.active {
  border-color: #3498db;
  background: #e3f2fd;
}

.intensity-option input[type="radio"] {
  display: none;
}

.option-content {
  text-align: center;
}

.option-title {
  font-weight: 500;
  color: #2c3e50;
  margin-bottom: 4px;
}

.option-desc {
  font-size: 0.85rem;
  color: #7f8c8d;
}

/* 表单元素 */
.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  color: #2c3e50;
  font-weight: 500;
}

.checkbox-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  margin-right: 8px;
  width: 16px;
  height: 16px;
}

/* 按钮 */
.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.3s;
}

.btn-primary {
  background: #3498db;
  color: white;
  width: 100%;
}

.btn-primary:hover:not(:disabled) {
  background: #2980b9;
}

.btn-primary:disabled {
  background: #95a5a6;
  cursor: not-allowed;
}

.btn-large {
  padding: 14px 28px;
  font-size: 1.1rem;
}

.btn-secondary {
  background: #27ae60;
  color: white;
}

.btn-secondary:hover {
  background: #229954;
}

.btn-text {
  background: transparent;
  color: #7f8c8d;
}

.btn-text:hover {
  color: #2c3e50;
}

.result-actions {
  display: flex;
  gap: 12px;
  margin-top: 16px;
}

/* 结果显示 */
.success-result {
  color: #27ae60;
}

.success-item {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 16px;
}

.success-icon {
  font-size: 1.5rem;
}

.success-title {
  font-weight: 500;
  margin-bottom: 4px;
}

.success-desc {
  color: #7f8c8d;
}

.error-result {
  text-align: center;
  color: #e74c3c;
}

.error-icon {
  font-size: 2rem;
  margin-bottom: 12px;
}

.error-message {
  font-size: 1.1rem;
}

/* 说明区域 */
.info-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.info-list li {
  padding: 8px 0;
  color: #2c3e50;
  line-height: 1.6;
}

.info-list li strong {
  color: #3498db;
}
</style>