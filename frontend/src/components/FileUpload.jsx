/**
 * Composant d'upload de fichier PDF avec drag & drop.
 * 
 * CONCEPT CLÉ — Props :
 * Les props sont les paramètres d'un composant React.
 * { onUpload, loading } sont passés par le composant parent (App).
 * - onUpload : fonction callback appelée quand un fichier est sélectionné
 * - loading : booléen qui indique si l'analyse est en cours
 */

import { useState, useRef } from 'react'

function FileUpload({ onUpload, loading }) {
  const [dragActive, setDragActive] = useState(false)
  const [fileName, setFileName] = useState(null)
  const inputRef = useRef(null)
  // useRef : crée une référence vers un élément DOM
  // Ici, on l'utilise pour accéder au <input type="file"> caché

  const handleFile = (file) => {
    if (file && file.type === 'application/pdf') {
      setFileName(file.name)
      onUpload(file)  // Appelle la fonction du parent
    } else {
      alert('Veuillez sélectionner un fichier PDF.')
    }
  }

  // Gestion du drag & drop
  const handleDrag = (e) => {
    e.preventDefault()
    e.stopPropagation()
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true)
    } else if (e.type === 'dragleave') {
      setDragActive(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    e.stopPropagation()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFile(e.dataTransfer.files[0])
    }
  }

  return (
    <div
      className={`
        border-2 border-dashed rounded-xl p-10 text-center transition-colors cursor-pointer
        ${dragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 bg-white hover:border-gray-400'}
        ${loading ? 'opacity-60 pointer-events-none' : ''}
      `}
      onDragEnter={handleDrag}
      onDragOver={handleDrag}
      onDragLeave={handleDrag}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
    >
      {/* Input caché — déclenché par le clic sur la zone */}
      <input
        ref={inputRef}
        type="file"
        accept=".pdf"
        className="hidden"
        onChange={(e) => handleFile(e.target.files[0])}
      />

      {loading ? (
        <div>
          <div className="animate-spin text-4xl mb-3">⏳</div>
          <p className="text-gray-600 font-medium">Analyse du relevé en cours...</p>
          <p className="text-sm text-gray-400 mt-1">Claude extrait vos transactions</p>
        </div>
      ) : (
        <div>
          <div className="text-4xl mb-3">📄</div>
          <p className="text-gray-700 font-medium">
            {fileName || 'Glissez-déposez votre relevé bancaire ici'}
          </p>
          <p className="text-sm text-gray-400 mt-1">ou cliquez pour sélectionner un fichier PDF</p>
        </div>
      )}
    </div>
  )
}

export default FileUpload
