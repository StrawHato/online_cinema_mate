import { api } from './client'
import type { Cart, Order, Page } from '../types'

export const getCart = async () => (await api.get<Cart>('/cart/')).data
export const addToCart = (uuid: string) => api.post(`/cart/${uuid}/`)
export const removeFromCart = (uuid: string) => api.delete(`/cart/${uuid}/`)
export const createOrder = async () => (await api.post<Order>('/orders/')).data
export const createCheckout = async (uuid: string) => (await api.post<{ checkout_url: string }>(`/payments/${uuid}/checkout/`)).data
export const getOrders = async () => (await api.get<Page<Order>>('/orders/')).data
