const BASE = import.meta.env.DEV ? '' : (import.meta.env.VITE_API_BASE || '')

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
}
