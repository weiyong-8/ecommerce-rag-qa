<template>
  <div class="login-wrap">
    <el-card class="login-card">
      <h2 class="login-title">🛒 电商知识库问答系统</h2>
      <el-tabs v-model="tab" stretch>
        <el-tab-pane label="登录" name="login">
          <el-form :model="loginForm" size="large" @keyup.enter="handleLogin">
            <el-form-item>
              <el-input v-model="loginForm.username" placeholder="用户名" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="loginForm.password"
                type="password"
                placeholder="密码"
                show-password
              />
            </el-form-item>
            <el-button
              type="primary"
              class="w100"
              size="large"
              :loading="loading"
              @click="handleLogin"
            >
              登 录
            </el-button>
          </el-form>
        </el-tab-pane>
        <el-tab-pane label="注册" name="register">
          <el-form :model="regForm" size="large" @keyup.enter="handleRegister">
            <el-form-item>
              <el-input v-model="regForm.username" placeholder="用户名(3-32 位字母/数字/中文)" />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="regForm.password"
                type="password"
                placeholder="密码(至少 6 位)"
                show-password
              />
            </el-form-item>
            <el-form-item>
              <el-input
                v-model="regForm.confirm"
                type="password"
                placeholder="确认密码"
                show-password
              />
            </el-form-item>
            <el-button
              type="primary"
              class="w100"
              size="large"
              :loading="loading"
              @click="handleRegister"
            >
              注 册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { login, register } from '../api/auth'
import { extractErrMsg } from '../api/request'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const tab = ref('login')
const loading = ref(false)
const loginForm = reactive({ username: '', password: '' })
const regForm = reactive({ username: '', password: '', confirm: '' })

async function handleLogin() {
  if (!loginForm.username || !loginForm.password) {
    return ElMessage.warning('请输入用户名和密码')
  }
  loading.value = true
  try {
    const res = await login({ username: loginForm.username, password: loginForm.password })
    userStore.setAuth({ token: res.access_token, username: res.user.username, role: res.user.role })
    ElMessage.success(`欢迎回来,${res.user.username}`)
    router.push(route.query.redirect || '/')
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!regForm.username || regForm.password.length < 6) {
    return ElMessage.warning('用户名至少 3 位,密码至少 6 位')
  }
  if (regForm.password !== regForm.confirm) {
    return ElMessage.warning('两次输入的密码不一致')
  }
  loading.value = true
  try {
    await register({ username: regForm.username, password: regForm.password })
    ElMessage.success('注册成功,请登录')
    loginForm.username = regForm.username
    loginForm.password = ''
    tab.value = 'login'
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrap {
  display: flex;
  justify-content: center;
  padding-top: 8vh;
}
.login-card {
  width: 420px;
}
.login-title {
  text-align: center;
  margin-bottom: 16px;
}
.w100 {
  width: 100%;
}
</style>
