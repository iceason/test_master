import { defineStore } from 'pinia'
import { ref } from 'vue'
import { getToken, setToken as _setToken, removeToken, setRefreshToken, removeRefreshToken } from '@/utils/axios'
import { request } from '@/utils/axios'

interface LoginPayload {
  username: string
  password: string
}

interface TokenResponse {
  access: string
  refresh?: string
}

interface CurrentUserResponse {
  username: string
  roles: string[]
  id?: number
  name?: string
  email?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(getToken() || '')
  const username = ref<string>('')
  const roles = ref<string[]>([])

  const setToken = (value: string) => {
    _setToken(value)
    token.value = value
  }

  const login = async (loginData: LoginPayload) => {
    const data = await request<TokenResponse>({
      url: 'token/',
      method: 'post',
      data: loginData
    })
    setToken(data.access)
    if (data.refresh) {
      setRefreshToken(data.refresh)
    }
  }

  const getInfo = async () => {
    const data = await request<CurrentUserResponse>({
      url: 'users/me', // 对应 /api/users/me
      method: 'get'
    })
    username.value = data.username
    roles.value = data.roles || []
  }

  const logout = () => {
    removeToken()
    removeRefreshToken()
    token.value = ''
    roles.value = []
    window.location.reload()
  }

  return { token, username, roles, setToken, login, getInfo, logout }
})
