import { useEffect, useState, type FormEvent } from 'react'
import { Link, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, Clapperboard, Film, Heart, Menu, Plus, Search, ShoppingBag, Sparkles, Star, Ticket, Trash2, UserRound, X } from 'lucide-react'
import * as moviesApi from './api/movies'
import * as shopApi from './api/shop'
import * as accountApi from './api/account'
import type { Movie } from './types'

const posters = [
  'photo-1485846234645-a62644f84728', 'photo-1440404653325-ab127d49abc1', 'photo-1517604931442-7e0c8ed2963c',
  'photo-1489599849927-2ee91cede3ba', 'photo-1505685296765-3a2736de412f', 'photo-1518676590629-3dcbd9c5a5c9',
  'photo-1478720568477-152d9b164e26', 'photo-1440404653325-ab127d49abc1', 'photo-1489599849927-2ee91cede3ba',
  'photo-1517604931442-7e0c8ed2963c', 'photo-1485846234645-a62644f84728', 'photo-1505685296765-3a2736de412f',
]
const posterUrl = (movie: Movie, index = 0) => `https://images.unsplash.com/${posters[(Number(movie.id || 0) + index) % posters.length]}?auto=format&fit=crop&w=900&q=85`
const money = (amount: number) => new Intl.NumberFormat('ru-RU', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(amount)
const shortError = (error: unknown) => {
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = e.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item)).join('. ')
  return e.message || 'Что-то пошло не так. Попробуйте ещё раз.'
}

function App() {
  const [signedIn, setSignedIn] = useState(Boolean(localStorage.getItem('access_token')))
  const [menuOpen, setMenuOpen] = useState(false)
  const [toast, setToast] = useState('')
  const queryClient = useQueryClient()
  useEffect(() => {
    const expire = () => { localStorage.removeItem('user_email'); setSignedIn(false); setToast('Сессия завершилась. Войдите снова.') }
    window.addEventListener('auth:expired', expire)
    return () => window.removeEventListener('auth:expired', expire)
  }, [])
  useEffect(() => { if (toast) { const id = window.setTimeout(() => setToast(''), 3200); return () => window.clearTimeout(id) } }, [toast])
  const signOut = () => {
    localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user_email'); setSignedIn(false)
    queryClient.clear(); setToast('Вы вышли из аккаунта')
  }
  return <>
    <header className="topbar"><div className="topbar-inner">
      <Link to="/" className="brand"><span className="brand-mark"><Clapperboard size={17} fill="currentColor" /></span><span>CINEMA<span className="brand-light">CLUB</span></span></Link>
      <nav className={menuOpen ? 'nav nav-open' : 'nav'}>
        <NavLink to="/" end onClick={() => setMenuOpen(false)}>Каталог</NavLink>
        {signedIn && <><NavLink to="/favorites" onClick={() => setMenuOpen(false)}>Избранное</NavLink><NavLink to="/orders" onClick={() => setMenuOpen(false)}>Заказы</NavLink></>}
      </nav>
      <div className="top-actions">
        <Link className="icon-button bag-button" to={signedIn ? '/cart' : '/login'} aria-label="Корзина"><ShoppingBag size={18} />{signedIn && <CartBadge />}</Link>
        {signedIn ? <><Link to="/profile" className="profile-link"><span className="avatar-small"><UserRound size={15} /></span><span>Профиль</span></Link><button className="text-button signout" onClick={signOut}>Выйти</button></> : <Link to="/login" className="login-link">Войти <ArrowUpRight size={15} /></Link>}
      </div>
      <button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Открыть меню">{menuOpen ? <X /> : <Menu />}</button>
    </div></header>
    <main className="main"><Routes>
      <Route path="/" element={<Catalog toast={setToast} />} />
      <Route path="/movie/:uuid" element={<MovieDetails signedIn={signedIn} toast={setToast} />} />
      <Route path="/login" element={<AuthPage mode="login" onSuccess={() => { setSignedIn(true); setToast('С возвращением!') }} />} />
      <Route path="/register" element={<AuthPage mode="register" onSuccess={() => { setSignedIn(true); setToast('Аккаунт создан') }} />} />
      <Route path="/activate" element={<ActivatePage />} />
      <Route path="/favorites" element={<Protected signedIn={signedIn}><Favorites toast={setToast} /></Protected>} />
      <Route path="/cart" element={<Protected signedIn={signedIn}><CartPage toast={setToast} /></Protected>} />
      <Route path="/profile" element={<Protected signedIn={signedIn}><ProfilePage toast={setToast} /></Protected>} />
      <Route path="/orders" element={<Protected signedIn={signedIn}><OrdersPage /></Protected>} />
      <Route path="*" element={<Catalog toast={setToast} />} />
    </Routes></main>
    <footer className="footer"><div className="footer-inner"><Link to="/" className="brand"><span className="brand-mark"><Clapperboard size={15} fill="currentColor" /></span><span>CINEMA<span className="brand-light">CLUB</span></span></Link><p>Кино, которое остаётся с тобой.</p><span className="footer-copy">© 2025 Cinema Club</span></div></footer>
    {toast && <div role="status" className="toast"><span className="toast-dot"><Check size={13} /></span>{toast}<button onClick={() => setToast('')} aria-label="Закрыть"><X size={15} /></button></div>}
  </>
}

function CartBadge() { const { data } = useQuery({ queryKey: ['cart-count'], queryFn: shopApi.getCart, staleTime: 20_000 }); return data?.total_movies ? <span className="badge-count">{data.total_movies}</span> : null }

function Protected({ signedIn, children }: { signedIn: boolean; children: React.ReactNode }) {
  const navigate = useNavigate()
  useEffect(() => { if (!signedIn) navigate('/login', { replace: true }) }, [signedIn, navigate])
  return signedIn ? children : null
}

function Catalog({ toast }: { toast: (s: string) => void }) {
  const [params, setParams] = useSearchParams()
  const search = params.get('search') || ''
  const genre = params.get('genre') || ''
  const page = Number(params.get('page') || 1)
  const sort = params.get('sort') || 'name'
  const [draft, setDraft] = useState(search)
  const { data: genreList = [] } = useQuery({ queryKey: ['genres'], queryFn: moviesApi.getGenres })
  const query = useQuery({ queryKey: ['movies', search, genre, page, sort], queryFn: () => moviesApi.getMovies({ search: search || undefined, genre: genre || undefined, page, sort }) })
  useEffect(() => setDraft(search), [search])
  const submitSearch = (e: FormEvent) => { e.preventDefault(); update({ search: draft.trim() || null, page: null }) }
  const update = (values: Record<string, string | null>) => setParams((old) => { const next = new URLSearchParams(old); for (const [key, value] of Object.entries(values)) value ? next.set(key, value) : next.delete(key); return next })
  return <>
    <section className="hero"><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-line" /> YOUR PRIVATE CINEMA</div><h1>Большие истории.<br /><span>Ваш вечер.</span></h1><p>Открывайте кино, которое хочется пересматривать. Коллекция историй для каждого настроения.</p><a className="button button-bright" href="#catalog">Смотреть каталог <ArrowDown size={16} /></a><div className="hero-proof"><div className="proof-avatars"><span>К</span><span>А</span><span>М</span><b>+</b></div><span><strong>Истории, которые выбирают</strong><br />снова и снова</span></div></div>
      <div className="hero-art"><div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" /><div className="hero-sun" /><div className="hero-poster hero-poster-back" /><div className="hero-poster hero-poster-front"><div className="poster-caption"><span>FEATURED COLLECTION</span><strong>THE ART OF<br />STORYTELLING</strong><small>VOL. 01 — EST. 2025</small></div></div><div className="floating-rating"><Star size={14} fill="currentColor" /><span>4.9</span><small>Editor's pick</small></div><div className="art-caption">FRAME NO. 024 <span>•</span> 35MM</div></div>
    </section>
    <section className="catalog-section" id="catalog"><div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> THE COLLECTION</div><h2>Найдите свой <em>фильм</em></h2></div><div className="catalog-total">{query.data ? `${query.data.total} фильмов в коллекции` : 'Кураторская подборка'}</div></div>
      <div className="filters-row"><form className="search-box" onSubmit={submitSearch}><Search size={17} /><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Название, режиссёр, актёр..." aria-label="Поиск фильмов" />{draft && <button type="button" onClick={() => { setDraft(''); update({ search: null, page: null }) }} aria-label="Очистить"><X size={15} /></button>}<kbd>↵</kbd></form><div className="filter-scroll"><button className={!genre ? 'filter-chip active' : 'filter-chip'} onClick={() => update({ genre: null, page: null })}>Все фильмы</button>{genreList.map((item) => <button key={item.id} className={genre === item.name ? 'filter-chip active' : 'filter-chip'} onClick={() => update({ genre: genre === item.name ? null : item.name, page: null })}>{item.name}</button>)}</div><label className="sort-select"><span>Сортировка</span><select value={sort} onChange={(e) => update({ sort: e.target.value, page: null })}><option value="name">По названию</option><option value="year">По году</option><option value="imdb">По рейтингу</option><option value="price">По цене</option></select><ChevronDown size={14} /></label></div>
      {query.isError ? <ErrorState message={shortError(query.error)} /> : query.isPending ? <MovieSkeleton /> : query.data.items.length ? <><div className="movie-grid">{query.data.items.map((movie, i) => <MovieCard key={movie.uuid} movie={movie} index={i} toast={toast} />)}</div><div className="pagination"><span>Показано <b>{query.data.items.length}</b> из <b>{query.data.total}</b></span><div className="page-buttons"><button disabled={page <= 1} onClick={() => update({ page: String(page - 1) })} aria-label="Предыдущая страница"><ArrowLeft size={16} /></button><span>{page} <i>/</i> {query.data.total_pages || 1}</span><button disabled={page >= query.data.total_pages} onClick={() => update({ page: String(page + 1) })} aria-label="Следующая страница"><ArrowRight size={16} /></button></div></div></> : <EmptyState title="Пока ничего не найдено" detail="Измените параметры поиска или выберите другой жанр." action={() => { setDraft(''); update({ search: null, genre: null, page: null }) }} />}
    </section>
  </>
}

function MovieCard({ movie, index, toast, isFavorite = false }: { movie: Movie; index: number; toast: (s: string) => void; isFavorite?: boolean }) {
  const queryClient = useQueryClient(); const signedIn = Boolean(localStorage.getItem('access_token'))
  const favorite = useMutation({ mutationFn: () => moviesApi.toggleFavorite(movie.uuid, isFavorite), onSuccess: () => { toast(isFavorite ? 'Удалено из избранного' : 'Добавлено в избранное'); queryClient.invalidateQueries({ queryKey: ['favorites'] }) }, onError: (e) => toast(shortError(e)) })
  const cart = useMutation({ mutationFn: () => shopApi.addToCart(movie.uuid), onSuccess: () => { toast('Фильм добавлен в корзину'); queryClient.invalidateQueries({ queryKey: ['cart'] }); queryClient.invalidateQueries({ queryKey: ['cart-count'] }) }, onError: (e) => toast(shortError(e)) })
  return <article className="movie-card" style={{ animationDelay: `${Math.min(index * 55, 450)}ms` }}><Link className="movie-poster" to={`/movie/${movie.uuid}`}><img src={posterUrl(movie, index)} alt="" loading="lazy" /><div className="poster-gradient" /><span className="poster-badge">{movie.certification?.name || 'FILM'}</span><span className="poster-year">{movie.year}</span><span className="poster-play"><Film size={17} /></span></Link><div className="movie-info"><div className="movie-title-row"><Link to={`/movie/${movie.uuid}`} className="movie-title">{movie.name}</Link><span className="movie-rating"><Star size={12} fill="currentColor" />{Number(movie.imdb).toFixed(1)}</span></div><div className="movie-meta"><span>{movie.genres.slice(0, 2).map((g) => g.name).join(' · ') || 'Авторское кино'}</span><span>{money(Number(movie.price))}</span></div><div className="card-actions"><Link to={`/movie/${movie.uuid}`} className="card-details">Подробнее <ArrowUpRight size={14} /></Link><div><button title={isFavorite ? 'Убрать из избранного' : signedIn ? 'В избранное' : 'Войдите, чтобы добавить в избранное'} className={isFavorite ? 'card-icon favorite-on' : 'card-icon'} onClick={() => signedIn ? favorite.mutate() : toast('Войдите, чтобы добавить в избранное')}><Heart size={16} fill={isFavorite ? 'currentColor' : 'none'} /></button><button className="card-icon" title="В корзину" onClick={() => signedIn ? cart.mutate() : toast('Войдите, чтобы добавить фильм в корзину')}><Plus size={17} /></button></div></div></div></article>
}

function MovieDetails({ signedIn, toast }: { signedIn: boolean; toast: (s: string) => void }) {
  const { uuid = '' } = useParams(); const navigate = useNavigate(); const qc = useQueryClient()
  const { data: movie, isPending, error } = useQuery({ queryKey: ['movie', uuid], queryFn: () => moviesApi.getMovie(uuid) })
  const { data: comments } = useQuery({ queryKey: ['comments', uuid], queryFn: () => moviesApi.getComments(uuid), enabled: !!movie && signedIn })
  const [comment, setComment] = useState(''); const [rating, setRating] = useState(0)
  const addCart = useMutation({ mutationFn: () => shopApi.addToCart(uuid), onSuccess: () => { toast('Фильм добавлен в корзину'); qc.invalidateQueries({ queryKey: ['cart'] }); qc.invalidateQueries({ queryKey: ['cart-count'] }) }, onError: (e) => toast(shortError(e)) })
  const favorite = useMutation({ mutationFn: () => moviesApi.toggleFavorite(uuid, false), onSuccess: () => { toast('Добавлено в избранное'); qc.invalidateQueries({ queryKey: ['favorites'] }) }, onError: (e) => toast(shortError(e)) })
  const rate = useMutation({ mutationFn: () => moviesApi.rateMovie(uuid, rating), onSuccess: () => { toast('Ваша оценка сохранена'); qc.invalidateQueries({ queryKey: ['movie', uuid] }) }, onError: (e) => toast(shortError(e)) })
  const post = useMutation({ mutationFn: () => moviesApi.postComment(uuid, comment), onSuccess: () => { setComment(''); toast('Комментарий опубликован'); qc.invalidateQueries({ queryKey: ['comments', uuid] }) }, onError: (e) => toast(shortError(e)) })
  if (isPending) return <MovieSkeleton />
  if (error || !movie) return <ErrorState message={shortError(error)} />
  return <section className="detail-page"><button className="back-link" onClick={() => navigate(-1)}><ArrowLeft size={15} /> Назад к каталогу</button><div className="detail-layout"><div className="detail-poster"><img src={posterUrl(movie, 3)} alt={movie.name} /><div className="poster-gradient" /><span className="detail-poster-mark">CC <i>—</i> 35MM</span></div><div className="detail-copy"><div className="eyebrow"><span className="eyebrow-line" /> CINEMA CLUB PRESENTS</div><h1>{movie.name}</h1><div className="detail-pills"><span>{movie.year}</span><span>{movie.time} мин</span><span>{movie.certification?.name}</span></div><div className="detail-rating"><span className="imdb-mark">IMDb</span><strong>{Number(movie.imdb).toFixed(1)}</strong><span className="rating-divider" /><Star size={15} fill="currentColor" /><strong>{Number(movie.average_rating).toFixed(1)}</strong><small>({movie.ratings_count} оценок)</small></div><p className="detail-description">{movie.description}</p><div className="detail-tags">{movie.genres.map((g) => <span key={g.id}>{g.name}</span>)}</div><div className="detail-price-row"><div><small>Цифровая коллекция</small><strong>{money(Number(movie.price))}</strong></div><button className="button button-bright" onClick={() => signedIn ? addCart.mutate() : navigate('/login')}><ShoppingBag size={16} /> В корзину <ArrowUpRight size={15} /></button><button className="button button-outline" onClick={() => signedIn ? favorite.mutate() : navigate('/login')} aria-label="В избранное"><Heart size={17} /></button></div><div className="detail-credits"><div><small>РЕЖИССЁР</small><span>{movie.directors.map((x) => x.name).join(', ') || '—'}</span></div><div><small>В ГЛАВНЫХ РОЛЯХ</small><span>{movie.stars.slice(0, 4).map((x) => x.name).join(', ') || '—'}</span></div></div></div></div>
    <div className="review-section"><div><div className="eyebrow"><span className="eyebrow-line" /> AFTER THE CREDITS</div><h2>Оставьте <em>впечатление</em></h2></div>{signedIn ? <div className="review-columns"><div className="rate-box"><span>Ваша оценка</span><div className="rating-input">{Array.from({ length: 10 }, (_, i) => <button key={i} aria-label={`Оценка ${i + 1}`} className={rating > i ? 'star-on' : ''} onClick={() => setRating(i + 1)}><Star size={20} fill="currentColor" /></button>)}</div><button disabled={!rating || rate.isPending} className="button button-outline rate-submit" onClick={() => rate.mutate()}>Оценить фильм <ArrowRight size={14} /></button></div><form className="comment-form" onSubmit={(e) => { e.preventDefault(); if (comment.trim()) post.mutate() }}><label htmlFor="comment">Поделитесь мнением</label><textarea id="comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="Что осталось с вами после титров?" rows={3} maxLength={5000} /><div><span>{comment.length} / 5000</span><button className="button button-bright" disabled={!comment.trim() || post.isPending}>Опубликовать <ArrowUpRight size={14} /></button></div></form></div> : <div className="login-prompt"><p>Войдите, чтобы оценить фильм и поделиться впечатлением.</p><Link to="/login" className="button button-outline">Войти в аккаунт <ArrowRight size={14} /></Link></div>}
    {comments?.items.length ? <div className="comments-list">{comments.items.map((c) => <article className="comment-card" key={c.uuid}><div className="comment-avatar">{c.author.username?.[0]?.toUpperCase() || 'К'}</div><div><div className="comment-heading"><strong>{c.author.username}</strong><span>{new Date(c.created_at).toLocaleDateString('ru-RU')}</span></div><p>{c.text}</p></div></article>)}</div> : signedIn && comments && <p className="muted-empty">Пока никто не оставил отзыв. Будьте первым.</p>}</div>
  </section>
}

function AuthPage({ mode, onSuccess }: { mode: 'login' | 'register'; onSuccess: () => void }) {
  const isLogin = mode === 'login'; const navigate = useNavigate(); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState('')
  const mutation = useMutation({ mutationFn: () => isLogin ? accountApi.login(email, password) : accountApi.register(email, password), onSuccess: (data) => { if (isLogin) { localStorage.setItem('access_token', data.access_token); localStorage.setItem('refresh_token', data.refresh_token); localStorage.setItem('user_email', email); onSuccess(); navigate('/') } else { setError('Аккаунт создан. Проверьте почту для активации, затем войдите.'); setTimeout(() => navigate('/login'), 3000) } }, onError: (e) => setError(shortError(e)) })
  return <section className="auth-page"><div className="auth-visual"><div className="auth-visual-noise" /><div className="auth-visual-inner"><span className="auth-kicker"><Sparkles size={14} /> YOUR SEAT IS WAITING</span><h2>Хорошее кино<br />начинается <em>здесь.</em></h2><p>Сохраняйте любимое, находите новое и собирайте свою коллекцию историй.</p><span className="auth-visual-index">01 / PERSONAL CINEMA</span></div></div><div className="auth-panel"><Link className="back-link" to="/"><ArrowLeft size={15} /> На главную</Link><div className="auth-form-wrap"><div className="eyebrow"><span className="eyebrow-line" /> {isLogin ? 'WELCOME BACK' : 'JOIN THE CLUB'}</div><h1>{isLogin ? 'С возвращением' : 'Создать аккаунт'}</h1><p>{isLogin ? 'Войдите, чтобы продолжить свою историю.' : 'Всего пара шагов до вашей личной киноколлекции.'}</p><form onSubmit={(e) => { e.preventDefault(); setError(''); mutation.mutate() }}><label htmlFor="email">Электронная почта</label><input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required /><label htmlFor="password">Пароль</label><input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Не менее 8 символов" autoComplete={isLogin ? 'current-password' : 'new-password'} minLength={8} required />{error && <div className={error.startsWith('Аккаунт') ? 'inline-success' : 'inline-error'}>{error}</div>}<button className="button button-bright auth-submit" disabled={mutation.isPending}>{mutation.isPending ? 'Подождите...' : isLogin ? 'Войти' : 'Создать аккаунт'} <ArrowRight size={16} /></button></form><div className="auth-switch">{isLogin ? 'Впервые в Cinema Club?' : 'Уже есть аккаунт?'} <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Создать аккаунт' : 'Войти'}</Link></div></div><div className="auth-footnote">Продолжая, вы соглашаетесь с условиями использования Cinema Club.</div></div></section>
}

function ActivatePage() {
  const [params] = useSearchParams(); const navigate = useNavigate()
  const [email, setEmail] = useState(params.get('email') || '')
  const [token, setToken] = useState(params.get('token') || '')
  const mutation = useMutation({ mutationFn: () => accountApi.activateAccount(email, token), onSuccess: () => setTimeout(() => navigate('/login'), 1800) })
  return <section className="activation-page"><div className="auth-form-wrap"><div className="eyebrow"><span className="eyebrow-line" /> ONE LAST STEP</div><h1>Подтвердите почту</h1><p>Перейдите по ссылке из письма или введите данные подтверждения ниже.</p><form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}><label htmlFor="activation-email">Электронная почта</label><input id="activation-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /><label htmlFor="activation-token">Код подтверждения</label><input id="activation-token" value={token} onChange={(e) => setToken(e.target.value)} required />{mutation.isError && <div className="inline-error">{shortError(mutation.error)}</div>}{mutation.isSuccess && <div className="inline-success">Почта подтверждена. Перенаправляем ко входу…</div>}<button className="button button-bright auth-submit" disabled={mutation.isPending || mutation.isSuccess}>{mutation.isPending ? 'Подтверждаем…' : 'Подтвердить аккаунт'} <ArrowRight size={16} /></button></form><div className="auth-switch"><Link to="/login">Вернуться ко входу</Link></div></div></section>
}

function Favorites({ toast }: { toast: (s: string) => void }) {
  const q = useQuery({ queryKey: ['favorites'], queryFn: moviesApi.getFavorites })
  return <section className="subpage"><PageIntro kicker="YOUR PERSONAL COLLECTION" title={<>Избранное <em>кино</em></>} description="Истории, которые вы решили оставить рядом." />{q.isError ? <ErrorState message={shortError(q.error)} /> : q.isPending ? <MovieSkeleton /> : q.data.items.length ? <div className="movie-grid">{q.data.items.map((m, i) => <MovieCard key={m.uuid} movie={m} index={i} toast={toast} isFavorite />)}</div> : <EmptyState title="Ваша коллекция пока пуста" detail="Добавляйте фильмы в избранное, чтобы вернуться к ним позже." action={() => window.location.assign('/')} />}</section>
}

function CartPage({ toast }: { toast: (s: string) => void }) {
  const qc = useQueryClient(); const navigate = useNavigate(); const q = useQuery({ queryKey: ['cart'], queryFn: shopApi.getCart })
  const remove = useMutation({ mutationFn: shopApi.removeFromCart, onSuccess: () => { qc.invalidateQueries({ queryKey: ['cart'] }); qc.invalidateQueries({ queryKey: ['cart-count'] }); toast('Фильм удалён из корзины') }, onError: (e) => toast(shortError(e)) })
  const checkout = useMutation({ mutationFn: async () => { const order = await shopApi.createOrder(); return shopApi.createCheckout(order.uuid) }, onSuccess: ({ checkout_url }) => { window.location.assign(checkout_url) }, onError: (e) => toast(shortError(e)) })
  if (q.isPending) return <section className="subpage"><MovieSkeleton /></section>
  if (q.isError) return <section className="subpage"><ErrorState message={shortError(q.error)} /></section>
  return <section className="subpage"><PageIntro kicker="YOUR NEXT FAVORITES" title={<>Корзина <em>покупок</em></>} description="Ваша личная коллекция начинается с одной хорошей истории." />{q.data.items.length ? <div className="cart-layout"><div className="cart-items">{q.data.items.map(({ movie }) => <article className="cart-item" key={movie.uuid}><Link to={`/movie/${movie.uuid}`} className="cart-thumb"><img src={posterUrl(movie as Movie, 2)} alt="" /></Link><div className="cart-item-copy"><Link to={`/movie/${movie.uuid}`}><strong>{movie.name}</strong></Link><span>{movie.year} · {movie.genres.map((g) => g.name).join(' / ')}</span></div><strong className="cart-price">{money(Number(movie.price))}</strong><button className="cart-remove" onClick={() => remove.mutate(movie.uuid)} aria-label="Удалить из корзины"><Trash2 size={16} /></button></article>)}</div><aside className="order-summary"><div className="eyebrow"><span className="eyebrow-line" /> ORDER SUMMARY</div><div className="summary-row"><span>Фильмов в корзине</span><span>{q.data.total_movies}</span></div><div className="summary-row"><span>Промежуточный итог</span><span>{money(Number(q.data.total_price))}</span></div><div className="summary-total"><span>Итого</span><strong>{money(Number(q.data.total_price))}</strong></div><button className="button button-bright checkout-button" disabled={checkout.isPending} onClick={() => checkout.mutate()}>{checkout.isPending ? 'Переходим к оплате...' : 'Перейти к оплате'} <ArrowRight size={16} /></button><p className="secure-note"><span>◇</span> Безопасная оплата через Stripe</p></aside></div> : <EmptyState title="Корзина ждёт свою первую историю" detail="Найдите фильм, который хочется забрать с собой." action={() => navigate('/')} />}</section>
}

function ProfilePage({ toast }: { toast: (s: string) => void }) {
  const qc = useQueryClient(); const profile = useQuery({ queryKey: ['profile'], queryFn: accountApi.getProfile })
  const [username, setUsername] = useState(''); const [first, setFirst] = useState(''); const [last, setLast] = useState(''); const [bio, setBio] = useState('')
  useEffect(() => { if (profile.data) { setUsername(profile.data.username || ''); setFirst(profile.data.first_name || ''); setLast(profile.data.last_name || ''); setBio(profile.data.info || '') } }, [profile.data])
  const update = useMutation({ mutationFn: () => { const d = new FormData(); d.append('username', username); d.append('first_name', first); d.append('last_name', last); if (bio) d.append('info', bio); return accountApi.updateProfile(d) }, onSuccess: () => { qc.invalidateQueries({ queryKey: ['profile'] }); toast('Профиль обновлён') }, onError: (e) => toast(shortError(e)) })
  if (profile.isPending) return <section className="subpage"><MovieSkeleton /></section>
  return <section className="subpage"><PageIntro kicker="YOUR MEMBERSHIP" title={<>Ваш <em>профиль</em></>} description="Пространство для вашей истории и любимых фильмов." />{profile.isError ? <ErrorState message={shortError(profile.error)} /> : <div className="profile-layout"><aside className="profile-card"><div className="profile-avatar">{(username || first || 'C')[0].toUpperCase()}</div><strong>{username || 'Киноман'}</strong><span>Участник Cinema Club</span><div className="profile-card-line" /><div className="profile-stat"><span>Статус</span><b><i className="online-dot" /> Активен</b></div><Link to="/favorites" className="profile-shortcut"><Heart size={15} /> Моё избранное <ArrowRight size={14} /></Link><Link to="/orders" className="profile-shortcut"><Ticket size={15} /> История заказов <ArrowRight size={14} /></Link></aside><form className="profile-form" onSubmit={(e) => { e.preventDefault(); update.mutate() }}><div className="form-section-title"><div><small>PERSONAL DETAILS</small><h3>Личная информация</h3></div><span className="muted">Обновлено в вашем профиле</span></div><div className="form-grid"><label>Имя пользователя<input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Ваше имя" /></label><label>Электронная почта<input value={localStorage.getItem('user_email') || ''} readOnly /></label><label>Имя<input value={first} onChange={(e) => setFirst(e.target.value)} placeholder="Имя" /></label><label>Фамилия<input value={last} onChange={(e) => setLast(e.target.value)} placeholder="Фамилия" /></label><label className="full-field">О себе<textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={4} placeholder="Расскажите о своих кино-предпочтениях..." /></label></div><div className="profile-save"><span>Ваши данные видны только вам.</span><button className="button button-bright" disabled={update.isPending}>{update.isPending ? 'Сохраняем...' : 'Сохранить изменения'} <ArrowRight size={15} /></button></div></form></div>}</section>
}

function OrdersPage() {
  const q = useQuery({ queryKey: ['orders'], queryFn: shopApi.getOrders })
  return <section className="subpage"><PageIntro kicker="YOUR CINEMA JOURNEY" title={<>История <em>заказов</em></>} description="Все истории, которые вы забрали с собой." />{q.isPending ? <MovieSkeleton /> : q.isError ? <ErrorState message={shortError(q.error)} /> : q.data.items.length ? <div className="orders-list">{q.data.items.map((o) => <article className="order-card" key={o.uuid}><div className="order-head"><div><small>ЗАКАЗ <span>#{o.uuid.slice(0, 8).toUpperCase()}</span></small><time>{new Date(o.created_at).toLocaleDateString('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })}</time></div><span className={`order-status status-${o.status.toLowerCase()}`}>{o.status}</span></div><div className="order-films">{o.items.map((item) => <Link key={item.id} to={`/movie/${item.movie.uuid}`} className="order-film"><span className="order-film-icon"><Film size={16} /></span><span><strong>{item.movie.name}</strong><small>{item.movie.year}</small></span><b>{money(Number(item.price_at_order))}</b></Link>)}</div><div className="order-total"><span>Итого</span><strong>{money(Number(o.total_amount))}</strong></div></article>)}</div> : <EmptyState title="История только начинается" detail="Ваши заказы появятся здесь после первой покупки." action={() => window.location.assign('/')} />}</section>
}

function PageIntro({ kicker, title, description }: { kicker: string; title: React.ReactNode; description: string }) { return <div className="page-intro"><div className="eyebrow"><span className="eyebrow-line" /> {kicker}</div><h1>{title}</h1><p>{description}</p></div> }
function EmptyState({ title, detail, action }: { title: string; detail: string; action: () => void }) { return <div className="empty-state"><div className="empty-icon"><Film size={22} /></div><h3>{title}</h3><p>{detail}</p><button className="button button-outline" onClick={action}>Открыть каталог <ArrowRight size={14} /></button></div> }
function ErrorState({ message }: { message: string }) { return <div className="error-state"><span>!</span><div><strong>Не удалось загрузить данные</strong><p>{message}</p></div></div> }
function MovieSkeleton() { return <div className="movie-grid">{Array.from({ length: 8 }, (_, i) => <div className="skeleton-card" key={i}><div className="skeleton-poster shimmer" /><div className="skeleton-line shimmer" /><div className="skeleton-line short shimmer" /></div>)}</div> }

export default App
