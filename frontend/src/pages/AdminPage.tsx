import { useState, type FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { ArrowRight, Clapperboard, Film, Plus, ShieldCheck, Tags, UserRound } from 'lucide-react'
import { getProfile } from '../api/account'
import * as adminApi from '../api/admin'
import { getGenres } from '../api/movies'

const messageFor = (error: unknown) => {
  const e = error as { response?: { data?: { detail?: unknown } }; message?: string }
  const detail = e.response?.data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((x) => typeof x === 'object' && x && 'msg' in x ? String(x.msg) : String(x)).join('. ')
  return e.message || 'Something went wrong. Please try again.'
}
const csv = (value: string) => value.split(',').map((item) => item.trim()).filter(Boolean)

export default function AdminPage({ toast }: { toast: (message: string) => void }) {
  const profile = useQuery({ queryKey: ['profile'], queryFn: getProfile })
  const genres = useQuery({ queryKey: ['genres'], queryFn: getGenres })
  const queryClient = useQueryClient()
  const [error, setError] = useState('')
  const [name, setName] = useState('')
  const [year, setYear] = useState('')
  const [time, setTime] = useState('')
  const [imdb, setImdb] = useState('')
  const [price, setPrice] = useState('')
  const [certification, setCertification] = useState('')
  const [genreNames, setGenreNames] = useState('')
  const [stars, setStars] = useState('')
  const [directors, setDirectors] = useState('')
  const [description, setDescription] = useState('')
  const [newGenre, setNewGenre] = useState('')
  const [newStar, setNewStar] = useState('')

  const createMovie = useMutation({
    mutationFn: adminApi.createMovie,
    onSuccess: (movie) => {
      toast(`“${movie.name}” was added to the catalog.`)
      setError('')
      queryClient.invalidateQueries({ queryKey: ['movies'] })
      queryClient.invalidateQueries({ queryKey: ['genres'] })
      setName(''); setYear(''); setTime(''); setImdb(''); setPrice(''); setCertification('')
      setGenreNames(''); setStars(''); setDirectors(''); setDescription('')
    },
    onError: (e) => setError(messageFor(e)),
  })
  const addGenre = useMutation({
    mutationFn: adminApi.createGenre,
    onSuccess: () => { toast('Genre created.'); setNewGenre(''); queryClient.invalidateQueries({ queryKey: ['genres'] }) },
    onError: (e) => setError(messageFor(e)),
  })
  const addStar = useMutation({
    mutationFn: adminApi.createStar,
    onSuccess: () => { toast('Cast member created.'); setNewStar('') },
    onError: (e) => setError(messageFor(e)),
  })

  if (profile.isPending) return <section className="subpage"><div className="admin-loading">Loading admin workspace…</div></section>
  if (profile.isError) return <section className="subpage"><div className="error-state"><span>!</span><div><strong>Could not verify your account</strong><p>{messageFor(profile.error)}</p></div></div></section>
  if (profile.data.group !== 'admin') return <section className="subpage"><div className="admin-denied"><ShieldCheck size={25} /><h1>Admin access required</h1><p>This workspace is available to administrator accounts only.</p></div></section>

  const submitMovie = (event: FormEvent) => {
    event.preventDefault(); setError('')
    createMovie.mutate({
      name: name.trim(), year: Number(year), time: Number(time), imdb: Number(imdb), votes: 0,
      meta_score: null, gross: null, price: Number(price), certification: certification.trim(),
      genres: csv(genreNames), stars: csv(stars), directors: csv(directors), description: description.trim(),
    })
  }

  return <section className="subpage admin-page">
    <div className="page-intro"><div className="eyebrow"><span className="eyebrow-line" /> CONTENT MANAGEMENT</div><h1>Admin <em>workspace</em></h1><p>Create films and maintain the catalog's shared lists.</p></div>
    {error && <div className="admin-error" role="alert">{error}</div>}
    <div className="admin-grid">
      <form className="admin-panel admin-movie-form" onSubmit={submitMovie}>
        <div className="admin-panel-heading"><span className="admin-panel-icon"><Clapperboard size={17} /></span><div><small>CATALOG</small><h2>Add a movie</h2></div></div>
        <div className="admin-fields">
          <label className="admin-full">Movie title<input value={name} onChange={(e) => setName(e.target.value)} required maxLength={255} placeholder="e.g. The Grand Budapest Hotel" /></label>
          <label>Release year<input type="number" value={year} onChange={(e) => setYear(e.target.value)} min="1888" max="2100" required /></label>
          <label>Runtime (minutes)<input type="number" value={time} onChange={(e) => setTime(e.target.value)} min="1" required /></label>
          <label>IMDb score<input type="number" value={imdb} onChange={(e) => setImdb(e.target.value)} min="0" max="10" step="0.1" required /></label>
          <label>Price (USD)<input type="number" value={price} onChange={(e) => setPrice(e.target.value)} min="0" step="0.01" required /></label>
          <label>Certification<input value={certification} onChange={(e) => setCertification(e.target.value)} required placeholder="PG-13" /></label>
          <label>Genres <span className="admin-hint">Comma separated</span><input value={genreNames} onChange={(e) => setGenreNames(e.target.value)} required placeholder="Drama, Comedy" /></label>
          <label>Cast <span className="admin-hint">Comma separated</span><input value={stars} onChange={(e) => setStars(e.target.value)} required placeholder="Actor names" /></label>
          <label className="admin-full">Directors <span className="admin-hint">Comma separated</span><input value={directors} onChange={(e) => setDirectors(e.target.value)} required placeholder="Director names" /></label>
          <label className="admin-full">Synopsis<textarea value={description} onChange={(e) => setDescription(e.target.value)} rows={5} required placeholder="A short description of the film…" /></label>
        </div>
        <button className="button button-bright admin-submit" disabled={createMovie.isPending}>{createMovie.isPending ? 'Adding movie…' : 'Add to catalog'} <ArrowRight size={15} /></button>
      </form>

      <div className="admin-side-panels">
        <form className="admin-panel admin-quick-form" onSubmit={(e) => { e.preventDefault(); addGenre.mutate(newGenre.trim()) }}>
          <div className="admin-panel-heading"><span className="admin-panel-icon"><Tags size={17} /></span><div><small>SHARED LISTS</small><h2>Create a genre</h2></div></div>
          <div className="admin-inline-form"><input value={newGenre} onChange={(e) => setNewGenre(e.target.value)} required placeholder="Genre name" /><button className="button button-bright" aria-label="Create genre" disabled={addGenre.isPending}><Plus size={16} /></button></div>
          <div className="admin-chips">{genres.data?.map((genre) => <span key={genre.id}>{genre.name}</span>)}</div>
        </form>
        <form className="admin-panel admin-quick-form" onSubmit={(e) => { e.preventDefault(); addStar.mutate(newStar.trim()) }}>
          <div className="admin-panel-heading"><span className="admin-panel-icon"><UserRound size={17} /></span><div><small>PEOPLE</small><h2>Add a cast member</h2></div></div>
          <div className="admin-inline-form"><input value={newStar} onChange={(e) => setNewStar(e.target.value)} required placeholder="Actor or actress name" /><button className="button button-bright" aria-label="Add cast member" disabled={addStar.isPending}><Plus size={16} /></button></div>
          <p className="admin-note"><Film size={14} /> Directors and cast can also be created automatically when adding a movie.</p>
        </form>
      </div>
    </div>
  </section>
}
