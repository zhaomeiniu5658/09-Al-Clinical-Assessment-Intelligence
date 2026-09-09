<template>
  <main class="research-page">
    <header class="research-topbar">
      <RouterLink class="research-brand" to="/platform" aria-label="返回夸克智汇平台">
        <span>Quarkmed</span>
        <strong>夸克智汇平台</strong>
      </RouterLink>

      <nav class="research-global-nav" aria-label="平台导航">
        <RouterLink to="/platform">首页</RouterLink>
        <a href="#" @click.prevent="showComingSoon('智能引擎AI')">智能引擎AI</a>
        <a href="#" @click.prevent="showComingSoon('智能BI')">智能BI</a>
        <a href="#" @click.prevent="showComingSoon('市场调研')">市场调研</a>
        <a class="is-active" href="#" @click.prevent>CNS 商机</a>
        <a href="#" @click.prevent="showComingSoon('sCTMS')">sCTMS</a>
        <a href="#" @click.prevent="showComingSoon('药物警戒')">药物警戒</a>
        <a href="#" @click.prevent="showComingSoon('临床评估量表')">临床评估量表</a>
      </nav>

      <div class="research-topbar__actions">
        <label class="research-global-search">
          <el-icon><Search /></el-icon>
          <input v-model="globalSearch" type="search" placeholder="搜索平台、知识、数据..." />
        </label>
        <button class="research-user-button" type="button" aria-label="用户中心" @click="showComingSoon('用户中心')">
          <el-icon><User /></el-icon>
        </button>
      </div>
    </header>

    <div class="research-body">
      <section class="research-content">
        <section class="research-hero">
          <div class="research-hero__copy">
            <span class="research-hero__icon"><el-icon><FirstAidKit /></el-icon></span>
            <div>
              <h1>CNS领域商机挖掘</h1>
              <p>汇聚医学数据 · 驱动科研创新 · 加速新药研发</p>
            </div>
          </div>
        </section>

        <section class="research-workspace">
          <nav class="research-tabs" aria-label="研究数据分类">
            <button
              v-for="tab in tabs"
              :key="tab.label"
              type="button"
              :class="{ 'is-active': activeTab === tab.key }"
              @click="activeTab = tab.key"
            >
              <el-icon><component :is="tab.icon" /></el-icon>
              <span>{{ tab.label }}</span>
            </button>
          </nav>

          <div class="research-summary">
            <span>共 {{ filteredTrials.length || 236 }} 条记录</span>
          </div>

          <section class="research-metrics" aria-label="临床试验数据概览">
            <article v-for="metric in metrics" :key="metric.label" class="research-metric" :class="`metric--${metric.tone}`">
              <span class="research-metric__icon"><el-icon><component :is="metric.icon" /></el-icon></span>
              <span class="research-metric__copy">
                <strong>{{ metric.value }}<small>{{ metric.unit }}</small></strong>
                <span>{{ metric.label }}</span>
              </span>
              <el-icon class="research-metric__arrow"><ArrowRight /></el-icon>
            </article>
          </section>

          <section class="research-toolbar">
            <label class="trial-search">
              <el-icon><Search /></el-icon>
              <input v-model="searchText" type="search" placeholder="搜索登记号、药物名称、企业、适应症、靶点、试验阶段..." />
            </label>
            <label v-for="filter in filters" :key="filter" class="trial-filter">
              <select v-model="selectedFilters[filter]">
                <option value="">{{ filter }}</option>
                <option v-for="option in filterOptions[filter]" :key="option" :value="option">{{ option }}</option>
              </select>
              <el-icon><ArrowDown /></el-icon>
            </label>
            <button class="filter-button" type="button" @click="resetFilters"><el-icon><Filter /></el-icon><span>筛选</span></button>
            <button class="primary-action" type="button" @click="showComingSoon('新建课题')"><el-icon><Plus /></el-icon><span>新建课题</span></button>
          </section>

          <section class="trial-table-wrap">
            <div class="trial-table" role="table" aria-label="临床试验登记列表">
              <div class="trial-row trial-row--head" role="row">
                <span>序号</span>
                <span>登记号</span>
                <span>试验状态</span>
                <span>药物名称</span>
                <span>适应症</span>
                <span>申请人名称</span>
                <span>首次公示信息日期</span>
                <span>试验分期</span>
                <span>操作</span>
              </div>
              <div v-for="(trial, index) in visibleTrials" :key="trial.id" class="trial-row" role="row">
                <span class="trial-index">{{ index + 1 }}</span>
                <span class="trial-id"><span class="trial-file"><el-icon><Document /></el-icon></span>{{ trial.id }}</span>
                <span><span class="status-pill" :class="`status--${trial.statusTone}`"><i></i>{{ trial.status }}</span></span>
                <span>{{ trial.drug }}</span>
                <span class="trial-indication">{{ trial.indication }}</span>
                <span>{{ trial.applicant }}</span>
                <span>{{ trial.date }}</span>
                <span>{{ trial.phase }}</span>
                <span class="trial-actions">
                  <button type="button" @click="showComingSoon(`查看 ${trial.id}`)">查看</button>
                  <button type="button" aria-label="更多操作" @click="showComingSoon('更多操作')"><el-icon><MoreFilled /></el-icon></button>
                </span>
              </div>
              <div v-if="visibleTrials.length === 0" class="trial-empty">未找到匹配的试验记录</div>
            </div>
            <div class="trial-pagination">
              <button type="button" aria-label="上一页" @click="showComingSoon('上一页')"><el-icon><ArrowLeft /></el-icon></button>
              <button class="is-active" type="button">1</button>
              <button type="button">2</button>
              <button type="button">3</button>
              <button type="button">4</button>
              <button type="button">5</button>
              <span>...</span>
              <button type="button">24</button>
              <button type="button" aria-label="下一页" @click="showComingSoon('下一页')"><el-icon><ArrowRight /></el-icon></button>
            </div>
          </section>
        </section>
      </section>

      <aside class="research-assistant">
        <div class="assistant-heading">
          <span class="assistant-avatar"><el-icon><Cpu /></el-icon></span>
          <div><strong>智核AI</strong><small>您的CNS领域商机助手</small></div>
          <el-icon class="assistant-heading__arrow"><ArrowDown /></el-icon>
        </div>
        <div class="assistant-greeting">你好！我可以帮你：</div>
        <div class="assistant-suggestions">
          <button v-for="suggestion in suggestions" :key="suggestion.title" type="button" @click="showComingSoon(suggestion.title)">
            <span class="suggestion-icon" :class="`suggestion--${suggestion.tone}`"><el-icon><component :is="suggestion.icon" /></el-icon></span>
            <span><strong>{{ suggestion.title }}</strong><small>{{ suggestion.description }}</small></span>
            <el-icon><ArrowRight /></el-icon>
          </button>
        </div>
        <h2>热门推荐 <i></i></h2>
        <div class="assistant-recommendations">
          <button v-for="item in recommendations" :key="item.title" type="button" @click="showComingSoon(item.title)">
            <span class="recommendation-icon"><el-icon><Document /></el-icon></span>
            <span><strong>{{ item.title }}</strong><small><em>{{ item.tag }}</em>{{ item.date }}</small></span>
          </button>
        </div>
        <div class="assistant-input">
          <input v-model="assistantText" type="text" placeholder="请输入您的问题..." @keyup.enter="sendAssistantMessage" />
          <button type="button" aria-label="发送问题" @click="sendAssistantMessage"><el-icon><Promotion /></el-icon></button>
        </div>
        <p class="assistant-note">支持文献查询、数据分析、关系图谱等</p>
      </aside>
    </div>
  </main>
</template>

<script setup lang="ts">
import {
  Aim,
  ArrowDown,
  ArrowLeft,
  ArrowRight,
  Calendar,
  Connection,
  Cpu,
  Document,
  Files,
  Filter,
  FirstAidKit,
  MoreFilled,
  OfficeBuilding,
  Plus,
  Promotion,
  Search,
  Tickets,
  TrendCharts,
  User
} from '@element-plus/icons-vue'
import type { Component } from 'vue'
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'

type Tone = 'blue' | 'purple' | 'teal' | 'orange'
type Trial = {
  id: string
  status: string
  statusTone: Tone
  drug: string
  indication: string
  applicant: string
  date: string
  phase: string
  tab: string
}

const globalSearch = ref('')
const searchText = ref('')
const assistantText = ref('')
const activeTab = ref('trial')
const tabs = [
  { key: 'trial', label: '2026年新登记临床试验', icon: FirstAidKit },
  { key: 'investment', label: '投融资信息及股权分布', icon: OfficeBuilding },
  { key: 'network', label: '社会关系图谱', icon: Connection },
  { key: 'news', label: '投融资新闻', icon: Tickets }
]
const metrics = [
  { value: '236', unit: '条', label: '临床试验', tone: 'blue', icon: FirstAidKit },
  { value: '48', unit: '家', label: '企业', tone: 'purple', icon: OfficeBuilding },
  { value: '96', unit: '个', label: '适应症', tone: 'teal', icon: Aim },
  { value: '18', unit: '条', label: '今日更新', tone: 'blue', icon: Calendar }
]
const filters = ['试验状态', '适应症', '企业', '日期范围', '试验分期']
const filterOptions: Record<string, string[]> = {
  试验状态: ['进行中', '待审核', '已完成', '已停止'],
  适应症: ['肿瘤', '免疫疾病', '代谢疾病'],
  企业: ['照源安健医药（北京）有限公司', '中国科学院上海药物研究所', '文达医药'],
  日期范围: ['近一周', '近一个月', '近一年'],
  试验分期: ['I期', 'II期', 'III期']
}
const selectedFilters = reactive<Record<string, string>>({})
filters.forEach((filter) => { selectedFilters[filter] = '' })
const trials: Trial[] = [
  { id: 'CTR20263294', status: '进行中', statusTone: 'teal', drug: 'BR005-036C片', indication: '成人有发烧或无发泡状细胞腺癌', applicant: '照源安健医药（北京）有限公司', date: '2026-08-28', phase: 'II / III期', tab: 'trial' },
  { id: 'CTR20263262', status: '待审核', statusTone: 'blue', drug: 'SHR-1701片', indication: '晚期实体瘤', applicant: '中国科学院上海药物研究所', date: '2026-08-24', phase: 'I期', tab: 'trial' },
  { id: 'CTR20263117', status: '进行中', statusTone: 'teal', drug: 'WD-910片', indication: '阿尔茨海默病', applicant: '文达医药', date: '2026-08-20', phase: 'I期', tab: 'trial' },
  { id: 'CTR20263056', status: '已完成', statusTone: 'purple', drug: 'IBN617肠溶胶囊', indication: '抑郁症', applicant: '合肥润德生物科技有限公司', date: '2026-08-18', phase: 'II期', tab: 'trial' },
  { id: 'CTR20263055', status: '已停止', statusTone: 'blue', drug: 'DM1001制剂', indication: '本品用于治疗成人特发性全身强直痉挛的体征和症状。', applicant: '复星万邦（江苏）医药集团有限公司', date: '2026-08-18', phase: 'II / III期', tab: 'trial' },
  { id: 'CTR20262873', status: '进行中', statusTone: 'teal', drug: 'AI辅助的药物靶点筛选与验证', indication: '肿瘤', applicant: '北京大学医学部', date: '2026-08-08', phase: 'I期', tab: 'trial' }
]
const suggestions: { title: string; description: string; tone: Tone; icon: Component }[] = [
  { title: '推荐相关文献', description: '基于研究方向智能推荐', tone: 'blue', icon: Files },
  { title: '生成研究摘要', description: '一键生成专业摘要', tone: 'purple', icon: Document },
  { title: '查看关系图谱', description: '洞察研究机构与合作网络', tone: 'blue', icon: Connection },
  { title: '分析企业投融资', description: '挖掘企业动态与投资信息', tone: 'teal', icon: TrendCharts }
]
const recommendations = [
  { title: 'PD-1抑制剂在肺癌中的研究进展', tag: '综述', date: '2024-12-12' },
  { title: '真实世界研究在临床试验中的应用', tag: '研究', date: '2024-11-28' },
  { title: '全球肿瘤药物研发趋势分析', tag: '分析', date: '2024-10-15' }
]

const filteredTrials = computed(() => {
  const keyword = `${searchText.value} ${globalSearch.value}`.trim().toLowerCase()
  return trials.filter((trial) => {
    const matchesTab = activeTab.value === 'trial' ? trial.tab === 'trial' : false
    const matchesKeyword = !keyword || Object.values(trial).join(' ').toLowerCase().includes(keyword)
    const matchesStatus = !selectedFilters['试验状态'] || trial.status === selectedFilters['试验状态']
    const matchesPhase = !selectedFilters['试验分期'] || trial.phase.includes(selectedFilters['试验分期'])
    return matchesTab && matchesKeyword && matchesStatus && matchesPhase
  })
})
const visibleTrials = computed(() => filteredTrials.value.slice(0, 5))

function resetFilters() {
  searchText.value = ''
  globalSearch.value = ''
  filters.forEach((filter) => { selectedFilters[filter] = '' })
}

function showComingSoon(name: string) {
  ElMessage.info(`${name}功能为静态演示`)
}

function sendAssistantMessage() {
  if (!assistantText.value.trim()) return
  ElMessage.success('已记录问题，接口接入后将由智核AI回答')
  assistantText.value = ''
}
</script>

<style scoped>
.research-page { min-height: 100vh; overflow: hidden; background: #f7fbff; color: #12377f; }
.research-topbar { position: relative; z-index: 3; display: flex; height: 72px; align-items: center; gap: 38px; padding: 0 34px 0 42px; border-bottom: 1px solid #e8f0fa; background: rgba(255, 255, 255, .94); }
.research-brand { display: flex; width: 158px; flex: 0 0 158px; flex-direction: column; color: #0c58cf; text-decoration: none; }
.research-brand span { font: 700 28px/1 Arial, "Helvetica Neue", sans-serif; letter-spacing: -1.7px; }.research-brand strong { margin: 4px 0 0 27px; color: #153e8e; font-size: 14px; letter-spacing: .7px; }
.research-global-nav { display: flex; height: 100%; align-items: center; gap: 31px; min-width: 0; flex: 1; }
.research-global-nav a { position: relative; display: inline-flex; height: 100%; align-items: center; color: #49679b; font-size: 14px; text-decoration: none; white-space: nowrap; }
.research-global-nav a:hover, .research-global-nav a.is-active { color: #1268e9; font-weight: 600; }.research-global-nav a.is-active::after { position: absolute; right: 0; bottom: 0; left: 0; height: 3px; border-radius: 3px 3px 0 0; background: #1679f6; content: ''; }
.research-topbar__actions { display: flex; flex: 0 0 auto; align-items: center; gap: 20px; }.research-global-search { display: flex; width: min(398px, 25vw); height: 40px; align-items: center; gap: 10px; padding: 0 16px; border-radius: 22px; background: #eef6ff; color: #5c8dd3; }.research-global-search input { min-width: 0; flex: 1; border: 0; outline: 0; background: transparent; color: #294c86; font-size: 13px; }.research-global-search input::placeholder { color: #9bb6d9; }.research-user-button { display: grid; width: 40px; height: 40px; place-items: center; border: 1px solid #deebf9; border-radius: 50%; background: #f5faff; color: #0e6bf1; font-size: 22px; cursor: pointer; }

.research-body { display: grid; min-height: calc(100vh - 72px); grid-template-columns: minmax(0, 1fr) 316px; }

.research-content { min-width: 0; padding: 14px 14px 20px 38px; background: #f8fcff; }.research-hero { position: relative; display: flex; min-height: 148px; align-items: center; overflow: hidden; border: 1px solid #dceeff; border-radius: 16px; background: #e6f4ff url('/platform/research-hero-bg.png') right center / auto 100% no-repeat; }.research-hero::after { position: absolute; inset: 0; background: linear-gradient(90deg, rgba(239, 249, 255, .92), rgba(230, 245, 255, .16) 75%); content: ''; }.research-hero__copy { position: relative; z-index: 1; display: flex; align-items: center; gap: 24px; padding-left: 12px; }.research-hero__icon { display: grid; width: 108px; height: 108px; place-items: center; border-radius: 28px; background: linear-gradient(145deg, #62cbf5, #146ff0); box-shadow: 0 10px 21px rgba(40, 131, 232, .22); color: #fff; font-size: 58px; }.research-hero h1 { margin: 0; color: #0d3b91; font-size: clamp(30px, 2.8vw, 45px); font-weight: 700; letter-spacing: 1px; }.research-hero p { margin: 12px 0 0; color: #4271ae; font-size: 17px; letter-spacing: .8px; }

.research-workspace { margin-top: 10px; padding: 16px 16px 12px; border: 1px solid #e1edf9; border-radius: 16px; background: rgba(255, 255, 255, .8); box-shadow: 0 8px 28px rgba(71, 130, 202, .05); }.research-tabs { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; padding-bottom: 15px; border-bottom: 1px solid #edf3fa; }.research-tabs button { display: flex; min-width: 0; height: 46px; align-items: center; justify-content: center; gap: 11px; border: 1px solid #dceafa; border-radius: 12px; background: linear-gradient(105deg, #f8fcff, #fff); color: #5778a9; font: inherit; font-size: 13px; cursor: pointer; }.research-tabs button .el-icon { color: #5689ce; font-size: 20px; }.research-tabs button.is-active { border-color: #1682f3; background: linear-gradient(100deg, #1f89f6, #3e9cf6); box-shadow: 0 5px 12px rgba(31, 137, 246, .19); color: #fff; }.research-tabs button.is-active .el-icon { color: #fff; }.research-summary { margin: 13px 0 9px; color: #8ba4c5; font-size: 12px; }
.research-metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 14px; }.research-metric { display: flex; min-width: 0; min-height: 75px; align-items: center; gap: 13px; padding: 9px 14px; border: 1px solid #e2effb; border-radius: 13px; background: linear-gradient(110deg, #fbfdff, #eef7ff); }.research-metric__icon { display: grid; width: 46px; height: 46px; flex: 0 0 46px; place-items: center; border-radius: 50%; background: linear-gradient(145deg, #b8ddff, #368af6); box-shadow: 0 4px 10px rgba(66, 145, 237, .2); color: #fff; font-size: 24px; }.metric--purple .research-metric__icon { background: linear-gradient(145deg, #c3b2ff, #7467ed); }.metric--teal .research-metric__icon { background: linear-gradient(145deg, #75e3d7, #0dcab9); }.research-metric__copy { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 4px; }.research-metric__copy strong { color: #1250bb; font-size: 25px; line-height: 1; }.research-metric__copy strong small { margin-left: 5px; color: #4777b3; font-size: 12px; font-weight: 500; }.research-metric__copy > span { color: #6e8bb4; font-size: 12px; }.research-metric__arrow { color: #2f84ee; font-size: 16px; }

.research-toolbar { display: flex; min-width: 0; align-items: center; gap: 9px; margin-top: 18px; padding-bottom: 16px; border-bottom: 1px solid #edf3fa; }.trial-search { display: flex; min-width: 180px; height: 38px; flex: 1; align-items: center; gap: 9px; padding: 0 13px; border: 1px solid #dbe9f7; border-radius: 10px; background: #fff; color: #5389ce; }.trial-search input { min-width: 0; flex: 1; border: 0; outline: 0; color: #315e9c; font-size: 12px; }.trial-search input::placeholder { color: #9bb4d4; }.trial-filter { position: relative; display: flex; width: 86px; height: 38px; align-items: center; border: 1px solid #dbe9f7; border-radius: 10px; background: #fff; }.trial-filter select { width: 100%; height: 100%; appearance: none; border: 0; outline: 0; padding: 0 26px 0 11px; background: transparent; color: #5577a7; font-size: 12px; cursor: pointer; }.trial-filter .el-icon { position: absolute; right: 8px; pointer-events: none; color: #6b94c9; font-size: 13px; }.filter-button, .primary-action { display: inline-flex; height: 38px; align-items: center; justify-content: center; gap: 7px; border: 1px solid #dbe9f7; border-radius: 10px; padding: 0 14px; background: #fff; color: #5277a8; font: inherit; font-size: 12px; cursor: pointer; }.primary-action { border-color: #1682f3; background: linear-gradient(105deg, #1b8bf4, #2775ed); color: #fff; box-shadow: 0 5px 12px rgba(32, 126, 239, .16); }.primary-action .el-icon { font-size: 16px; }

.trial-table-wrap { overflow: auto; padding-top: 10px; }.trial-table { min-width: 930px; overflow: hidden; border: 1px solid #deebf8; border-radius: 12px; background: #fff; }.trial-row { display: grid; min-height: 62px; grid-template-columns: 44px 116px 92px 112px minmax(150px, 1.25fr) minmax(145px, 1.1fr) 112px 80px 104px; align-items: center; column-gap: 10px; padding: 0 12px; border-bottom: 1px solid #edf3fa; color: #446696; font-size: 12px; }.trial-row:last-child { border-bottom: 0; }.trial-row--head { min-height: 44px; background: linear-gradient(180deg, #f5faff, #eef6ff); color: #37649d; font-size: 11px; font-weight: 600; }.trial-id { display: flex; align-items: center; gap: 6px; color: #245ba9; }.trial-file { display: grid; width: 28px; height: 28px; place-items: center; border-radius: 9px; background: #eaf4ff; color: #207bf1; font-size: 15px; }.trial-indication { line-height: 1.5; }.status-pill { display: inline-flex; align-items: center; gap: 5px; padding: 4px 8px; border-radius: 99px; background: #e9f8f4; color: #0eb696; white-space: nowrap; }.status-pill i { width: 6px; height: 6px; border-radius: 50%; background: currentColor; }.status--blue { background: #eaf3ff; color: #2d88ef; }.status--purple { background: #f0eaff; color: #8157e8; }.trial-actions { display: flex; align-items: center; gap: 9px; }.trial-actions button { border: 0; background: transparent; color: #1677ed; font: inherit; cursor: pointer; }.trial-actions button:last-child { padding: 0; font-size: 16px; }.trial-empty { padding: 60px 0; color: #93a9c5; text-align: center; }.trial-pagination { display: flex; align-items: center; justify-content: flex-end; gap: 7px; padding-top: 9px; }.trial-pagination button { display: grid; width: 29px; height: 29px; place-items: center; border: 1px solid #dceafa; border-radius: 8px; background: #fff; color: #5a80b4; font: inherit; font-size: 11px; cursor: pointer; }.trial-pagination button.is-active { border-color: #1682f3; background: #1682f3; color: #fff; }.trial-pagination span { color: #7995ba; }

.research-assistant { position: relative; z-index: 2; display: flex; min-width: 0; flex-direction: column; margin: 14px 16px 20px 0; padding: 18px 16px 15px; overflow: hidden; border: 1px solid #dceaf7; border-radius: 16px; background: linear-gradient(180deg, rgba(248, 252, 255, .98), rgba(255, 255, 255, .96)); box-shadow: 0 10px 28px rgba(47, 117, 191, .08); }.assistant-heading { display: flex; align-items: center; gap: 11px; padding-bottom: 14px; }.assistant-avatar { display: grid; width: 44px; height: 44px; place-items: center; border-radius: 13px; background: linear-gradient(145deg, #58a7ff, #1769f1); box-shadow: 0 6px 12px rgba(46, 125, 238, .18); color: #fff; font-size: 24px; }.assistant-heading div { display: flex; min-width: 0; flex: 1; flex-direction: column; gap: 5px; }.assistant-heading strong { color: #153d86; font-size: 15px; }.assistant-heading small { color: #8ba9cf; font-size: 11px; }.assistant-heading__arrow { color: #5f88bd; font-size: 15px; }.assistant-greeting { padding: 13px; border: 1px solid #dcecfb; border-radius: 12px; background: #eef7ff; color: #35619b; font-size: 12px; }.assistant-suggestions { display: flex; flex-direction: column; gap: 8px; margin-top: 9px; }.assistant-suggestions button { display: grid; grid-template-columns: 34px minmax(0, 1fr) 14px; align-items: center; gap: 9px; min-height: 58px; border: 1px solid #edf3fa; border-radius: 12px; padding: 8px; background: #fff; color: #2d5a99; text-align: left; cursor: pointer; }.assistant-suggestions button:hover { border-color: #bddcff; background: #f7fbff; }.suggestion-icon { display: grid; width: 34px; height: 34px; place-items: center; border-radius: 10px; background: #eaf4ff; color: #2182f3; font-size: 17px; }.suggestion--purple { background: #f0eaff; color: #8157e8; }.suggestion--teal { background: #e6fbf7; color: #0db7a3; }.assistant-suggestions strong, .assistant-suggestions small { display: block; }.assistant-suggestions strong { font-size: 12px; }.assistant-suggestions small { margin-top: 3px; color: #9ab1ce; font-size: 10px; }.assistant-suggestions > button > .el-icon { color: #4389d5; font-size: 14px; }.research-assistant h2 { display: flex; align-items: center; gap: 10px; margin: 22px 0 11px; color: #214e92; font-size: 13px; }.research-assistant h2 i { display: block; width: 24px; height: 1px; background: #c7d9ee; }.assistant-recommendations { display: flex; flex-direction: column; gap: 10px; }.assistant-recommendations button { display: grid; grid-template-columns: 37px minmax(0, 1fr); align-items: center; gap: 9px; border: 0; padding: 0; background: transparent; color: #2c5995; text-align: left; cursor: pointer; }.recommendation-icon { display: grid; width: 37px; height: 37px; place-items: center; border-radius: 11px; background: linear-gradient(145deg, #eef6ff, #dbeaff); color: #217ef0; font-size: 19px; }.assistant-recommendations strong { display: block; overflow: hidden; font-size: 11px; text-overflow: ellipsis; white-space: nowrap; }.assistant-recommendations small { display: flex; align-items: center; gap: 8px; margin-top: 5px; color: #91a9c7; font-size: 10px; }.assistant-recommendations em { padding: 2px 6px; border-radius: 99px; background: #edf5ff; color: #5c8bd0; font-style: normal; }.assistant-input { display: flex; height: 42px; align-items: center; gap: 8px; margin-top: auto; padding: 0 7px 0 13px; border: 1px solid #dbeafa; border-radius: 12px; background: #fff; }.assistant-input input { min-width: 0; flex: 1; border: 0; outline: 0; color: #315e9c; font-size: 11px; }.assistant-input input::placeholder { color: #a0b6d0; }.assistant-input button { display: grid; width: 29px; height: 29px; place-items: center; border: 0; border-radius: 50%; background: #398cf2; color: #fff; cursor: pointer; }.assistant-note { margin: 10px 0 0; color: #96adca; font-size: 10px; }

@media (max-width: 1320px) { .research-topbar { gap: 20px; padding-left: 25px; }.research-global-nav { gap: 18px; }.research-body { grid-template-columns: minmax(0, 1fr); }.research-assistant { position: fixed; right: 15px; bottom: 15px; width: 316px; max-height: calc(100vh - 105px); }.research-content { padding-left: 18px; }.research-toolbar { flex-wrap: wrap; }.trial-search { flex-basis: 100%; }.research-assistant .assistant-input { margin-top: 20px; } }
@media (max-width: 860px) { .research-topbar { height: auto; min-height: 72px; flex-wrap: wrap; padding: 14px 18px; }.research-brand { width: 140px; flex-basis: 140px; }.research-global-nav { order: 3; width: 100%; height: 38px; flex-basis: 100%; gap: 20px; overflow-x: auto; }.research-global-nav a { height: 38px; }.research-topbar__actions { margin-left: auto; }.research-body { display: block; }.research-content { padding: 10px; }.research-assistant { display: none; }.research-hero__copy { padding-left: 22px; }.research-workspace { padding: 12px; }.research-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 560px) { .research-global-search { width: 42px; padding: 0 12px; }.research-global-search input { display: none; }.research-topbar__actions { gap: 9px; }.research-hero { min-height: 130px; }.research-hero__icon { width: 64px; height: 64px; border-radius: 18px; font-size: 35px; }.research-hero__copy { gap: 13px; padding-left: 16px; }.research-hero h1 { font-size: 25px; }.research-hero p { margin-top: 7px; font-size: 12px; }.research-tabs { grid-template-columns: repeat(2, minmax(0, 1fr)); }.research-tabs button { height: 42px; font-size: 11px; }.research-metrics { gap: 8px; }.research-metric { gap: 8px; min-height: 68px; padding: 7px; }.research-metric__icon { width: 36px; height: 36px; flex-basis: 36px; font-size: 18px; }.research-metric__copy strong { font-size: 19px; }.research-metric__copy > span { font-size: 10px; }.research-toolbar { gap: 7px; }.trial-filter { flex: 1; }.filter-button, .primary-action { flex: 1; padding: 0 8px; }.research-brand span { font-size: 24px; }.research-brand strong { margin-left: 21px; font-size: 11px; } }
</style>
