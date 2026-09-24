import { useEffect, useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { ImagePlus, LoaderCircle } from 'lucide-react'
import { updateProfile } from '../api/account'
import type { Profile } from '../types'

export default function AvatarPicker({ profile, toast }: { profile: Profile; toast: (message: string) => void }) {
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')
  const queryClient = useQueryClient()
  useEffect(() => {
    if (!file) { setPreview(''); return }
    const url = URL.createObjectURL(file)
    setPreview(url)
    return () => URL.revokeObjectURL(url)
  }, [file])

  const upload = useMutation({
    mutationFn: () => {
      if (!file) throw new Error('Choose an image first.')
      const data = new FormData()
      data.append('avatar', file)
      return updateProfile(data)
    },
    onSuccess: () => {
      setFile(null); setError('')
      queryClient.invalidateQueries({ queryKey: ['profile'] })
      toast('Profile photo updated.')
    },
    onError: (e) => {
      const err = e as { response?: { data?: { detail?: string } }; message?: string }
      setError(err.response?.data?.detail || err.message || 'Upload failed. Please try again.')
    },
  })

  const avatar = preview || (profile.avatar ? `${import.meta.env.VITE_S3_PUBLIC_URL || 'http://localhost:9000/online-cinema'}/${encodeURI(profile.avatar)}` : '')
  const chooseFile = (selected: File | undefined) => {
    setError('')
    if (!selected) { setFile(null); return }
    if (!['image/jpeg', 'image/png'].includes(selected.type)) { setError('Choose a JPG or PNG image.'); return }
    if (selected.size > 1024 * 1024) { setError('The image must be smaller than 1 MB.'); return }
    setFile(selected)
  }

  return <div className="avatar-picker">
    <div className="profile-avatar">{avatar ? <img src={avatar} alt="Profile avatar" onError={(e) => { e.currentTarget.style.display = 'none' }} /> : (profile.username || profile.first_name || 'C')[0].toUpperCase()}</div>
    <label className="avatar-pick-button" htmlFor="avatar-file"><ImagePlus size={13} /> Choose photo</label>
    <input id="avatar-file" className="avatar-file-input" type="file" accept="image/jpeg,image/png" onChange={(e) => { chooseFile(e.target.files?.[0]); e.currentTarget.value = '' }} />
    {file && <div className="avatar-selection"><span>{file.name}</span><button className="button button-bright" type="button" onClick={() => upload.mutate()} disabled={upload.isPending}>{upload.isPending ? <LoaderCircle className="spin" size={14} /> : 'Upload'}</button></div>}
    {error && <p className="avatar-error" role="alert">{error}</p>}
    <small className="avatar-help">JPG or PNG · max 1 MB</small>
  </div>
}
