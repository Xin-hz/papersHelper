<template>
  <div class="app">
    <header class="nav-header">
      <router-link to="/" class="nav-logo">幼儿园教师 AI 论文助手</router-link>
      <div class="nav-links">
        <router-link to="/" exact-active-class="nav-active">首页</router-link>
        <router-link to="/write" active-class="nav-active">写论文</router-link>
        <router-link to="/revise" active-class="nav-active">改论文</router-link>
        <router-link to="/topics" active-class="nav-active">选题库</router-link>
        <router-link to="/knowledge" active-class="nav-active">知识库</router-link>
        <router-link to="/daily" active-class="nav-active">日常工具</router-link>
      </div>
    </header>
    <main class="container">
      <router-view />
    </main>
  </div>
</template>

<script setup>
</script>

<style scoped>
.app { min-height: 100vh; display: flex; flex-direction: column; }
.nav-header {
  background: var(--card);
  border-bottom: 1px solid var(--border);
  padding: 0 1.5rem;
  display: flex;
  align-items: center;
  gap: 2rem;
  flex-shrink: 0;
}
.nav-logo {
  font-weight: 700;
  font-size: 1.15rem;
  color: var(--primary);
  padding: 1rem 0;
  text-decoration: none;
  white-space: nowrap;
}
.nav-logo:hover { text-decoration: none; color: var(--primary-hover); }
.nav-links {
  display: flex;
  align-items: center;
  gap: 0.25rem;
  flex-wrap: wrap;
}
.nav-links a {
  color: var(--text);
  text-decoration: none;
  padding: 0.6rem 0.9rem;
  border-radius: var(--radius);
  font-size: 0.95rem;
  transition: background .15s, color .15s;
}
.nav-links a:hover {
  background: var(--bg);
  text-decoration: none;
  color: var(--primary);
}
.nav-links a.nav-active {
  background: rgba(15, 118, 110, .1);
  color: var(--primary);
  font-weight: 500;
}
.container { flex: 1; max-width: 920px; margin: 0 auto; padding: 1.75rem 1.5rem; width: 100%; }
</style>
