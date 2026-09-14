import { defineStore } from 'pinia'

// 用户登录态(M1 接入后端认证后启用)
export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    username: localStorage.getItem('username') || '',
    role: localStorage.getItem('role') || '',
  }),
  getters: {
    isLogin: (state) => !!state.token,
    isAdmin: (state) => state.role === 'admin',
  },
  actions: {
    setAuth({ token, username, role }) {
      this.token = token
      this.username = username
      this.role = role
      localStorage.setItem('token', token)
      localStorage.setItem('username', username)
      localStorage.setItem('role', role)
    },
    logout() {
      this.token = ''
      this.username = ''
      this.role = ''
      localStorage.clear()
    },
  },
})
