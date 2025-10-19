// GetStarted.jsx
import { Link, useNavigate } from 'react-router-dom'
import { useCallback, useMemo, useRef, useState } from 'react'
import '../App.css'

export default function GetStarted() {
  const [fileInfo, setFileInfo] = useState(null)        // { name, size, type }
  const [selectedFile, setSelectedFile] = useState(null) // File object
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const [serverResp, setServerResp] = useState(null)     // backend response after upload
  const inputRef = useRef()
  const navigate = useNavigate()

  const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
  

  const handleFiles = useCallback(async (files) => {
    if (!files || !files.length) return
    const file = files[0]
    const ext = (file.name.split('.').pop() || '').toLowerCase()

    if (!['json', 'csv'].includes(ext)) {
      setError('Please upload a .json or .csv file')
      setFileInfo(null); setPreview(''); setSelectedFile(null)
      return
    }

    setError('')
    setSelectedFile(file)
    const text = await file.text()
    setFileInfo({ name: file.name, size: file.size, type: ext })

    if (ext === 'json') {
      try {
        const obj = JSON.parse(text)
        const sample = typeof obj === 'object' ? JSON.stringify(obj, null, 2) : String(obj)
        setPreview(sample.slice(0, 800))
      } catch {
        setError('Invalid JSON file'); setPreview('')
      }
    } else {
      const lines = text.split(/\r?\n/).slice(0, 10)
      setPreview(lines.join('\n'))
    }
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault(); e.stopPropagation()
    handleFiles(e.dataTransfer.files)
  }, [handleFiles])

  const onBrowse = useCallback((e) => handleFiles(e.target.files), [handleFiles])

  const prettySize = useMemo(() => {
    if (!fileInfo) return ''
    const kb = fileInfo.size / 1024
    return kb > 1024 ? (kb/1024).toFixed(2) + ' MB' : kb.toFixed(1) + ' KB'
  }, [fileInfo])

  const handleContinue = useCallback(async () => {
    if (!selectedFile) {
      setError('Please select a file first'); return
    }
    try {
      setLoading(true); setError(''); setServerResp(null)

      const form = new FormData()
      form.append('file', selectedFile, selectedFile.name)

      const res = await fetch(`${API_BASE}/ingest/providers`, {
        method: 'POST',
        body: form,
        headers: { Accept: 'application/json' },
      })
      const json = await res.json().catch(() => ({}))

      if (!res.ok) {
        const detail = json?.detail
        const msg = Array.isArray(detail)
          ? detail.map(d => `${(d.loc||[]).join('.')}: ${d.msg}`).join(' | ')
          : (detail || res.statusText || 'Upload failed')
        throw new Error(msg)
      }

      setServerResp(json) // { id, filename, path, type, processed? }
    } catch (e) {
      setError(e.message || 'Upload failed')
    } finally {
      setLoading(false)
    }
  }, [selectedFile, API_BASE])

  return (
    <div className="bg-black text-white min-h-screen flex flex-col">
      <header className="nav">
        <div className="container" style={{ paddingTop: 24 }}>
          <div className="brand">Serendale</div>
          <div>
            <Link to="/" className="pill-btn pill-btn--sm" style={{ display: 'inline-flex', alignItems: 'center' }}>
              <span className="pill-avatar-ring"><span className="pill-avatar" /></span>
              <span className="pill-text">Back to Home</span>
              <span className="pill-arrow" aria-hidden>
                <svg viewBox="0 0 24 24"><path d="M6 18 L18 6" /><path d="M9 6 H18 V15" /></svg>
              </span>
            </Link>
          </div>
        </div>
      </header>

      <main className="container" style={{ paddingTop: '10vh', paddingBottom: '10vh' }}>
        <h1 className="ey-gradient" style={{ textAlign: 'center' }}>Get Started</h1>
        <p className="ey-sub" style={{ textAlign: 'left', maxWidth: 780 }}>
          Receive continuously verified provider data with a confidence score, so you can act with certainty.
        </p>

        {/* Dropzone */}
        <div
          className="dropzone"
          onDragOver={(e)=>{e.preventDefault();}}
          onDrop={onDrop}
          onClick={()=> inputRef.current?.click()}
          role="button"
          aria-label="Upload file"
        >
          <input
            ref={inputRef}
            type="file"
            accept=".json,.csv,application/json,text/csv"
            onChange={onBrowse}
            hidden
          />
          <div className="dropzone-inner">
            <div className="dropzone-icon" aria-hidden>📄</div>
            <div>
              <div className="dropzone-title">Drag & drop your file here</div>
              <div className="dropzone-sub">or click to browse • Accepted: .json, .csv</div>
            </div>
          </div>
        </div>

        {error && <div className="dz-error" role="alert" style={{ marginTop: 12 }}>{error}</div>}

        {/* File card + actions */}
        {fileInfo && (
          <div className="file-card" style={{ marginTop: 16 }}>
            <div className="file-row">
              <div className="file-name">{fileInfo.name}</div>
              <div className="file-meta">{fileInfo.type.toUpperCase()} • {prettySize}</div>
            </div>
            {preview && <pre className="file-preview"><code>{preview}</code></pre>}

            {/* Primary action: upload */}
            {!serverResp && (
              <div style={{ marginTop: 16, display: 'flex', gap: 12 }}>
                <button className="pill-btn" onClick={handleContinue} disabled={loading}>
                  <span className="pill-text">{loading ? 'Uploading…' : 'Continue'}</span>
                </button>
                <button
                  className="pill-btn pill-btn--sm"
                  onClick={() => { setFileInfo(null); setSelectedFile(null); setPreview(''); setServerResp(null); setError(''); }}
                  disabled={loading}
                >
                  <span className="pill-text">Clear</span>
                </button>
              </div>
            )}

            {/* Success: show Go to Dashboard */}
            {serverResp && (
              <div style={{ marginTop: 16, display: 'flex', gap: 12, alignItems: 'center' }}>
                <span style={{ opacity: 0.8 }}>✅ Uploaded: <code>{serverResp.filename}</code></span>
                <button
                  className="pill-btn"
                  onClick={() => navigate('/dashboard', { state: { upload: serverResp } })}
                >
                  <span className="pill-text">Go to Dashboard</span>
                </button>
              </div>
            )}

            {/* Optional: show backend response */}
            {serverResp && (
              <div className="file-server-response" style={{ marginTop: 12 }}>
                <pre className="file-preview"><code>{JSON.stringify(serverResp, null, 2)}</code></pre>
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  )
}
