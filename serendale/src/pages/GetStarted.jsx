import { Link } from 'react-router-dom'
import { useCallback, useMemo, useRef, useState } from 'react'
import '../App.css'

export default function GetStarted() {
  const [fileInfo, setFileInfo] = useState(null)
  const [preview, setPreview] = useState('')
  const [error, setError] = useState('')
  const inputRef = useRef()

  const handleFiles = useCallback(async (files) => {
    if (!files || !files.length) return
    const file = files[0]
    const ext = (file.name.split('.').pop() || '').toLowerCase()
    if (!['json', 'csv'].includes(ext)) {
      setError('Please upload a .json or .csv file')
      setFileInfo(null)
      setPreview('')
      return
    }
    setError('')
    const text = await file.text()
    setFileInfo({ name: file.name, size: file.size, type: ext })
    if (ext === 'json') {
      try {
        const obj = JSON.parse(text)
        const sample = typeof obj === 'object' ? JSON.stringify(obj, null, 2) : String(obj)
        setPreview(sample.slice(0, 800))
      } catch (e) {
        setError('Invalid JSON file')
        setPreview('')
      }
    } else {
      // very light CSV preview: first ~10 lines
      const lines = text.split(/\r?\n/).slice(0, 10)
      setPreview(lines.join('\n'))
    }
  }, [])

  const onDrop = useCallback((e) => {
    e.preventDefault()
    e.stopPropagation()
    const dt = e.dataTransfer
    handleFiles(dt.files)
  }, [handleFiles])

  const onBrowse = useCallback((e) => {
    handleFiles(e.target.files)
  }, [handleFiles])

  const prettySize = useMemo(() => {
    if (!fileInfo) return ''
    const kb = fileInfo.size / 1024
    return kb > 1024 ? (kb/1024).toFixed(2) + ' MB' : kb.toFixed(1) + ' KB'
  }, [fileInfo])

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
                <svg viewBox="0 0 24 24">
                  <path d="M6 18 L18 6" />
                  <path d="M9 6 H18 V15" />
                </svg>
              </span>
            </Link>
          </div>
        </div>
      </header>
      <main className="container" style={{ paddingTop: '10vh', paddingBottom: '10vh' }}>
        <h1 className="ey-gradient slide-in-left delay-1" style={{ textAlign: 'center' }}>Get Started</h1>
        <p className="ey-sub slide-in-right delay-2" style={{ textAlign: 'left', maxWidth: 780 }}>
          Receive continuously verified provider data with a confidence score, so you can act with certainty.</p>

        {/* Dropzone */}
        <div
          className="dropzone slide-up delay-3"
          onDragOver={(e)=>{e.preventDefault();}}
          onDrop={onDrop}
          onClick={()=> inputRef.current?.click()}
        >
          <input ref={inputRef} type="file" accept=".json,.csv,application/json,text/csv" onChange={onBrowse} hidden />
          <div className="dropzone-inner">
            <div className="dropzone-icon" aria-hidden>📄</div>
            <div>
              <div className="dropzone-title">Drag & drop your file here</div>
              <div className="dropzone-sub">or click to browse • Accepted: .json, .csv</div>
            </div>
          </div>
        </div>

  {error && <div className="dz-error slide-up delay-3">{error}</div>}

        {/* File card preview */}
        {fileInfo && (
          <div className="file-card slide-up delay-4">
            <div className="file-row">
              <div className="file-name">{fileInfo.name}</div>
              <div className="file-meta">{fileInfo.type.toUpperCase()} • {prettySize}</div>
            </div>
            {preview && (
              <pre className="file-preview"><code>{preview}</code></pre>
            )}
            <div style={{ marginTop: 16 }}>
              <button className="pill-btn">
                <span className="pill-text">Continue</span>
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
