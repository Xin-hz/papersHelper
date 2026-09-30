<template>
  <div class="home">
    <header class="home-header">
      <h1 class="home-title">工作台</h1>
      <p class="home-desc">两条主线：先写出来，再改到位</p>
    </header>
    <div class="grid two-cta">
      <router-link to="/write" class="card main-cta">
        <h3>✍️ 写论文</h3>
        <p>借鉴获奖选题 → 检索知识库 → 生成提纲 → 补充素材正式撰写</p>
      </router-link>
      <router-link to="/revise" class="card main-cta alt">
        <h3>🛠️ 改论文</h3>
        <p>粘贴或上传稿件 → 按意见优化 / 降重 / 生成评审报告</p>
      </router-link>
    </div>
    <div class="grid">
      <router-link to="/topics" class="card">
        <h3>选题库</h3>
        <p>1459 条浙江获奖选题检索与 AI 选题建议</p>
      </router-link>
      <router-link to="/knowledge" class="card">
        <h3>知识库</h3>
        <p>上传文档、智能问答、论文采集</p>
      </router-link>
      <router-link to="/daily?tool=lesson" class="card">
        <h3>教案生成</h3>
        <p>按主题与领域生成完整教案</p>
      </router-link>
      <router-link to="/daily?tool=case" class="card">
        <h3>教学案例</h3>
        <p>撰写情境与反思的教学案例</p>
      </router-link>
      <router-link to="/daily?tool=topic" class="card">
        <h3>课题申报</h3>
        <p>生成教育科研课题申报书（评职称用）</p>
      </router-link>
    </div>
  </div>
</template>

<script setup>
</script>

<style scoped>
.home { padding-top: 0.25rem; }
.home-header { margin-bottom: 1.75rem; }
.home-title {
  margin: 0 0 0.5rem;
  font-size: 1.5rem;
  font-weight: 600;
  color: var(--text);
  letter-spacing: 0.02em;
}
.home-desc {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-muted);
}
.text-muted { color: var(--text-muted); }
a.card { text-decoration: none; color: inherit; }
.two-cta { grid-template-columns: 1fr 1fr; margin-bottom: 1.25rem; }
.main-cta {
  padding: 1.4rem 1.5rem;
  border: 2px solid var(--primary);
  background: var(--card);
  border-radius: var(--radius);
}
.main-cta h3 { margin: 0 0 0.4rem; color: var(--primary); font-size: 1.2rem; }
.main-cta p { margin: 0; }
.main-cta:hover { box-shadow: 0 4px 14px rgba(0,0,0,0.08); }
.main-cta.alt h3 { color: #2a7f62; }
@media (max-width: 640px) { .two-cta { grid-template-columns: 1fr; } }
</style>
