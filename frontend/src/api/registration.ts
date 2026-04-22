import { request } from '@/utils/axios'

export interface InviteCreateResult {
  invite_url: string
  expires_at: string
}

export interface InviteValidateResult {
  valid: boolean
  reason?: string
  expires_at?: string
}

export function createRegistrationInvite() {
  return request<InviteCreateResult>({
    url: 'registration-invites/',
    method: 'post',
    data: {},
  })
}

export function validateRegistrationInvite(token: string) {
  return request<InviteValidateResult>({
    url: 'register/validate/',
    method: 'get',
    params: { token },
  })
}

export function registerWithInvite(payload: {
  token: string
  username: string
  password: string
  confirm_password: string
}) {
  return request<{ access: string; refresh: string }>({
    url: 'register/',
    method: 'post',
    data: payload,
  })
}
