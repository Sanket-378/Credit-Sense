import { useRef, useState } from 'react'
import { FileText, FileUp, Trash2, UploadCloud } from 'lucide-react'

const DOCUMENT_TYPES = ['Salary Slip', 'Bank Statement', 'Invoice', 'ID Proof']
const ACCEPTED_TYPES = ['application/pdf', 'image/jpeg', 'image/png']
const ACCEPTED_EXTENSIONS = /\.(pdf|jpe?g|png)$/i
const MAX_FILE_SIZE = 10 * 1024 * 1024

function formatSize(bytes) {
  return bytes < 1024 * 1024
    ? `${Math.max(1, Math.round(bytes / 1024))} KB`
    : `${(bytes / (1024 * 1024)).toFixed(1)} MB`
}

export default function UploadBox({ files, onFilesChange, disabled = false }) {
  const inputRef = useRef(null)
  const [dragging, setDragging] = useState(false)
  const [fileError, setFileError] = useState('')

  function addFiles(fileList) {
    const selectedFiles = Array.from(fileList)
    const validFiles = selectedFiles.filter((file) =>
      (ACCEPTED_TYPES.includes(file.type) || ACCEPTED_EXTENSIONS.test(file.name)) &&
      file.size <= MAX_FILE_SIZE,
    )
    setFileError(validFiles.length < selectedFiles.length
      ? 'Some files were not added. Choose PDF, JPG or PNG files up to 10 MB each.'
      : '')
    onFilesChange((current) => [
      ...current,
      ...validFiles.map((file) => ({
        id: `${file.name}-${file.size}-${file.lastModified}-${Math.random()}`,
        file,
        type: 'Salary Slip',
      })),
    ])
  }

  return (
    <section className="panel upload-panel" aria-label="Upload documents">
      <div
        className={`dropzone ${dragging ? 'dropzone-active' : ''}`}
        onDragOver={(event) => { event.preventDefault(); setDragging(true) }}
        onDragLeave={() => setDragging(false)}
        onDrop={(event) => {
          event.preventDefault()
          setDragging(false)
          if (!disabled) addFiles(event.dataTransfer.files)
        }}
      >
        <input
          ref={inputRef}
          className="sr-only"
          type="file"
          accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png"
          multiple
          disabled={disabled}
          onChange={(event) => {
            if (event.target.files) addFiles(event.target.files)
            event.target.value = ''
          }}
          aria-label="Choose PDF or image documents"
        />
        <div className="upload-icon"><UploadCloud size={23} aria-hidden="true" /></div>
        <p className="drop-title">Drop your documents here</p>
        <p className="drop-copy">or <button type="button" className="text-button" disabled={disabled} onClick={() => inputRef.current?.click()}>browse files</button> from your device</p>
        <p className="file-hint">PDF, JPG or PNG · Up to 10 MB each</p>
      </div>
      {fileError && <p className="error-message upload-error" role="alert">{fileError}</p>}

      {files.length > 0 && (
        <div className="file-list">
          <div className="file-list-heading">
            <h3>Your documents <span className="count-pill">{files.length}</span></h3>
          </div>
          {files.map((item) => (
            <div className="file-row" key={item.id}>
              <div className="file-type-icon"><FileText size={18} aria-hidden="true" /></div>
              <div className="file-meta">
                <p className="file-name">{item.file.name}</p>
                <p className="file-size">{formatSize(item.file.size)}</p>
              </div>
              <label className="sr-only" htmlFor={`document-type-${item.id}`}>Document type for {item.file.name}</label>
              <select
                id={`document-type-${item.id}`}
                className="type-select"
                value={item.type}
                disabled={disabled}
                onChange={(event) => onFilesChange((current) => current.map((file) =>
                  file.id === item.id ? { ...file, type: event.target.value } : file,
                ))}
              >
                {DOCUMENT_TYPES.map((type) => <option key={type}>{type}</option>)}
              </select>
              <button
                type="button"
                className="icon-button remove-file"
                aria-label={`Remove ${item.file.name}`}
                disabled={disabled}
                onClick={() => onFilesChange((current) => current.filter((file) => file.id !== item.id))}
              >
                <Trash2 size={17} aria-hidden="true" />
              </button>
            </div>
          ))}
          <p className="upload-privacy"><FileUp size={14} aria-hidden="true" /> Your files are encrypted and deleted after processing.</p>
        </div>
      )}
    </section>
  )
}
