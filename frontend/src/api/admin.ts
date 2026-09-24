import { api } from './client'
import type { Movie } from '../types'

export interface MovieInput {
  name: string
  year: number
  time: number
  imdb: number
  votes: number
  meta_score: number | null
  gross: number | null
  description: string
  price: number
  certification: string
  genres: string[]
  stars: string[]
  directors: string[]
}

export const createMovie = async (movie: MovieInput) => (await api.post<Movie>('/movies/', movie)).data
export const createGenre = async (name: string) => (await api.post('/genres/', { name })).data
export const createStar = async (name: string) => (await api.post('/stars/', { name })).data
