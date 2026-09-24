import { useEffect, useState, type FormEvent } from 'react'
import { Link, NavLink, Route, Routes, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowDown, ArrowLeft, ArrowRight, ArrowUpRight, Check, ChevronDown, Clapperboard, Film, Heart, Menu, Plus, Search, ShoppingBag, Sparkles, Star, Ticket, Trash2, UserRound, X } from 'lucide-react'
import * as moviesApi from './api/movies'
import * as shopApi from './api/shop'
import * as accountApi from './api/account'
import AdminPage from './pages/AdminPage'
import AvatarPicker from './pages/AvatarPicker'
import type { Movie } from './types'

const posters = [
  'photo-1485846234645-a62644f84728', 'photo-1440404653325-ab127d49abc1', 'photo-1517604931442-7e0c8ed2963c',
  'photo-1489599849927-2ee91cede3ba', 'photo-1505685296765-3a2736de412f', 'photo-1518676590629-3dcbd9c5a5c9',
  'photo-1478720568477-152d9b164e26', 'photo-1440404653325-ab127d49abc1', 'photo-1489599849927-2ee91cede3ba',
  'photo-1517604931442-7e0c8ed2963c', 'photo-1485846234645-a62644f84728', 'photo-1505685296765-3a2736de412f',
]
const posterUrl = (movie: Movie, index = 0) => `https://images.unsplash.com/${posters[(Number(movie.id || 0) + index) % posters.length]}?auto=format&fit=crop&w=900&q=85`
const money = (amount: number) => new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 2 }).format(amount)
const shortError = (error: unknown) => {
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = e.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => typeof item === 'object' && item && 'msg' in item ? String(item.msg) : String(item)).join('. ')
  return e.message || 'Something went wrong. Please try again.'
}

function App() {
  const [signedIn, setSignedIn] = useState(Boolean(localStorage.getItem('access_token')))
  const [menuOpen, setMenuOpen] = useState(false)
  const [toast, setToast] = useState('')
  const queryClient = useQueryClient()
  const currentProfile = useQuery({ queryKey: ['profile'], queryFn: accountApi.getProfile, enabled: signedIn })
  useEffect(() => {
    const expire = () => { localStorage.removeItem('user_email'); setSignedIn(false); setToast('Your session has expired. Please sign in again.') }
    window.addEventListener('auth:expired', expire)
    return () => window.removeEventListener('auth:expired', expire)
  }, [])
  useEffect(() => { if (toast) { const id = window.setTimeout(() => setToast(''), 3200); return () => window.clearTimeout(id) } }, [toast])
  const signOut = () => {
    localStorage.removeItem('access_token'); localStorage.removeItem('refresh_token'); localStorage.removeItem('user_email'); setSignedIn(false)
    queryClient.clear(); setToast('You have signed out.')
  }
  return <>
    <header className="topbar"><div className="topbar-inner">
      <Link to="/" className="brand"><span className="brand-mark"><Clapperboard size={17} fill="currentColor" /></span><span>CINEMA<span className="brand-light">CLUB</span></span></Link>
      <nav className={menuOpen ? 'nav nav-open' : 'nav'}>
        <NavLink to="/" end onClick={() => setMenuOpen(false)}>Catalog</NavLink>
        {signedIn && <><NavLink to="/favorites" onClick={() => setMenuOpen(false)}>Favorites</NavLink><NavLink to="/orders" onClick={() => setMenuOpen(false)}>Orders</NavLink>{currentProfile.data?.group === 'admin' && <NavLink to="/admin" onClick={() => setMenuOpen(false)}>Admin</NavLink>}</>}
      </nav>
      <div className="top-actions">
        <Link className="icon-button bag-button" to={signedIn ? '/cart' : '/login'} aria-label="Cart"><ShoppingBag size={18} />{signedIn && <CartBadge />}</Link>
        {signedIn ? <><Link to="/profile" className="profile-link"><span className="avatar-small"><UserRound size={15} /></span><span>Profile</span></Link><button className="text-button signout" onClick={signOut}>Sign out</button></> : <Link to="/login" className="login-link">Sign in <ArrowUpRight size={15} /></Link>}
      </div>
      <button className="mobile-menu" onClick={() => setMenuOpen(!menuOpen)} aria-label="Open menu">{menuOpen ? <X /> : <Menu />}</button>
    </div></header>
    <main className="main"><Routes>
      <Route path="/" element={<Catalog toast={setToast} />} />
      <Route path="/movie/:uuid" element={<MovieDetails signedIn={signedIn} toast={setToast} />} />
      <Route path="/login" element={<AuthPage mode="login" onSuccess={() => { setSignedIn(true); setToast('Welcome back!') }} />} />
      <Route path="/register" element={<AuthPage mode="register" onSuccess={() => { setSignedIn(true); setToast('Account created.') }} />} />
      <Route path="/activate" element={<ActivatePage />} />
      <Route path="/favorites" element={<Protected signedIn={signedIn}><Favorites toast={setToast} /></Protected>} />
      <Route path="/cart" element={<Protected signedIn={signedIn}><CartPage toast={setToast} /></Protected>} />
      <Route path="/profile" element={<Protected signedIn={signedIn}><ProfilePage toast={setToast} /></Protected>} />
      <Route path="/orders" element={<Protected signedIn={signedIn}><OrdersPage /></Protected>} />
      <Route path="/admin" element={<Protected signedIn={signedIn}><AdminPage toast={setToast} /></Protected>} />
      <Route path="*" element={<Catalog toast={setToast} />} />
    </Routes></main>
    <footer className="footer"><div className="footer-inner"><Link to="/" className="brand"><span className="brand-mark"><Clapperboard size={15} fill="currentColor" /></span><span>CINEMA<span className="brand-light">CLUB</span></span></Link><p>Stories that stay with you.</p><span className="footer-copy">© 2025 Cinema Club</span></div></footer>
    {toast && <div role="status" className="toast"><span className="toast-dot"><Check size={13} /></span>{toast}<button onClick={() => setToast('')} aria-label="Close"><X size={15} /></button></div>}
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
    <section className="hero"><div className="hero-copy"><div className="eyebrow"><span className="eyebrow-line" /> YOUR PRIVATE CINEMA</div><h1>Big stories.<br /><span>Your evening.</span></h1><p>Discover films worth watching again: a collection of stories for every mood.</p><a className="button button-bright" href="#catalog">Browse films <ArrowDown size={16} /></a><div className="hero-proof"><div className="proof-avatars"><span>C</span><span>A</span><span>M</span><b>+</b></div><span><strong>Stories chosen</strong><br />again and again</span></div></div>
      <div className="hero-art"><div className="hero-orbit orbit-one" /><div className="hero-orbit orbit-two" /><div className="hero-sun" /><div className="hero-poster hero-poster-back" /><div className="hero-poster hero-poster-front"><div className="poster-caption"><span>FEATURED COLLECTION</span><strong>THE ART OF<br />STORYTELLING</strong><small>VOL. 01 — EST. 2025</small></div></div><div className="floating-rating"><Star size={14} fill="currentColor" /><span>4.9</span><small>Editor's pick</small></div><div className="art-caption">FRAME NO. 024 <span>•</span> 35MM</div></div>
    </section>
    <section className="catalog-section" id="catalog"><div className="section-heading"><div><div className="eyebrow"><span className="eyebrow-line" /> THE COLLECTION</div><h2>Find your next <em>film</em></h2></div><div className="catalog-total">{query.data ? `${query.data.total} films in the collection` : 'Curated selection'}</div></div>
      <div className="filters-row"><form className="search-box" onSubmit={submitSearch}><Search size={17} /><input value={draft} onChange={(e) => setDraft(e.target.value)} placeholder="Title, director, or cast…" aria-label="Search films" />{draft && <button type="button" onClick={() => { setDraft(''); update({ search: null, page: null }) }} aria-label="Clear search"><X size={15} /></button>}<kbd>↵</kbd></form><div className="filter-scroll"><button className={!genre ? 'filter-chip active' : 'filter-chip'} onClick={() => update({ genre: null, page: null })}>All films</button>{genreList.map((item) => <button key={item.id} className={genre === item.name ? 'filter-chip active' : 'filter-chip'} onClick={() => update({ genre: genre === item.name ? null : item.name, page: null })}>{item.name}</button>)}</div><label className="sort-select"><span>Sort by</span><select value={sort} onChange={(e) => update({ sort: e.target.value, page: null })}><option value="name">Title</option><option value="year">Year</option><option value="imdb">Rating</option><option value="price">Price</option></select><ChevronDown size={14} /></label></div>
      {query.isError ? <ErrorState message={shortError(query.error)} /> : query.isPending ? <MovieSkeleton /> : query.data.items.length ? <><div className="movie-grid">{query.data.items.map((movie, i) => <MovieCard key={movie.uuid} movie={movie} index={i} toast={toast} />)}</div><div className="pagination"><span>Showing <b>{query.data.items.length}</b> of <b>{query.data.total}</b></span><div className="page-buttons"><button disabled={page <= 1} onClick={() => update({ page: String(page - 1) })} aria-label="Previous page"><ArrowLeft size={16} /></button><span>{page} <i>/</i> {query.data.total_pages || 1}</span><button disabled={page >= query.data.total_pages} onClick={() => update({ page: String(page + 1) })} aria-label="Next page"><ArrowRight size={16} /></button></div></div></> : <EmptyState title="No films found" detail="Adjust your search or choose a different genre." action={() => { setDraft(''); update({ search: null, genre: null, page: null }) }} />}
    </section>
  </>
}

function MovieCard({ movie, index, toast, isFavorite = false }: { movie: Movie; index: number; toast: (s: string) => void; isFavorite?: boolean }) {
  const queryClient = useQueryClient(); const signedIn = Boolean(localStorage.getItem('access_token'))
  const favorite = useMutation({ mutationFn: () => moviesApi.toggleFavorite(movie.uuid, isFavorite), onSuccess: () => { toast(isFavorite ? 'Removed from favorites.' : 'Added to favorites.'); queryClient.invalidateQueries({ queryKey: ['favorites'] }) }, onError: (e) => toast(shortError(e)) })
  const cart = useMutation({ mutationFn: () => shopApi.addToCart(movie.uuid), onSuccess: () => { toast('Film added to your cart.'); queryClient.invalidateQueries({ queryKey: ['cart'] }); queryClient.invalidateQueries({ queryKey: ['cart-count'] }) }, onError: (e) => toast(shortError(e)) })
  return <article className="movie-card" style={{ animationDelay: `${Math.min(index * 55, 450)}ms` }}><Link className="movie-poster" to={`/movie/${movie.uuid}`}><img src={posterUrl(movie, index)} alt="" loading="lazy" /><div className="poster-gradient" /><span className="poster-badge">{movie.certification?.name || 'FILM'}</span><span className="poster-year">{movie.year}</span><span className="poster-play"><Film size={17} /></span></Link><div className="movie-info"><div className="movie-title-row"><Link to={`/movie/${movie.uuid}`} className="movie-title">{movie.name}</Link><span className="movie-rating"><Star size={12} fill="currentColor" />{Number(movie.imdb).toFixed(1)}</span></div><div className="movie-meta"><span>{movie.genres.slice(0, 2).map((g) => g.name).join(' · ') || 'Independent film'}</span><span>{money(Number(movie.price))}</span></div><div className="card-actions"><Link to={`/movie/${movie.uuid}`} className="card-details">Details <ArrowUpRight size={14} /></Link><div><button title={isFavorite ? 'Remove from favorites' : signedIn ? 'Add to favorites' : 'Sign in to save films to your favorites.'} className={isFavorite ? 'card-icon favorite-on' : 'card-icon'} onClick={() => signedIn ? favorite.mutate() : toast('Sign in to save films to your favorites.')}><Heart size={16} fill={isFavorite ? 'currentColor' : 'none'} /></button><button className="card-icon" title="Add to cart" onClick={() => signedIn ? cart.mutate() : toast('Sign in to add a film to your cart.')}><Plus size={17} /></button></div></div></div></article>
}

function MovieDetails({ signedIn, toast }: { signedIn: boolean; toast: (s: string) => void }) {
  const { uuid = '' } = useParams(); const navigate = useNavigate(); const qc = useQueryClient()
  const { data: movie, isPending, error } = useQuery({ queryKey: ['movie', uuid], queryFn: () => moviesApi.getMovie(uuid) })
  const { data: comments } = useQuery({ queryKey: ['comments', uuid], queryFn: () => moviesApi.getComments(uuid), enabled: !!movie && signedIn })
  const [comment, setComment] = useState(''); const [rating, setRating] = useState(0)
  const addCart = useMutation({ mutationFn: () => shopApi.addToCart(uuid), onSuccess: () => { toast('Film added to your cart.'); qc.invalidateQueries({ queryKey: ['cart'] }); qc.invalidateQueries({ queryKey: ['cart-count'] }) }, onError: (e) => toast(shortError(e)) })
  const favorite = useMutation({ mutationFn: () => moviesApi.toggleFavorite(uuid, false), onSuccess: () => { toast('Added to favorites.'); qc.invalidateQueries({ queryKey: ['favorites'] }) }, onError: (e) => toast(shortError(e)) })
  const rate = useMutation({ mutationFn: () => moviesApi.rateMovie(uuid, rating), onSuccess: () => { toast('Your rating has been saved.'); qc.invalidateQueries({ queryKey: ['movie', uuid] }) }, onError: (e) => toast(shortError(e)) })
  const post = useMutation({ mutationFn: () => moviesApi.postComment(uuid, comment), onSuccess: () => { setComment(''); toast('Comment posted.'); qc.invalidateQueries({ queryKey: ['comments', uuid] }) }, onError: (e) => toast(shortError(e)) })
  if (isPending) return <MovieSkeleton />
  if (error || !movie) return <ErrorState message={shortError(error)} />
  return <section className="detail-page"><button className="back-link" onClick={() => navigate(-1)}><ArrowLeft size={15} /> Back to catalog</button><div className="detail-layout"><div className="detail-poster"><img src={posterUrl(movie, 3)} alt={movie.name} /><div className="poster-gradient" /><span className="detail-poster-mark">CC <i>—</i> 35MM</span></div><div className="detail-copy"><div className="eyebrow"><span className="eyebrow-line" /> CINEMA CLUB PRESENTS</div><h1>{movie.name}</h1><div className="detail-pills"><span>{movie.year}</span><span>{movie.time} min</span><span>{movie.certification?.name}</span></div><div className="detail-rating"><span className="imdb-mark">IMDb</span><strong>{Number(movie.imdb).toFixed(1)}</strong><span className="rating-divider" /><Star size={15} fill="currentColor" /><strong>{Number(movie.average_rating).toFixed(1)}</strong><small>({movie.ratings_count} ratings)</small></div><p className="detail-description">{movie.description}</p><div className="detail-tags">{movie.genres.map((g) => <span key={g.id}>{g.name}</span>)}</div><div className="detail-price-row"><div><small>Digital collection</small><strong>{money(Number(movie.price))}</strong></div><button className="button button-bright" onClick={() => signedIn ? addCart.mutate() : navigate('/login')}><ShoppingBag size={16} /> Add to cart <ArrowUpRight size={15} /></button><button className="button button-outline" onClick={() => signedIn ? favorite.mutate() : navigate('/login')} aria-label="Add to favorites"><Heart size={17} /></button></div><div className="detail-credits"><div><small>DIRECTOR</small><span>{movie.directors.map((x) => x.name).join(', ') || '—'}</span></div><div><small>STARRING</small><span>{movie.stars.slice(0, 4).map((x) => x.name).join(', ') || '—'}</span></div></div></div></div>
    <div className="review-section"><div><div className="eyebrow"><span className="eyebrow-line" /> AFTER THE CREDITS</div><h2>Leave an <em>impression</em></h2></div>{signedIn ? <div className="review-columns"><div className="rate-box"><span>Your rating</span><div className="rating-input">{Array.from({ length: 10 }, (_, i) => <button key={i} aria-label={`Rating ${i + 1}`} className={rating > i ? 'star-on' : ''} onClick={() => setRating(i + 1)}><Star size={20} fill="currentColor" /></button>)}</div><button disabled={!rating || rate.isPending} className="button button-outline rate-submit" onClick={() => rate.mutate()}>Submit rating <ArrowRight size={14} /></button></div><form className="comment-form" onSubmit={(e) => { e.preventDefault(); if (comment.trim()) post.mutate() }}><label htmlFor="comment">Share your thoughts</label><textarea id="comment" value={comment} onChange={(e) => setComment(e.target.value)} placeholder="What stayed with you after the credits?" rows={3} maxLength={5000} /><div><span>{comment.length} / 5000</span><button className="button button-bright" disabled={!comment.trim() || post.isPending}>Post comment <ArrowUpRight size={14} /></button></div></form></div> : <div className="login-prompt"><p>Sign in to rate this film and share your thoughts.</p><Link to="/login" className="button button-outline">Sign in to your account <ArrowRight size={14} /></Link></div>}
    {comments?.items.length ? <div className="comments-list">{comments.items.map((c) => <article className="comment-card" key={c.uuid}><div className="comment-avatar">{c.author.username?.[0]?.toUpperCase() || 'C'}</div><div><div className="comment-heading"><strong>{c.author.username}</strong><span>{new Date(c.created_at).toLocaleDateString('en-US')}</span></div><p>{c.text}</p></div></article>)}</div> : signedIn && comments && <p className="muted-empty">No reviews yet. Be the first to share one.</p>}</div>
  </section>
}

function AuthPage({ mode, onSuccess }: { mode: 'login' | 'register'; onSuccess: () => void }) {
  const isLogin = mode === 'login'; const navigate = useNavigate(); const [email, setEmail] = useState(''); const [password, setPassword] = useState(''); const [error, setError] = useState('')
  const mutation = useMutation({ mutationFn: () => isLogin ? accountApi.login(email, password) : accountApi.register(email, password), onSuccess: (data) => { if (isLogin) { localStorage.setItem('access_token', data.access_token); localStorage.setItem('refresh_token', data.refresh_token); localStorage.setItem('user_email', email); onSuccess(); navigate('/') } else { setError('Account created. Check your email to activate it, then sign in.'); setTimeout(() => navigate('/login'), 3000) } }, onError: (e) => setError(shortError(e)) })
  return <section className="auth-page"><div className="auth-visual"><div className="auth-visual-noise" /><div className="auth-visual-inner"><span className="auth-kicker"><Sparkles size={14} /> YOUR SEAT IS WAITING</span><h2>Great films<br />start <em>here.</em></h2><p>Save your favorites, discover something new, and build a collection of stories.</p><span className="auth-visual-index">01 / PERSONAL CINEMA</span></div></div><div className="auth-panel"><Link className="back-link" to="/"><ArrowLeft size={15} /> Home</Link><div className="auth-form-wrap"><div className="eyebrow"><span className="eyebrow-line" /> {isLogin ? 'WELCOME BACK' : 'JOIN THE CLUB'}</div><h1>{isLogin ? 'Welcome back' : 'Create an account'}</h1><p>{isLogin ? 'Sign in to continue your story.' : 'Just a couple of steps to your personal film collection.'}</p><form onSubmit={(e) => { e.preventDefault(); setError(''); mutation.mutate() }}><label htmlFor="email">Email address</label><input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required /><label htmlFor="password">Password</label><input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" autoComplete={isLogin ? 'current-password' : 'new-password'} minLength={8} required />{error && <div className={error.startsWith('Account created') ? 'inline-success' : 'inline-error'}>{error}</div>}<button className="button button-bright auth-submit" disabled={mutation.isPending}>{mutation.isPending ? 'Please wait…' : isLogin ? 'Sign in' : 'Create an account'} <ArrowRight size={16} /></button></form><div className="auth-switch">{isLogin ? 'New to Cinema Club?' : 'Already have an account?'} <Link to={isLogin ? '/register' : '/login'}>{isLogin ? 'Create an account' : 'Sign in'}</Link></div></div><div className="auth-footnote">By continuing, you accept the Cinema Club terms of use.</div></div></section>
}

function ActivatePage() {
  const [params] = useSearchParams(); const navigate = useNavigate()
  const [email, setEmail] = useState(params.get('email') || '')
  const [token, setToken] = useState(params.get('token') || '')
  const mutation = useMutation({ mutationFn: () => accountApi.activateAccount(email, token), onSuccess: () => setTimeout(() => navigate('/login'), 1800) })
  return <section className="activation-page"><div className="auth-form-wrap"><div className="eyebrow"><span className="eyebrow-line" /> ONE LAST STEP</div><h1>Verify your email</h1><p>Follow the link in your email, or enter your confirmation details below.</p><form onSubmit={(e) => { e.preventDefault(); mutation.mutate() }}><label htmlFor="activation-email">Email address</label><input id="activation-email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required /><label htmlFor="activation-token">Confirmation token</label><input id="activation-token" value={token} onChange={(e) => setToken(e.target.value)} required />{mutation.isError && <div className="inline-error">{shortError(mutation.error)}</div>}{mutation.isSuccess && <div className="inline-success">Email confirmed. Redirecting to sign in…</div>}<button className="button button-bright auth-submit" disabled={mutation.isPending || mutation.isSuccess}>{mutation.isPending ? 'Confirming…' : 'Confirm account'} <ArrowRight size={16} /></button></form><div className="auth-switch"><Link to="/login">Back to sign in</Link></div></div></section>
}

function Favorites({ toast }: { toast: (s: string) => void }) {
  const q = useQuery({ queryKey: ['favorites'], queryFn: moviesApi.getFavorites })
  return <section className="subpage"><PageIntro kicker="YOUR PERSONAL COLLECTION" title={<>Favorite <em>films</em></>} description="Stories you want to keep close." />{q.isError ? <ErrorState message={shortError(q.error)} /> : q.isPending ? <MovieSkeleton /> : q.data.items.length ? <div className="movie-grid">{q.data.items.map((m, i) => <MovieCard key={m.uuid} movie={m} index={i} toast={toast} isFavorite />)}</div> : <EmptyState title="Your collection is empty for now" detail="Save films to your favorites and come back to them later." action={() => window.location.assign('/')} />}</section>
}

function CartPage({ toast }: { toast: (s: string) => void }) {
  const qc = useQueryClient(); const navigate = useNavigate(); const q = useQuery({ queryKey: ['cart'], queryFn: shopApi.getCart })
  const remove = useMutation({ mutationFn: shopApi.removeFromCart, onSuccess: () => { qc.invalidateQueries({ queryKey: ['cart'] }); qc.invalidateQueries({ queryKey: ['cart-count'] }); toast('Film removed from your cart.') }, onError: (e) => toast(shortError(e)) })
  const checkout = useMutation({ mutationFn: async () => { const order = await shopApi.createOrder(); return shopApi.createCheckout(order.uuid) }, onSuccess: ({ checkout_url }) => { window.location.assign(checkout_url) }, onError: (e) => toast(shortError(e)) })
  if (q.isPending) return <section className="subpage"><MovieSkeleton /></section>
  if (q.isError) return <section className="subpage"><ErrorState message={shortError(q.error)} /></section>
  return <section className="subpage"><PageIntro kicker="YOUR NEXT FAVORITES" title={<>Your <em>cart</em></>} description="Your personal collection begins with one great story." />{q.data.items.length ? <div className="cart-layout"><div className="cart-items">{q.data.items.map(({ movie }) => <article className="cart-item" key={movie.uuid}><Link to={`/movie/${movie.uuid}`} className="cart-thumb"><img src={posterUrl(movie as Movie, 2)} alt="" /></Link><div className="cart-item-copy"><Link to={`/movie/${movie.uuid}`}><strong>{movie.name}</strong></Link><span>{movie.year} · {movie.genres.map((g) => g.name).join(' / ')}</span></div><strong className="cart-price">{money(Number(movie.price))}</strong><button className="cart-remove" onClick={() => remove.mutate(movie.uuid)} aria-label="Remove from cart"><Trash2 size={16} /></button></article>)}</div><aside className="order-summary"><div className="eyebrow"><span className="eyebrow-line" /> ORDER SUMMARY</div><div className="summary-row"><span>Films in cart</span><span>{q.data.total_movies}</span></div><div className="summary-row"><span>Subtotal</span><span>{money(Number(q.data.total_price))}</span></div><div className="summary-total"><span>Total</span><strong>{money(Number(q.data.total_price))}</strong></div><button className="button button-bright checkout-button" disabled={checkout.isPending} onClick={() => checkout.mutate()}>{checkout.isPending ? 'Redirecting to checkout…' : 'Proceed to checkout'} <ArrowRight size={16} /></button><p className="secure-note"><span>◇</span> Secure payment powered by Stripe</p></aside></div> : <EmptyState title="Your cart is waiting for its first story" detail="Find a film you would like to add to your collection." action={() => navigate('/')} />}</section>
}

function ProfilePage({ toast }: { toast: (s: string) => void }) {
  const qc = useQueryClient(); const profile = useQuery({ queryKey: ['profile'], queryFn: accountApi.getProfile })
  const [username, setUsername] = useState(''); const [first, setFirst] = useState(''); const [last, setLast] = useState(''); const [bio, setBio] = useState('')
  useEffect(() => { if (profile.data) { setUsername(profile.data.username || ''); setFirst(profile.data.first_name || ''); setLast(profile.data.last_name || ''); setBio(profile.data.info || '') } }, [profile.data])
  const update = useMutation({ mutationFn: () => { const d = new FormData(); d.append('username', username); d.append('first_name', first); d.append('last_name', last); if (bio) d.append('info', bio); return accountApi.updateProfile(d) }, onSuccess: () => { qc.invalidateQueries({ queryKey: ['profile'] }); toast('Profile updated.') }, onError: (e) => toast(shortError(e)) })
  if (profile.isPending) return <section className="subpage"><MovieSkeleton /></section>
  return <section className="subpage"><PageIntro kicker="YOUR MEMBERSHIP" title={<>Your <em>profile</em></>} description="A space for your account and favorite films." />{profile.isError ? <ErrorState message={shortError(profile.error)} /> : <div className="profile-layout"><aside className="profile-card"><AvatarPicker profile={profile.data!} toast={toast} /><strong>{username || 'Film fan'}</strong><span>Cinema Club member</span><div className="profile-card-line" /><div className="profile-stat"><span>Status</span><b><i className="online-dot" /> Active</b></div><Link to="/favorites" className="profile-shortcut"><Heart size={15} /> My favorites <ArrowRight size={14} /></Link><Link to="/orders" className="profile-shortcut"><Ticket size={15} /> Order history <ArrowRight size={14} /></Link></aside><form className="profile-form" onSubmit={(e) => { e.preventDefault(); update.mutate() }}><div className="form-section-title"><div><small>PERSONAL DETAILS</small><h3>Personal information</h3></div><span className="muted">Profile details</span></div><div className="form-grid"><label>Username<input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="Your username" /></label><label>Email address<input value={localStorage.getItem('user_email') || ''} readOnly /></label><label>First name<input value={first} onChange={(e) => setFirst(e.target.value)} placeholder="First name" /></label><label>Last name<input value={last} onChange={(e) => setLast(e.target.value)} placeholder="Last name" /></label><label className="full-field">About me<textarea value={bio} onChange={(e) => setBio(e.target.value)} rows={4} placeholder="Tell us about your film preferences…" /></label></div><div className="profile-save"><span>Your profile details are only visible to you.</span><button className="button button-bright" disabled={update.isPending}>{update.isPending ? 'Saving…' : 'Save changes'} <ArrowRight size={15} /></button></div></form></div>}</section>
}

function OrdersPage() {
  const [params] = useSearchParams()
  const paymentUuid = params.get('payment_uuid')
  const paymentResult = params.get('payment')
  const qc = useQueryClient()
  const payment = useQuery({
    queryKey: ['payment', paymentUuid],
    queryFn: () => shopApi.getPayment(paymentUuid!),
    enabled: paymentResult === 'success' && !!paymentUuid,
    refetchInterval: (query) => ['successful', 'canceled', 'refunded'].includes(query.state.data?.status || '') || query.state.dataUpdateCount >= 30 || query.state.fetchFailureCount >= 10 ? false : 2000,
  })
  const q = useQuery({ queryKey: ['orders'], queryFn: shopApi.getOrders })
  useEffect(() => {
    if (payment.data?.status === 'successful') qc.invalidateQueries({ queryKey: ['orders'] })
  }, [payment.data?.status, qc])
  const paymentNotice = paymentResult === 'cancelled'
    ? <div className="inline-error" role="status">Payment was cancelled. Your order remains unpaid.</div>
    : paymentResult === 'success' && payment.data?.status === 'successful'
      ? <div className="inline-success" role="status">Payment confirmed. Your order is now paid.</div>
      : paymentResult === 'success' && payment.data?.status === 'canceled'
        ? <div className="inline-error" role="status">This payment was cancelled. You can retry checkout from your cart.</div>
      : paymentResult === 'success'
        ? <div className="inline-success" role="status">Payment submitted. Waiting for Stripe to confirm it…</div>
        : null
  return <section className="subpage"><PageIntro kicker="YOUR CINEMA JOURNEY" title={<>Order <em>history</em></>} description="Every story you have brought home." />{paymentNotice}{payment.isError && <ErrorState message="We could not check the payment status. Refresh this page in a moment." />}{q.isPending ? <MovieSkeleton /> : q.isError ? <ErrorState message={shortError(q.error)} /> : q.data.items.length ? <div className="orders-list">{q.data.items.map((o) => <article className="order-card" key={o.uuid}><div className="order-head"><div><small>ORDER <span>#{o.uuid.slice(0, 8).toUpperCase()}</span></small><time>{new Date(o.created_at).toLocaleDateString('en-US', { day: 'numeric', month: 'long', year: 'numeric' })}</time></div><span className={`order-status status-${o.status.toLowerCase()}`}>{o.status}</span></div><div className="order-films">{o.items.map((item) => <Link key={item.id} to={`/movie/${item.movie.uuid}`} className="order-film"><span className="order-film-icon"><Film size={16} /></span><span><strong>{item.movie.name}</strong><small>{item.movie.year}</small></span><b>{money(Number(item.price_at_order))}</b></Link>)}</div><div className="order-total"><span>Total</span><strong>{money(Number(o.total_amount))}</strong></div></article>)}</div> : <EmptyState title="Your order history is empty" detail="Your orders will appear here after your first purchase." action={() => window.location.assign('/')} />}</section>
}

function PageIntro({ kicker, title, description }: { kicker: string; title: React.ReactNode; description: string }) { return <div className="page-intro"><div className="eyebrow"><span className="eyebrow-line" /> {kicker}</div><h1>{title}</h1><p>{description}</p></div> }
function EmptyState({ title, detail, action }: { title: string; detail: string; action: () => void }) { return <div className="empty-state"><div className="empty-icon"><Film size={22} /></div><h3>{title}</h3><p>{detail}</p><button className="button button-outline" onClick={action}>Browse the catalog <ArrowRight size={14} /></button></div> }
function ErrorState({ message }: { message: string }) { return <div className="error-state"><span>!</span><div><strong>Could not load data</strong><p>{message}</p></div></div> }
function MovieSkeleton() { return <div className="movie-grid">{Array.from({ length: 8 }, (_, i) => <div className="skeleton-card" key={i}><div className="skeleton-poster shimmer" /><div className="skeleton-line shimmer" /><div className="skeleton-line short shimmer" /></div>)}</div> }

export default App
