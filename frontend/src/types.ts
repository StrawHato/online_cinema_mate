export interface Genre { id: number; name: string }
export interface Person { id: number; name: string }
export interface Movie {
  id: number; uuid: string; name: string; year: number; time: number; imdb: number; votes: number;
  meta_score: number | null; gross: number | null; description: string; price: number;
  average_rating: number; ratings_count: number; certification: Genre; genres: Genre[];
  stars: Person[]; directors: Person[];
}
export interface MoviePage { total: number; page: number; page_size: number; total_pages: number; items: Movie[] }
export interface CartItem { id: number; added_at: string; movie: Pick<Movie, 'uuid' | 'name' | 'year' | 'price' | 'genres'> }
export interface Cart { total_movies: number; total_price: number; items: CartItem[] }
export interface Profile { id: number; user_id: number; username: string | null; first_name: string | null; last_name: string | null; gender: string | null; date_of_birth: string | null; info: string | null; avatar: string | null; group: 'user' | 'moderator' | 'admin' }
export interface Order { uuid: string; created_at: string; status: string; total_amount: number; items: { id: number; price_at_order: number; movie: { uuid: string; name: string; year: number } }[] }
export interface Page<T> { total: number; page: number; page_size: number; total_pages: number; items: T[] }
