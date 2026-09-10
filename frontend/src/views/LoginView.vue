<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-brand">
        <h1>AI临床量表智能质控系统</h1>
        <p>单用户质控工作台</p>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" @submit.prevent="handleLogin">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" size="large" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input v-model="form.password" size="large" type="password" autocomplete="current-password" show-password />
        </el-form-item>
        <el-checkbox v-model="form.remember_me" class="remember-checkbox">记住密码</el-checkbox>
        <el-button class="login-button" type="primary" size="large" :loading="loading" @click="handleLogin">
          登录
        </el-button>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { nextTick, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({
  username: localStorage.getItem('remembered_username') || '',
  password: '',
  remember_me: localStorage.getItem('remember_login') === 'true'
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }]
}

async function handleLogin() {
  await formRef.value?.validate()
  loading.value = true
  try {
    await auth.login(form.username, form.password, form.remember_me)
    if (form.remember_me) {
      localStorage.setItem('remembered_username', form.username)
      localStorage.setItem('remember_login', 'true')
    } else {
      localStorage.removeItem('remembered_username')
      localStorage.removeItem('remember_login')
    }
    ElMessage.success('登录成功')
    await router.replace({ name: 'qc-list' })
    await nextTick()
    if (router.currentRoute.value.name !== 'qc-list') {
      window.location.assign('/')
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.remember-checkbox { margin: -4px 0 18px; }
</style>
