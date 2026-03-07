<template>
  <div class="home">
    <header class="home-header">
      <h1 class="home-title">工作台</h1>
      <p class="home-desc">选择下方功能开始使用</p>
    </header>
    <div class="grid">
      <router-link to="/paper" class="card">
        <h3>论文</h3>
        <p>生成、润色、扩写、降重</p>
      </router-link>
      <router-link to="/lesson" class="card">
        <h3>教案生成</h3>
        <p>按主题与领域生成完整教案</p>
      </router-link>
      <router-link to="/case" class="card">
        <h3>教学案例生成</h3>
        <p>撰写情境与反思的教学案例</p>
      </router-link>
      <router-link to="/topic" class="card">
        <h3>课题申报</h3>
        <p>生成教育科研课题申报书（评职称用）</p>
      </router-link>
      <router-link to="/knowledge" class="card">
        <h3>知识库</h3>
        <p>上传 PDF/DOCX，智能问答</p>
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
</style>
