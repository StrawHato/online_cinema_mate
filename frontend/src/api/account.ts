import { api } from './client'
import type { Profile } from '../types'

export const login = async (email: string, password: string) => (await api.post<{ access_token: string; refresh_token: string }>('/accounts/login/', { email, password })).data
export const register = async (email: string, password: string) => (await api.post('/accounts/register/', { email, password })).data
export const activateAccount = async (email: string, token: string) => (await api.post<{ message: string }>('/accounts/activate/', { email, token })).data
export const getProfile = async () => (await api.get<Profile>('/profile/')).data
export const updateProfile = async (data: FormData) => (await api.patch<Profile>('/profile/', data)).data
