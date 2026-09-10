<template>
  <main class="platform-home">
    <section class="platform-hero" aria-label="平台欢迎区">
      <img src="/platform/home-hero.png" alt="" />
    </section>

    <section class="platform-apps" aria-labelledby="platform-apps-title">
      <h1 id="platform-apps-title" class="sr-only">平台应用</h1>
      <button
        v-for="app in filteredApps"
        :key="app.name"
        class="app-card"
        :class="`app-card--${app.tone}`"
        type="button"
        @click="openApp(app)"
      >
        <span class="app-card__icon"><img :src="`/platform/icons/${app.icon}`" :alt="`${app.name}图标`" /></span>
        <span class="app-card__copy">
          <strong>{{ app.name }}</strong>
          <small v-if="app.description">{{ app.description }}</small>
        </span>
        <span class="app-card__arrow"><el-icon><ArrowRight /></el-icon></span>
      </button>
      <div v-if="filteredApps.length === 0" class="empty-apps">未找到匹配的平台应用</div>
    </section>

    <footer class="platform-footer" aria-label="平台价值">
      <span>专业·安全·高效</span>
    </footer>
  </main>
</template>

<script setup lang="ts">
import { ArrowRight } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

type AppTone = 'blue' | 'purple' | 'teal' | 'orange' | 'cyan'
type PlatformApp = {
  name: string
  tone: AppTone
  icon: string
  description?: string
  route?: string
  url?: string
}

const searchText = ref('')
const router = useRouter()
const apps: PlatformApp[] = [
  { name: '智核引擎AI', tone: 'blue', icon: 'ai.svg' },
  { name: '智能BI看板', tone: 'purple', icon: 'bi.svg' },
  { name: '市场调研汇总', tone: 'teal', icon: 'ops.svg' },
  { name: '医药BD交易商机', tone: 'orange', icon: 'bd.svg' },
  { name: 'CNS商机挖掘', tone: 'cyan', icon: 'research.svg', route: 'platform-research' },
  { name: '药物警戒', tone: 'blue', icon: 'pv.svg' },
  { name: '临床评估量表', tone: 'purple', icon: 'scale.svg', route: 'dashboard' },
  { name: '公司模板库', tone: 'blue', icon: 'ppt.svg' },
  { name: 'Dify AI应用开发', tone: 'blue', icon: 'dify.svg', url: import.meta.env.VITE_DIFY_URL || 'http://localhost:8081' }
]

const filteredApps = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  return keyword ? apps.filter((app) => app.name.toLowerCase().includes(keyword)) : apps
})

function openApp(app: PlatformApp) {
  if (app.route) {
    router.push({ name: app.route })
    return
  }
  if (app.url) {
    window.open(app.url, '_blank', 'noopener,noreferrer')
    return
  }
  ElMessage.info(`${app.name} 页面正在建设中`)
}

function showUserMessage() {
  ElMessage.info('用户中心暂未开放')
}
</script>

<style scoped>
.platform-home {
  min-height: calc(100vh - 72px);
  overflow-x: hidden;
  background: #fff;
  color: #10245d;
}

.platform-hero { height: clamp(208px, 15.5vw, 260px); overflow: hidden; }
.platform-hero img { display: block; width: 100%; height: 100%; object-fit: cover; object-position: center; }

.platform-apps {
  display: grid;
  width: min(1475px, calc(100% - 80px));
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 29px 27px;
  margin: 50px auto 0;
}

.app-card {
  display: grid;
  min-height: 160px;
  grid-template-columns: 86px minmax(0, 1fr) 42px;
  align-items: center;
  gap: 17px;
  padding: 0 18px 0 30px;
  border: 1px solid transparent;
  border-radius: 16px;
  background: #f8fbff;
  color: #112a70;
  text-align: left;
  cursor: pointer;
  transition: transform .2s, box-shadow .2s, border-color .2s;
}

.app-card:hover { transform: translateY(-3px); box-shadow: 0 12px 28px rgba(71, 113, 189, .12); }
.app-card__copy { display: flex; min-width: 0; flex-direction: column; gap: 6px; }
.app-card strong { font-size: 20px; font-weight: 600; white-space: nowrap; }
.app-card small { color: #7b91b8; font-size: 13px; line-height: 1.4; }
.app-card__icon { display: grid; width: 76px; height: 76px; place-items: center; }
.app-card__icon img { display: block; width: 64px; height: 64px; }
.app-card__arrow { display: grid; width: 42px; height: 42px; place-items: center; justify-self: end; border-radius: 50%; font-size: 24px; }
.app-card--blue { border-color: #dbeeff; background: linear-gradient(115deg, #f6fbff, #eff9ff); }.app-card--blue .app-card__arrow { background: #e6f3ff; color: #3989ee; }
.app-card--purple { border-color: #e7e0ff; background: linear-gradient(115deg, #fbfaff, #f8f5ff); }.app-card--purple .app-card__arrow { background: #f2ebff; color: #6841ec; }
.app-card--teal { border-color: #d2f2ee; background: linear-gradient(115deg, #f8fffe, #f0fcfb); }.app-card--teal .app-card__arrow { background: #e7fbf7; color: #10bba9; }
.app-card--orange { border-color: #faeadb; background: linear-gradient(115deg, #fffdfb, #fffaf6); }.app-card--orange .app-card__arrow { background: #fff1e6; color: #ff8339; }
.app-card--cyan { border-color: #dceefb; background: linear-gradient(115deg, #f9fdff, #f1faff); }.app-card--cyan .app-card__arrow { background: #e5f6ff; color: #168fe1; }
.empty-apps { grid-column: 1 / -1; padding: 70px 0; color: #8fa0c2; text-align: center; }

.platform-footer {
  display: flex;
  min-height: 106px;
  align-items: center;
  justify-content: center;
  width: min(1475px, calc(100% - 80px));
  margin: 64px auto 0;
  border-top: 1px solid #edf2f9;
  color: #6680b3;
  font-size: 16px;
  font-weight: 600;
  letter-spacing: 2px;
}

.platform-footer span { display: inline-flex; align-items: center; color: #6b83b0; }
.sr-only { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0, 0, 0, 0); white-space: nowrap; }

@media (max-width: 1120px) {
  .platform-apps { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .app-card { min-height: 142px; }
}

@media (max-width: 680px) {
  .platform-apps { width: calc(100% - 28px); grid-template-columns: 1fr; gap: 14px; margin-top: 28px; }
  .app-card { min-height: 110px; grid-template-columns: 64px minmax(0, 1fr) 38px; padding-left: 18px; }.app-card__icon { width: 58px; height: 58px; }.app-card__icon img { width: 58px; height: 58px; }.app-card strong { font-size: 17px; }.app-card__arrow { width: 38px; height: 38px; }
  .platform-footer { width: calc(100% - 28px); margin-top: 34px; font-size: 14px; letter-spacing: 1px; }
}
</style>
