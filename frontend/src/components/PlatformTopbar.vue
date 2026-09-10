<template>
  <header class="platform-topbar">
    <RouterLink class="platform-brand" to="/platform" aria-label="返回夸克智汇平台">
      <span>Quarkmed</span>
      <strong>夸克智汇平台</strong>
    </RouterLink>

    <nav class="platform-global-nav" aria-label="平台导航">
      <RouterLink :class="{ 'is-active': isActive('platform-home') }" to="/platform">首页</RouterLink>
      <a href="#" @click.prevent="showComingSoon('智核引擎AI')">智核引擎AI</a>
      <a href="#" @click.prevent="showComingSoon('智能BI看板')">智能BI看板</a>
      <a href="#" @click.prevent="showComingSoon('市场调研汇总')">市场调研汇总</a>
      <a href="#" @click.prevent="showComingSoon('医药BD交易商机')">医药BD交易商机</a>
      <RouterLink :class="{ 'is-active': isActive('platform-research') }" to="/platform/research">CNS商机挖掘</RouterLink>
      <a href="#" @click.prevent="showComingSoon('药物警戒')">药物警戒</a>
      <RouterLink :class="{ 'is-active': isActive('dashboard') }" to="/dashboard">临床评估量表</RouterLink>
      <a href="#" @click.prevent="showComingSoon('公司模板库')">公司模板库</a>
      <a href="#" @click.prevent="openDify">Dify AI应用开发</a>
    </nav>

    <div class="platform-topbar__actions">
      <label class="platform-global-search">
        <el-icon><Search /></el-icon>
        <input v-model="searchText" type="search" placeholder="搜索平台、知识、数据..." />
      </label>
      <button class="platform-user-button" type="button" aria-label="用户中心" @click="showComingSoon('用户中心')">
        <el-icon><User /></el-icon>
      </button>
    </div>
  </header>
</template>

<script setup lang="ts">
import { Search, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { ref } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const searchText = ref('')

function isActive(name: string) {
  return route.name === name
}

function showComingSoon(name: string) {
  ElMessage.info(`${name}功能为静态演示`)
}

function openDify() {
  window.open(import.meta.env.VITE_DIFY_URL || 'http://localhost:8081', '_blank', 'noopener,noreferrer')
}
</script>

<style scoped>
.platform-topbar { position: sticky; top: 0; z-index: 20; display: flex; height: 72px; align-items: center; gap: 24px; padding: 0 34px 0 42px; border-bottom: 1px solid #e8f0fa; background: rgba(255, 255, 255, .96); }
.platform-brand { display: flex; width: 146px; flex: 0 0 146px; flex-direction: column; color: #0c58cf; text-decoration: none; }
.platform-brand span { font: 700 28px/1 Arial, "Helvetica Neue", sans-serif; letter-spacing: -1.7px; }
.platform-brand strong { margin: 4px 0 0 27px; color: #153e8e; font-size: 14px; letter-spacing: .7px; }
.platform-global-nav { display: flex; height: 100%; align-items: center; gap: 20px; min-width: 0; flex: 1; overflow-x: auto; scrollbar-width: none; }
.platform-global-nav::-webkit-scrollbar { display: none; }
.platform-global-nav a { position: relative; display: inline-flex; height: 100%; flex: 0 0 auto; align-items: center; color: #49679b; font-size: 13px; text-decoration: none; white-space: nowrap; }
.platform-global-nav a:hover, .platform-global-nav a.is-active { color: #1268e9; font-weight: 600; }
.platform-global-nav a.is-active::after { position: absolute; right: 0; bottom: 0; left: 0; height: 3px; border-radius: 3px 3px 0 0; background: #1679f6; content: ''; }
.platform-topbar__actions { display: flex; flex: 0 0 auto; align-items: center; gap: 20px; }
.platform-global-search { display: flex; width: min(320px, 20vw); height: 40px; align-items: center; gap: 10px; padding: 0 16px; border-radius: 22px; background: #eef6ff; color: #5c8dd3; }
.platform-global-search input { min-width: 0; flex: 1; border: 0; outline: 0; background: transparent; color: #294c86; font-size: 13px; }
.platform-global-search input::placeholder { color: #9bb6d9; }
.platform-user-button { display: grid; width: 40px; height: 40px; place-items: center; border: 1px solid #deebf9; border-radius: 50%; background: #f5faff; color: #0e6bf1; font-size: 22px; cursor: pointer; }

@media (max-width: 1200px) {
  .platform-topbar { gap: 20px; padding-left: 25px; }
  .platform-global-nav { gap: 18px; }
}

@media (max-width: 900px) {
  .platform-topbar { height: auto; min-height: 72px; flex-wrap: wrap; padding: 14px 18px; }
  .platform-brand { width: 140px; flex-basis: 140px; }
  .platform-global-nav { order: 3; width: 100%; height: 38px; flex-basis: 100%; gap: 20px; overflow-x: auto; }
  .platform-global-nav a { height: 38px; }
  .platform-topbar__actions { margin-left: auto; }
}

@media (max-width: 560px) {
  .platform-global-search { width: 42px; padding: 0 12px; }
  .platform-global-search input { display: none; }
  .platform-topbar__actions { gap: 9px; }
  .platform-brand span { font-size: 24px; }
  .platform-brand strong { margin-left: 21px; font-size: 11px; }
}
</style>
