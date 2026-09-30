const BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE || '')

// 把服务端透传的配额/欠费错误翻译成可操作的中文提示
export function friendlyError(text) {
  const t = String(text || '')
  if (/余额不足|insufficient balance|FreeTier|免费额度|suspended/i.test(t)) {
    return 'AI 服务额度用完了：请到对应平台充值（智谱 open.bigmodel.cn / 月之暗面 moonshot.cn / 阿里百炼 dashscope），或修改 .env 的 LLM_PROVIDER 切换到有余额的服务商后重启后端。检索、选题库等非 AI 功能不受影响。'
  }
  if (/api_key|401|Invalid Key/i.test(t)) {
    return 'AI 服务 API Key 无效：请检查 .env 中对应平台的 Key 配置。'
  }
  return t
}

async function request(path, options = {}) {
  const url = BASE + path
  const res = await fetch(url, {
    ...options,
    headers: { 'Content-Type': 'application/json', ...options.headers },
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) throw new Error(data.detail || data.message || res.statusText)
  return data
}

export const api = {
  askKnowledge: (body) =>
    request('/api/ask_knowledge', {
      method: 'POST',
      body: JSON.stringify({
        question: body.question,
        top_k: body.top_k,
      }),
    }),
  generatePaper: (body) => request('/api/generate_paper', { method: 'POST', body: JSON.stringify(body) }),
  improvePaper: (body) => request('/api/improve_paper', { method: 'POST', body: JSON.stringify(body) }),
  expandPaper: (body) => request('/api/expand_paper', { method: 'POST', body: JSON.stringify(body) }),
  reduceWeight: (body) => request('/api/reduce_weight', { method: 'POST', body: JSON.stringify(body) }),
  generateLessonPlan: (body) => request('/api/generate_lesson_plan', { method: 'POST', body: JSON.stringify(body) }),
  generateTeachingCase: (body) => request('/api/generate_teaching_case', { method: 'POST', body: JSON.stringify(body) }),
  topicApplication: (body) => request('/api/topic_application', { method: 'POST', body: JSON.stringify(body) }),
  uploadKnowledge: (files) => {
    const fd = new FormData()
    const list = Array.isArray(files) ? files : [files]
    list.forEach((file) => fd.append('files', file))
    return fetch(BASE + '/api/upload_knowledge', { method: 'POST', body: fd }).then(r => r.json())
  },
  // 论文搜索和采集
  searchPapers: (body) => request('/api/papers/search', { method: 'POST', body: JSON.stringify(body) }),
  collectPapers: (body) => request('/api/papers/collect', { method: 'POST', body: JSON.stringify(body) }),
  // 选题库
  topicsSearch: (body) => request('/api/topics/search', { method: 'POST', body: JSON.stringify(body) }),
  topicsSuggest: (body) => request('/api/topics/suggest', { method: 'POST', body: JSON.stringify(body) }),
  // 图文排版 Word
  generateDocx: (body) => request('/api/paper/generate_docx', { method: 'POST', body: JSON.stringify(body) }),
  // 提纲 / 评审
  generateOutline: (body) => request('/api/generate_outline', { method: 'POST', body: JSON.stringify(body) }),
  reviewPaper: (body) => request('/api/review_paper', { method: 'POST', body: JSON.stringify(body) }),
}
