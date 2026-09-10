<template>
  <main class="platform-home">
    <header class="platform-header">
      <RouterLink class="platform-logo" to="/platform" aria-label="夸克智汇平台首页">
        <span class="platform-logo__word">Quarkmed</span>
        <strong>夸克医药</strong>
      </RouterLink>

      <div class="platform-header__tools">
        <label class="platform-search">
          <el-icon><Search /></el-icon>
          <input v-model="searchText" type="search" placeholder="搜索平台、知识、数据..." />
        </label>
        <button class="platform-avatar" aria-label="用户中心" type="button" @click="showUserMessage">
          <el-icon><User /></el-icon>
        </button>
      </div>
    </header>

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
        <strong>{{ app.name }}</strong>
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
import { ArrowRight, Search, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'

type AppTone = 'blue' | 'purple' | 'teal' | 'orange' | 'cyan'
type PlatformApp = {
  name: string
  tone: AppTone
  icon: string
}

const searchText = ref('')
const apps: PlatformApp[] = [
  { name: '智核引擎AI', tone: 'blue', icon: 'ai.svg' },
  { name: '智能BI看板', tone: 'purple', icon: 'bi.svg' },
  { name: '运营工作台', tone: 'teal', icon: 'ops.svg' },
  { name: '医药BD交易商机', tone: 'orange', icon: 'bd.svg' },
  { name: '医学研究平台', tone: 'cyan', icon: 'research.svg' },
  { name: 'sCTMS', tone: 'purple', icon: 'sctms.svg' },
  { name: '药物警戒', tone: 'blue', icon: 'pv.svg' },
  { name: '临床评估量表', tone: 'purple', icon: 'scale.svg' }
]

const filteredApps = computed(() => {
  const keyword = searchText.value.trim().toLowerCase()
  return keyword ? apps.filter((app) => app.name.toLowerCase().includes(keyword)) : apps
})

function openApp(app: PlatformApp) {
  ElMessage.info(`${app.name} 页面正在建设中`)
}

function showUserMessage() {
  ElMessage.info('用户中心暂未开放')
}
</script>

<style scoped>
.platform-home {
  min-height: 100vh;
  overflow-x: hidden;
  background: #fff;
  color: #10245d;
}

.platform-header {
  display: flex;
  height: 80px;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  padding: 0 clamp(28px, 4vw, 70px);
  background: rgba(255, 255, 255, .95);
}

.platform-logo {
  display: flex;
  flex-direction: column;
  color: #10245d;
  text-decoration: none;
}

.platform-logo__word {
  font-family: Arial, "Helvetica Neue", sans-serif;
  font-size: 35px;
  font-weight: 700;
  letter-spacing: -2px;
  line-height: .9;
}

.platform-logo strong { margin: 6px 0 0 45px; font-size: 17px; letter-spacing: 1px; }
.platform-header__tools { display: flex; align-items: center; gap: 28px; }
.platform-search { display: flex; width: min(465px, 40vw); height: 45px; align-items: center; gap: 12px; padding: 0 18px; border-radius: 24px; background: #edf5ff; color: #7192ca; }
.platform-search .el-icon { font-size: 22px; }
.platform-search input { min-width: 0; flex: 1; border: 0; outline: 0; background: transparent; color: #234274; font-size: 15px; }
.platform-search input::placeholder { color: #9cb0d1; }
.platform-avatar { display: grid; width: 45px; height: 45px; place-items: center; border: 0; border-radius: 50%; background: #edf5ff; color: #3968ad; font-size: 23px; cursor: pointer; }

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
.app-card strong { font-size: 20px; font-weight: 600; white-space: nowrap; }
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
  .platform-header { height: 70px; padding: 0 18px; }
  .platform-logo__word { font-size: 28px; }.platform-logo strong { margin-left: 35px; font-size: 13px; }
  .platform-header__tools { gap: 10px; }.platform-search { width: 44px; padding: 0 11px; }.platform-search input { display: none; }
  .platform-apps { width: calc(100% - 28px); grid-template-columns: 1fr; gap: 14px; margin-top: 28px; }
  .app-card { min-height: 110px; grid-template-columns: 64px minmax(0, 1fr) 38px; padding-left: 18px; }.app-card__icon { width: 58px; height: 58px; }.app-card__icon img { width: 58px; height: 58px; }.app-card strong { font-size: 17px; }.app-card__arrow { width: 38px; height: 38px; }
  .platform-footer { width: calc(100% - 28px); margin-top: 34px; font-size: 14px; letter-spacing: 1px; }
}
</style>
