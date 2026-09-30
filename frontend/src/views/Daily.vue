<template>
  <div class="daily-page">
    <div class="page-header">
      <h1>📝 日常工具</h1>
      <p class="subtitle">教案生成、教学案例、课题申报等日常教学工具</p>
    </div>

    <!-- 工具选择导航 -->
    <div class="tools-nav card">
      <div class="tool-tabs">
        <button
          @click="activeTool = 'lesson'"
          :class="['tool-tab', { active: activeTool === 'lesson' }]"
        >
          📚 教案生成
        </button>
        <button
          @click="activeTool = 'case'"
          :class="['tool-tab', { active: activeTool === 'case' }]"
        >
          🎭 教学案例
        </button>
        <button
          @click="activeTool = 'topic'"
          :class="['tool-tab', { active: activeTool === 'topic' }]"
        >
          📋 课题申报
        </button>
      </div>
    </div>

    <!-- 教案生成工具 -->
    <div v-if="activeTool === 'lesson'" class="tool-section">
      <div class="card">
        <h3>📚 教案生成</h3>
        <div class="form-group">
          <label>课程主题</label>
          <input
            v-model="lessonForm.topic"
            type="text"
            placeholder="例如：认识四季、认识数字"
            class="input-field"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>适合年龄</label>
            <input
              v-model="lessonForm.grade"
              type="text"
              placeholder="例如：大班、中班、小班"
              class="input-field"
            />
          </div>

          <div class="form-group">
            <label>教学领域</label>
            <input
              v-model="lessonForm.subject"
              type="text"
              placeholder="例如：语言、艺术、科学"
              class="input-field"
            />
          </div>
        </div>

        <div class="form-group">
          <label>教学目标</label>
          <textarea
            v-model="lessonForm.goal"
            placeholder="描述本次教学要达成的目标"
            class="textarea-field"
            rows="3"
          ></textarea>
        </div>

        <div class="form-group">
          <label>课时安排</label>
          <input
            v-model="lessonForm.duration"
            type="text"
            placeholder="例如：一课时、20分钟"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="lessonForm.use_rag" />
            结合知识库资料（使用RAG技术）
          </label>
        </div>

        <div class="button-group">
          <button @click="generateLesson" :disabled="lessonGenerating" class="btn btn-primary">
            {{ lessonGenerating ? '生成中...' : '✏️ 生成教案' }}
          </button>
          <button @click="clearLessonForm" class="btn btn-text">清空</button>
        </div>

        <div v-if="lessonResult" class="result-section card">
          <div class="result-header">
            <h4>生成结果</h4>
            <button @click="copyResult('lesson')" class="btn btn-text">📋 复制</button>
          </div>
          <div class="result-content">{{ lessonResult }}</div>
        </div>
      </div>
    </div>

    <!-- 教学案例工具 -->
    <div v-if="activeTool === 'case'" class="tool-section">
      <div class="card">
        <h3>🎭 教学案例生成</h3>
        <div class="form-group">
          <label>活动主题</label>
          <input
            v-model="caseForm.topic"
            type="text"
            placeholder="例如：区域活动中幼儿争抢材料"
            class="input-field"
          />
        </div>

        <div class="form-row">
          <div class="form-group">
            <label>年龄段</label>
            <input
              v-model="caseForm.age"
              type="text"
              placeholder="例如：大班、中班、小班"
              class="input-field"
            />
          </div>

          <div class="form-group">
            <label>活动目标</label>
            <input
              v-model="caseForm.goal"
              type="text"
              placeholder="描述本次活动要达成的目标"
              class="input-field"
            />
          </div>
        </div>

        <div class="form-group">
          <label>场景说明</label>
          <input
            v-model="caseForm.scenario"
            type="text"
            placeholder="例如：区域活动、集体教学、游戏活动"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="caseForm.use_rag" />
            结合知识库资料（使用RAG技术）
          </label>
        </div>

        <div class="button-group">
          <button @click="generateCase" :disabled="caseGenerating" class="btn btn-primary">
            {{ caseGenerating ? '生成中...' : '🎭 生成教学案例' }}
          </button>
          <button @click="clearCaseForm" class="btn btn-text">清空</button>
        </div>

        <div v-if="caseResult" class="result-section card">
          <div class="result-header">
            <h4>生成结果</h4>
            <button @click="copyResult('case')" class="btn btn-text">📋 复制</button>
          </div>
          <div class="result-content">{{ caseResult }}</div>
        </div>
      </div>
    </div>

    <!-- 课题申报工具 -->
    <div v-if="activeTool === 'topic'" class="tool-section">
      <div class="card">
        <h3>📋 课题申报书生成</h3>
        <div class="form-group">
          <label>课题名称</label>
          <input
            v-model="topicForm.topic"
            type="text"
            placeholder="例如：幼儿园区域活动中教师指导策略研究"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label>研究方向</label>
          <input
            v-model="topicForm.direction"
            type="text"
            placeholder="例如：游戏化教学、家园共育"
            class="input-field"
          />
        </div>

        <div class="form-group">
          <label class="checkbox-label">
            <input type="checkbox" v-model="topicForm.use_rag" />
            结合知识库资料（使用RAG技术）
          </label>
        </div>

        <div class="button-group">
          <button @click="generateTopic" :disabled="topicGenerating" class="btn btn-primary">
            {{ topicGenerating ? '生成中...' : '📋 生成课题申报书' }}
          </button>
          <button @click="clearTopicForm" class="btn-text">清空</button>
        </div>

        <div v-if="topicResult" class="result-section card">
          <div class="result-header">
            <h4>生成结果</h4>
            <button @click="copyResult('topic')" class="btn btn-text">📋 复制</button>
          </div>
          <div class="result-content">{{ topicResult }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { friendlyError } from '../api'
import { useRoute } from 'vue-router'

const API_BASE = '' // 同源请求：dev 走 vite 代理，生产与后端同域

const route = useRoute()
// 当前激活的工具（支持 ?tool=lesson/case/topic 定位，与首页卡片入口一致）
const validTools = ['lesson', 'case', 'topic']
const activeTool = ref(validTools.includes(route.query.tool) ? route.query.tool : 'lesson')

// 教案表单
const lessonForm = ref({
  topic: '',
  grade: '',
  subject: '',
  goal: '',
  duration: '',
  use_rag: true
})
const lessonGenerating = ref(false)
const lessonResult = ref('')

// 教学案例表单
const caseForm = ref({
  topic: '',
  age: '',
  goal: '',
  scenario: '',
  use_rag: true
})
const caseGenerating = ref(false)
const caseResult = ref('')

// 课题申报表单
const topicForm = ref({
  topic: '',
  direction: '',
  use_rag: true
})
const topicGenerating = ref(false)
const topicResult = ref('')

// 生成教案
const generateLesson = async () => {
  if (!lessonForm.value.topic.trim()) {
    alert('请输入课程主题')
    return
  }

  lessonGenerating.value = true
  lessonResult.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/generate_lesson_plan`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: lessonForm.value.topic,
        grade: lessonForm.value.grade,
        goal: lessonForm.value.goal,
        subject: lessonForm.value.subject,
        duration: lessonForm.value.duration,
        use_rag: lessonForm.value.use_rag,
      }),
    })

    const data = await response.json()

    if (data.success) {
      lessonResult.value = data.content
    } else {
      alert(friendlyError(data.content || '未知错误'))
    }
  } catch (error) {
    console.error('生成教案出错:', error)
    alert(friendlyError(error.message))
  } finally {
    lessonGenerating.value = false
  }
}

// 生成教学案例
const generateCase = async () => {
  if (!caseForm.value.topic.trim()) {
    alert('请输入活动主题')
    return
  }

  caseGenerating.value = true
  caseResult.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/generate_teaching_case`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: caseForm.value.topic,
        age: caseForm.value.age,
        goal: caseForm.value.goal,
        scenario: caseForm.value.scenario,
        use_rag: caseForm.value.use_rag,
      }),
    })

    const data = await response.json()

    if (data.success) {
      caseResult.value = data.content
    } else {
      alert(friendlyError(data.content || '未知错误'))
    }
  } catch (error) {
    console.error('生成教学案例出错:', error)
    alert(friendlyError(error.message))
  } finally {
    caseGenerating.value = false
  }
}

// 生成课题申报书
const generateTopic = async () => {
  if (!topicForm.value.topic.trim()) {
    alert('请输入课题名称')
    return
  }

  topicGenerating.value = true
  topicResult.value = ''

  try {
    const response = await fetch(`${API_BASE}/api/topic_application`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        topic: topicForm.value.topic,
        direction: topicForm.value.direction,
        use_rag: topicForm.value.use_rag,
      }),
    })

    const data = await response.json()

    if (data.success) {
      topicResult.value = data.content
    } else {
      alert(friendlyError(data.content || '未知错误'))
    }
  } catch (error) {
    console.error('生成课题申报书出错:', error)
    alert(friendlyError(error.message))
  } finally {
    topicGenerating.value = false
  }
}

// 清空表单函数
const clearLessonForm = () => {
  lessonForm.value = {
    topic: '',
    grade: '',
    subject: '',
    goal: '',
    duration: '',
    use_rag: true
  }
  lessonResult.value = ''
}

const clearCaseForm = () => {
  caseForm.value = {
    topic: '',
    age: '',
    goal: '',
    scenario: '',
    use_rag: true
  }
  caseResult.value = ''
}

const clearTopicForm = () => {
  topicForm.value = {
    topic: '',
    direction: '',
    use_rag: true
  }
  topicResult.value = ''
}

// 复制结果
const copyResult = (type) => {
  let content = ''
  if (type === 'lesson') content = lessonResult.value
  if (type === 'case') content = caseResult.value
  if (type === 'topic') content = topicResult.value

  if (navigator.clipboard) {
    navigator.clipboard.writeText(content)
    alert('已复制到剪贴板')
  } else {
    alert('复制功能不支持，请手动复制')
  }
}
</script>

<style scoped>
.daily-page {
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

.card h4 {
  margin: 0;
  color: var(--text);
}

.tools-nav {
  margin-bottom: 1.5rem;
}

.tool-tabs {
  display: flex;
  gap: 0.5rem;
  background: var(--bg);
  padding: 0.3rem;
  border-radius: var(--radius);
}

.tool-tab {
  padding: 0.6rem 1rem;
  border: none;
  background: transparent;
  color: var(--text);
  border-radius: var(--radius);
  cursor: pointer;
  font-size: 0.95rem;
  transition: all 0.2s;
  font-weight: 500;
}

.tool-tab:hover {
  background: var(--bg-alt);
  color: var(--primary);
}

.tool-tab.active {
  background: var(--primary);
  color: white;
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

.textarea-field {
  width: 100%;
  padding: 0.6rem 0.8rem;
  border: 1px solid var(--border);
  border-radius: var(--radius);
  font-size: 0.95rem;
  font-family: inherit;
  min-height: 80px;
  resize: vertical;
}

.textarea-field:focus {
  outline: none;
  border-color: var(--primary);
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  cursor: pointer;
  font-size: 0.9rem;
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

.result-section {
  margin-top: 1.5rem;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 0.5rem;
  border-bottom: 1px solid var(--border);
}

.result-content {
  line-height: 1.6;
  white-space: pre-wrap;
  color: var(--text);
}

@media (max-width: 640px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .button-group {
    flex-direction: column;
  }

  .tool-tabs {
    flex-wrap: wrap;
  }
}
</style>