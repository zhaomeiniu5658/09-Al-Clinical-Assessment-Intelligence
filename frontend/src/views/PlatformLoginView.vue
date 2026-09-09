<template>
  <main class="platform-login">
    <div class="platform-login__visual" aria-hidden="true">
      <img src="/platform/login-left.png" alt="" />
    </div>

    <section class="platform-login__panel" aria-labelledby="platform-login-title">
      <div class="platform-login__brand" aria-label="夸克医药">
        <span class="brand-word">Quarkmed</span>
        <strong>夸克医药</strong>
      </div>

      <div class="platform-login__heading">
        <h1 id="platform-login-title">欢迎登录 <em>夸克智汇平台</em></h1>
        <p>汇聚医药数据 · 赋能业务发展</p>
      </div>

      <form class="platform-login__form" @submit.prevent="handleLogin">
        <label class="platform-input">
          <el-icon><User /></el-icon>
          <input v-model="form.username" type="text" autocomplete="username" placeholder="请输入账号" />
        </label>
        <label class="platform-input">
          <el-icon><Lock /></el-icon>
          <input v-model="form.password" :type="passwordVisible ? 'text' : 'password'" autocomplete="current-password" placeholder="请输入密码" />
          <button class="input-action" type="button" aria-label="显示或隐藏密码" @click="passwordVisible = !passwordVisible">
            <el-icon><View v-if="!passwordVisible" /><Hide v-else /></el-icon>
          </button>
        </label>

        <div class="platform-login__options">
          <label class="remember-option">
            <input v-model="form.remember" type="checkbox" />
            <span class="fake-checkbox"><el-icon><Check /></el-icon></span>
            <span>记住账号</span>
          </label>
          <button class="forgot-link" type="button" @click="showForgotMessage">忘记密码?</button>
        </div>

        <button class="platform-login__submit" type="submit">
          <span>登录</span>
          <el-icon><ArrowRight /></el-icon>
        </button>
      </form>

      <p class="platform-login__slogan">—&nbsp;&nbsp;专业 · 安全 · 高效&nbsp;&nbsp;—</p>
    </section>
  </main>
</template>

<script setup lang="ts">
import { ArrowRight, Check, Hide, Lock, User, View } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const passwordVisible = ref(false)
const form = reactive({
  username: localStorage.getItem('platform_username') || '',
  password: '',
  remember: localStorage.getItem('platform_remember') === 'true'
})

function handleLogin() {
  if (form.remember) localStorage.setItem('platform_username', form.username)
  else localStorage.removeItem('platform_username')
  localStorage.setItem('platform_remember', String(form.remember))
  ElMessage.success('登录成功')
  router.push({ name: 'platform-home' })
}

function showForgotMessage() {
  ElMessage.info('密码找回功能暂未开放')
}
</script>

<style scoped>
.platform-login {
  position: relative;
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(520px, 44vw);
  min-height: 100vh;
  overflow: hidden;
  align-items: center;
  justify-items: center;
  background:
    radial-gradient(circle at 58% 42%, rgba(255, 255, 255, .82), transparent 34%),
    linear-gradient(115deg, #eef7ff 0%, #dceeff 53%, #edf7ff 100%);
}

.platform-login__visual {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.platform-login__visual::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, transparent 49%, rgba(232, 244, 255, .55) 100%);
  content: '';
}

.platform-login__visual img {
  width: auto;
  height: 100%;
  max-width: none;
}

.platform-login__panel {
  position: relative;
  z-index: 1;
  grid-column: 2;
  justify-self: center;
  width: min(500px, calc(100vw - 40px));
  min-height: 656px;
  padding: 56px 46px 38px;
  border: 1px solid rgba(255, 255, 255, .92);
  border-radius: 16px;
  background: rgba(255, 255, 255, .84);
  box-shadow: 0 18px 52px rgba(92, 153, 224, .14);
  backdrop-filter: blur(10px);
}

.platform-login__brand {
  display: flex;
  flex-direction: column;
  align-items: center;
  color: #0e1c50;
}

.brand-word {
  font-family: Arial, "Helvetica Neue", sans-serif;
  font-size: 40px;
  font-weight: 700;
  letter-spacing: -2.2px;
  line-height: 1;
}

.brand-word::first-letter { letter-spacing: -5px; }

.platform-login__brand strong {
  margin-top: 8px;
  font-size: 18px;
  letter-spacing: 1px;
}

.platform-login__heading {
  margin-top: 36px;
  text-align: center;
}

.platform-login__heading h1 {
  margin: 0;
  color: #111d50;
  font-size: 25px;
  font-weight: 700;
  letter-spacing: 1px;
}

.platform-login__heading em {
  color: #4568f2;
  font-style: normal;
}

.platform-login__heading p {
  margin: 12px 0 0;
  color: #9aaaca;
  font-size: 16px;
  letter-spacing: 1px;
}

.platform-login__form { margin-top: 38px; }

.platform-input {
  display: flex;
  align-items: center;
  height: 56px;
  margin-top: 22px;
  padding: 0 17px;
  border: 1px solid #dce5f2;
  border-radius: 12px;
  background: rgba(255, 255, 255, .74);
  color: #9aabc8;
  transition: border-color .2s, box-shadow .2s;
}

.platform-input:first-child { margin-top: 0; }
.platform-input:focus-within { border-color: #6ca5fa; box-shadow: 0 0 0 3px rgba(76, 141, 245, .12); }
.platform-input > .el-icon { flex: 0 0 auto; font-size: 21px; }
.platform-input input { min-width: 0; flex: 1; border: 0; outline: 0; padding: 0 14px; background: transparent; color: #273a68; font-size: 16px; }
.platform-input input::placeholder { color: #a8b6cd; }
.input-action { display: grid; width: 25px; height: 30px; place-items: center; border: 0; background: transparent; color: #9babc5; cursor: pointer; }

.platform-login__options {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-top: 21px;
  color: #91a1bf;
  font-size: 15px;
}

.remember-option { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; }
.remember-option input { position: absolute; width: 1px; height: 1px; opacity: 0; }
.fake-checkbox { display: grid; width: 19px; height: 19px; place-items: center; border: 1px solid #a8bad8; border-radius: 4px; color: transparent; }
.remember-option input:checked + .fake-checkbox { border-color: #367bf4; background: #367bf4; color: #fff; }
.fake-checkbox .el-icon { font-size: 14px; font-weight: 700; }
.forgot-link { border: 0; background: transparent; color: #346ff0; font-size: 15px; cursor: pointer; }

.platform-login__submit {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  width: 100%;
  height: 57px;
  margin-top: 31px;
  border: 0;
  border-radius: 12px;
  background: linear-gradient(100deg, #20a1f0 0%, #3b80f4 46%, #5e38ee 100%);
  box-shadow: 0 11px 24px rgba(66, 112, 235, .18);
  color: #fff;
  font-size: 17px;
  font-weight: 600;
  cursor: pointer;
  transition: transform .2s, box-shadow .2s;
}

.platform-login__submit:hover { transform: translateY(-1px); box-shadow: 0 14px 28px rgba(66, 112, 235, .25); }
.platform-login__submit .el-icon { font-size: 20px; }
.platform-login__slogan { margin: 76px 0 0; color: #9baaca; font-size: 15px; letter-spacing: 1px; text-align: center; }

@media (max-width: 1050px) {
  .platform-login { grid-template-columns: minmax(0, 1fr) minmax(480px, 52vw); }
  .platform-login__visual img { width: max(100%, 1024px); object-fit: cover; object-position: left center; }
}

@media (max-width: 720px) {
  .platform-login { grid-template-columns: 1fr; place-items: center; padding: 20px; }
  .platform-login__visual { opacity: .42; }
  .platform-login__panel { grid-column: 1; width: min(500px, 100%); min-height: 0; margin: 0; padding: 38px 24px 30px; }
  .platform-login__heading { margin-top: 28px; }
  .platform-login__heading h1 { font-size: 21px; }
  .platform-login__heading p { font-size: 13px; }
  .platform-login__form { margin-top: 30px; }
  .platform-login__slogan { margin-top: 48px; }
}
</style>
