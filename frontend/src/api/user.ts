import { request } from '@/utils/axios'

// 用户类型定义
export interface User {
  id: number
  name: string
  email: string
}

// 获取用户个人信息
export const getUserProfile = () => {
  return request<User>({
    url: 'users/me',
    method: 'get'
  })
}

// 更新用户个人信息
export const updateUserProfile = (data: Partial<User>) => {
  return request<User>({
    url: 'users/me',
    method: 'put',
    data
  })
}
