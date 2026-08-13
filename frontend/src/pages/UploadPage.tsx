import { useCallback, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { ImagePlus, Upload } from 'lucide-react'
import { uploadImage } from '../api/images'

const MAX_SIZE_MB = 10
const ALLOWED_TYPES = ['image/jpeg', 'image/png', 'image/webp']

export function UploadPage() {
  const navigate = useNavigate()
  const [preview, setPreview] = useState<string | null>(null)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [progress, setProgress] = useState(0)
  const [dragOver, setDragOver] = useState(false)

  const mutation = useMutation({
    mutationFn: (file: File) => uploadImage(file, setProgress),
    onSuccess: (data) => {
      toast.success('Image uploaded successfully')
      navigate(`/processing/${data.processing_id}`)
    },
    onError: (err: Error) => {
      toast.error(err.message)
      setProgress(0)
    },
  })

  const validateAndSetFile = useCallback((file: File) => {
    if (!ALLOWED_TYPES.includes(file.type)) {
      toast.error('Only JPEG, PNG, and WebP images are allowed')
      return
    }
    if (file.size > MAX_SIZE_MB * 1024 * 1024) {
      toast.error(`File must be under ${MAX_SIZE_MB}MB`)
      return
    }
    setSelectedFile(file)
    setPreview(URL.createObjectURL(file))
  }, [])

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault()
      setDragOver(false)
      const file = e.dataTransfer.files[0]
      if (file) validateAndSetFile(file)
    },
    [validateAndSetFile]
  )

  const handleUpload = () => {
    if (!selectedFile) {
      toast.error('Please select an image first')
      return
    }
    mutation.mutate(selectedFile)
  }

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Upload Image</h2>
        <p className="text-slate-500">Upload a vehicle image for async analysis</p>
      </div>

      <div
        onDragOver={(e) => {
          e.preventDefault()
          setDragOver(true)
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`rounded-xl border-2 border-dashed p-10 text-center transition ${
          dragOver ? 'border-brand-500 bg-brand-50' : 'border-slate-300 bg-white'
        }`}
      >
        {preview ? (
          <img src={preview} alt="Preview" className="mx-auto mb-4 max-h-64 rounded-lg object-contain" />
        ) : (
          <ImagePlus className="mx-auto mb-4 h-16 w-16 text-slate-300" />
        )}
        <p className="mb-2 text-slate-600">Drag and drop an image here, or</p>
        <label className="inline-flex cursor-pointer items-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white hover:bg-brand-700">
          <Upload className="h-4 w-4" />
          Choose file
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            className="hidden"
            onChange={(e) => {
              const file = e.target.files?.[0]
              if (file) validateAndSetFile(file)
            }}
          />
        </label>
        <p className="mt-3 text-xs text-slate-400">JPEG, PNG, WebP · Max {MAX_SIZE_MB}MB</p>
      </div>

      {selectedFile && (
        <div className="rounded-lg border border-slate-200 bg-white p-4">
          <p className="text-sm font-medium text-slate-700">{selectedFile.name}</p>
          <p className="text-xs text-slate-400">{(selectedFile.size / 1024).toFixed(1)} KB</p>
        </div>
      )}

      {mutation.isPending && (
        <div>
          <div className="mb-1 flex justify-between text-sm text-slate-500">
            <span>Uploading...</span>
            <span>{progress}%</span>
          </div>
          <div className="h-2 overflow-hidden rounded-full bg-slate-200">
            <div
              className="h-full bg-brand-500 transition-all"
              style={{ width: `${progress}%` }}
            />
          </div>
        </div>
      )}

      <button
        onClick={handleUpload}
        disabled={!selectedFile || mutation.isPending}
        className="w-full rounded-lg bg-brand-600 py-3 font-medium text-white hover:bg-brand-700 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {mutation.isPending ? 'Uploading...' : 'Upload & Process'}
      </button>
    </div>
  )
}
