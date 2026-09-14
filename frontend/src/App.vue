<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <span class="title" style="cursor: pointer" @click="$router.push('/')">
        🛒 电商知识库问答系统
      </span>
      <div class="right">
        <nav v-if="userStore.isLogin" class="nav">
          <router-link to="/">问答</router-link>
          <router-link v-if="userStore.isAdmin" to="/admin">知识库管理</router-link>
        </nav>
        <el-dropdown v-if="userStore.isLogin" @command="onCommand">
          <span class="user-name">{{ userStore.username }} ▾</span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="password">修改密码</el-dropdown-item>
              <el-dropdown-item command="logout" divided>退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </el-header>
    <el-main>
      <router-view />
    </el-main>

    <!-- 修改密码弹窗 -->
    <el-dialog v-model="pwdVisible" title="修改密码" width="420px">
      <el-form :model="pwdForm" label-width="90px">
        <el-form-item label="原密码">
          <el-input v-model="pwdForm.old_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="pwdForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input v-model="pwdForm.confirm" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="pwdVisible = false">取消</el-button>
        <el-button type="primary" :loading="pwdLoading" @click="submitPassword">
          确认修改
        </el-button>
      </template>
    </el-dialog>
  </el-container>
</template>

<script setup>
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { changePassword } from './api/auth'
import { extractErrMsg } from './api/request'
import { useUserStore } from './stores/user'

const router = useRouter()
const userStore = useUserStore()

const pwdVisible = ref(false)
const pwdLoading = ref(false)
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

function onCommand(cmd) {
  if (cmd === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (cmd === 'password') {
    pwdForm.old_password = ''
    pwdForm.new_password = ''
    pwdForm.confirm = ''
    pwdVisible.value = true
  }
}

async function submitPassword() {
  if (!pwdForm.old_password || pwdForm.new_password.length < 6) {
    return ElMessage.warning('请填写原密码,新密码至少 6 位')
  }
  if (pwdForm.new_password !== pwdForm.confirm) {
    return ElMessage.warning('两次输入的新密码不一致')
  }
  pwdLoading.value = true
  try {
    await changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    ElMessage.success('密码修改成功')
    pwdVisible.value = false
  } catch (e) {
    ElMessage.error(extractErrMsg(e))
  } finally {
    pwdLoading.value = false
  }
}
</script>

<style>
body {
  margin: 0;
  font-family: 'Helvetica Neue', Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif;
}
.app-header {
  background: #001529;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.title {
  font-size: 18px;
  font-weight: 600;
}
.right {
  display: flex;
  align-items: center;
}
.nav a {
  color: rgba(255, 255, 255, 0.75);
  margin-right: 20px;
  text-decoration: none;
}
.nav a:hover,
.nav a.router-link-active {
  color: #fff;
}
.user-name {
  color: #fff;
  cursor: pointer;
  outline: none;
}
</style>
