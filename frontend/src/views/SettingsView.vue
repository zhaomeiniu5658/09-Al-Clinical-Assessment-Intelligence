<template>
  <AppShell title="系统设置" subtitle="配置临床评估平台的语音转录与智能质控服务">
    <div class="settings-page">
      <section class="settings-card">
        <div class="settings-card-header">
          <div class="settings-title-wrap">
            <div class="settings-icon"><el-icon><Microphone /></el-icon></div>
            <div>
              <h2>讯飞语音转录文本大模型</h2>
              <p>非实时语音转写大模型 · WebAPI</p>
            </div>
          </div>
          <span class="config-status" :class="isConfigured ? 'ready' : 'pending'"><i></i>{{ isConfigured ? '已配置' : '待配置' }}</span>
        </div>

        <el-divider />

        <el-form ref="formRef" class="settings-form" :model="form" :rules="rules" label-position="top">
          <div class="form-grid">
            <el-form-item label="模型名称" prop="model_name">
              <el-input v-model="form.model_name" placeholder="非实时语音转写大模型" />
            </el-form-item>
            <el-form-item label="WebAPI 地址" prop="web_api">
              <el-input v-model="form.web_api" placeholder="https://office-api-ist-dx.iflyaisol.com" />
            </el-form-item>
            <el-form-item label="APPID" prop="app_id">
              <el-input v-model="form.app_id" placeholder="请输入讯飞 APPID" />
            </el-form-item>
            <el-form-item label="APISecret" prop="api_secret">
              <el-input v-model="form.api_secret" type="password" show-password :placeholder="secretPlaceholder" autocomplete="new-password" @focus="prepareSecretInput('api_secret')" @blur="restoreSecretMask('api_secret')" />
            </el-form-item>
            <el-form-item label="APIKey" prop="api_key">
              <el-input v-model="form.api_key" type="password" show-password :placeholder="keyPlaceholder" autocomplete="new-password" @focus="prepareSecretInput('api_key')" @blur="restoreSecretMask('api_key')" />
            </el-form-item>
          </div>

          <el-form-item label="个性化热词" prop="hotwords">
            <el-input v-model="form.hotwords" type="textarea" :rows="5" placeholder="请输入需要优先识别的专业词汇，多个热词请按行填写" />
            <span class="field-hint">每行填写一个热词，例如：抑郁症、焦虑量表、心理评估</span>
          </el-form-item>

          <div class="form-footer">
            <span class="save-hint"><el-icon><Lock /></el-icon> APISecret 与 APIKey 仅用于当前平台的语音转录服务</span>
            <div class="form-actions">
              <el-button :disabled="saving" @click="loadSettings">取消修改</el-button>
              <el-button type="primary" :loading="saving" :icon="Check" @click="saveSettings">保存设置</el-button>
            </div>
          </div>
        </el-form>
      </section>
    </div>
  </AppShell>
</template>

<script setup lang="ts">
import { Check, Lock, Microphone } from '@element-plus/icons-vue'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'
import { fetchXfyunAsrSettings, updateXfyunAsrSettings } from '../api/settings'
import AppShell from '../components/AppShell.vue'

const formRef = ref<FormInstance>()
const loading = ref(true)
const saving = ref(false)
const secretConfigured = ref(false)
const keyConfigured = ref(false)
const maskedSecret = '********'
const form = reactive({ model_name: '非实时语音转写大模型', app_id: '', api_secret: '', api_key: '', web_api: 'https://office-api-ist-dx.iflyaisol.com', hotwords: '' })
const rules: FormRules = {
  model_name: [{ required: true, message: '请输入模型名称', trigger: 'blur' }],
  app_id: [{ required: true, message: '请输入 APPID', trigger: 'blur' }],
  web_api: [{ required: true, type: 'url', message: '请输入有效的 WebAPI 地址', trigger: 'blur' }]
}
const isConfigured = computed(() => secretConfigured.value && keyConfigured.value)
const secretPlaceholder = computed(() => secretConfigured.value ? maskedSecret : '请输入 APISecret')
const keyPlaceholder = computed(() => keyConfigured.value ? maskedSecret : '请输入 APIKey')

async function loadSettings() {
  loading.value = true
  try {
    const settings = await fetchXfyunAsrSettings()
    form.model_name = settings.model_name
    form.app_id = settings.app_id
    form.web_api = settings.web_api
    form.hotwords = settings.hotwords || ''
    form.api_secret = settings.api_secret_configured ? maskedSecret : ''
    form.api_key = settings.api_key_configured ? maskedSecret : ''
    secretConfigured.value = settings.api_secret_configured
    keyConfigured.value = settings.api_key_configured
  } finally { loading.value = false }
}
async function saveSettings() {
  await formRef.value?.validate()
  saving.value = true
  try {
    const settings = await updateXfyunAsrSettings({ model_name: form.model_name, app_id: form.app_id, web_api: form.web_api, hotwords: form.hotwords || undefined, api_secret: form.api_secret === maskedSecret ? undefined : form.api_secret || undefined, api_key: form.api_key === maskedSecret ? undefined : form.api_key || undefined })
    form.api_secret = settings.api_secret_configured ? maskedSecret : ''
    form.api_key = settings.api_key_configured ? maskedSecret : ''
    secretConfigured.value = settings.api_secret_configured
    keyConfigured.value = settings.api_key_configured
    ElMessage.success('讯飞语音转录设置已保存')
  } finally { saving.value = false }
}
function prepareSecretInput(field: 'api_secret' | 'api_key') {
  if (form[field] === maskedSecret) form[field] = ''
}
function restoreSecretMask(field: 'api_secret' | 'api_key') {
  const configured = field === 'api_secret' ? secretConfigured.value : keyConfigured.value
  if (configured && !form[field]) form[field] = maskedSecret
}
onMounted(loadSettings)
</script>

<style scoped>
.settings-page { max-width: 1080px; margin: 8px auto 0; }.settings-card { padding: 28px 32px 24px; border: 1px solid #e8ebf2; border-radius: 8px; background: #fff; box-shadow: 0 4px 16px rgba(15, 23, 42, .035); }.settings-card-header { display: flex; align-items: center; justify-content: space-between; gap: 20px; }.settings-title-wrap { display: flex; align-items: center; gap: 14px; }.settings-icon { display: grid; width: 44px; height: 44px; place-items: center; border-radius: 10px; background: #eef0ff; color: #6366f1; font-size: 21px; }.settings-title-wrap h2, .settings-title-wrap p { margin: 0; }.settings-title-wrap h2 { color: #1f2937; font-size: 18px; }.settings-title-wrap p { margin-top: 5px; color: #8b95a5; font-size: 13px; }.config-status { display: inline-flex; align-items: center; gap: 7px; padding: 6px 10px; border-radius: 6px; font-size: 12px; }.config-status i { width: 6px; height: 6px; border-radius: 50%; }.config-status.ready { background: #ecfdf5; color: #10b981; }.config-status.ready i { background: #10b981; }.config-status.pending { background: #fffbeb; color: #d97706; }.config-status.pending i { background: #f59e0b; }.settings-card :deep(.el-divider) { margin: 24px 0; border-color: #edf0f5; }.settings-form { max-width: 900px; }.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0 26px; }.settings-form :deep(.el-form-item__label) { padding-bottom: 8px; color: #374151; font-size: 14px; }.settings-form :deep(.el-form-item) { margin-bottom: 21px; }.field-hint { display: block; margin-top: 7px; color: #9ca3af; font-size: 12px; }.form-footer { display: flex; align-items: center; justify-content: space-between; gap: 18px; margin-top: 7px; padding-top: 22px; border-top: 1px solid #edf0f5; }.save-hint { display: inline-flex; align-items: center; gap: 6px; color: #8b95a5; font-size: 12px; }.form-actions { display: flex; gap: 10px; flex-shrink: 0; }
@media (max-width: 720px) { .settings-card { padding: 22px 18px; }.settings-card-header { align-items: flex-start; flex-direction: column; }.form-grid { grid-template-columns: 1fr; }.form-footer { align-items: flex-start; flex-direction: column; }.form-actions { width: 100%; }.form-actions .el-button { flex: 1; } }
</style>
