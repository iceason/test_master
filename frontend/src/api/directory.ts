import { request } from '@/utils/axios'

// 目录相关接口
export interface Directory {
  id: number
  name: string
  parent?: number | null
  level: number
  order: number
  sub_directories?: Directory[]
  description?: string
}

export const getDirectories = () => {
  return request<Directory[]>({
    url: 'directories/',
    method: 'get'
  })
}

export const createDirectory = (data: Partial<Directory>) => {
  return request<Directory>({
    url: 'directories/',
    method: 'post',
    data
  })
}

export const updateDirectory = (id: number, data: Partial<Directory>) => {
  return request<Directory>({
    url: `directories/${id}/`,
    method: 'put',
    data
  })
}

export const deleteDirectory = (id: number) => {
  return request<void>({
    url: `directories/${id}/`,
    method: 'delete'
  })
}
