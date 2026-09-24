import { api } from './client'
import type { Movie, MoviePage, Page } from '../types'

export interface MovieFilters { search?: string; genre?: string; sort?: string; page?: number }
export const getMovies = async (filters: MovieFilters = {}) => (await api.get<MoviePage>('/movies/', { params: { page_size: 12, sort: 'name', ...filters } })).data
export const getMovie = async (uuid: string) => (await api.get<Movie>(`/movies/${uuid}/`)).data
export const getGenres = async () => (await api.get<{ id: number; name: string }[]>('/genres/')).data
export const getFavorites = async () => (await api.get<MoviePage>('/profile/favorites/', { params: { page_size: 20 } })).data
export const toggleFavorite = async (uuid: string, isFavorite: boolean) => api({ method: isFavorite ? 'delete' : 'post', url: `/profile/favorites/${uuid}/` })
export const rateMovie = async (uuid: string, rating: number) => api.post(`/movies/${uuid}/rating/`, { rating })
export const getComments = async (uuid: string) => (await api.get<Page<Comment>>(`/movies/${uuid}/comments/`)).data
export interface Comment { uuid: string; text: string; author: { username: string }; likes_count: number; replies_count: number; is_edited: boolean; is_liked: boolean; parent_comment_uuid: string | null; created_at: string; updated_at: string; replies: Comment[] }
export const postComment = async (uuid: string, text: string, parentCommentUuid?: string) => api.post(`/movies/${uuid}/comments/`, { text, ...(parentCommentUuid ? { parent_comment_uuid: parentCommentUuid } : {}) })
