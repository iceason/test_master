import { request } from '@/utils/axios'

export interface Project {
  id: number
  name: string
  description: string
  order: number
  created_by: number | null
  created_by_name: string | null
  created_at: string
  member_count: number
}

export interface ProjectMember {
  id: number
  user_id: number
  username: string
  email: string
  role: string
  role_display: string
  joined_at: string
}

export interface SimpleUser {
  id: number
  username: string
  email: string
}

export const getProjects = () => {
  return request<Project[]>({
    url: 'projects/',
    method: 'get',
  })
}

export const createProject = (data: Partial<Project>) => {
  return request<Project>({
    url: 'projects/',
    method: 'post',
    data,
  })
}

export const updateProject = (id: number, data: Partial<Project>) => {
  return request<Project>({
    url: `projects/${id}/`,
    method: 'put',
    data,
  })
}

export const deleteProject = (id: number) => {
  return request<void>({
    url: `projects/${id}/`,
    method: 'delete',
  })
}

export const getProjectMembers = (id: number) => {
  return request<ProjectMember[]>({
    url: `projects/${id}/members/`,
    method: 'get',
  })
}

export const addProjectMember = (id: number, data: { user_id: number; role: string }) => {
  return request<ProjectMember>({
    url: `projects/${id}/add_member/`,
    method: 'post',
    data,
  })
}

export const removeProjectMember = (id: number, userId: number) => {
  return request<{ status: string }>({
    url: `projects/${id}/remove_member/`,
    method: 'post',
    data: { user_id: userId },
  })
}

export const updateMemberRole = (id: number, data: { user_id: number; role: string }) => {
  return request<ProjectMember>({
    url: `projects/${id}/update_member_role/`,
    method: 'post',
    data,
  })
}

export const searchUsers = (search: string) => {
  return request<SimpleUser[]>({
    url: 'users/',
    method: 'get',
    params: { search },
  })
}
