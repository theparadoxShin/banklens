/**
 * BankLens — Composant principal de l'application.
 * 
 * ARCHITECTURE REACT :
 * - App.jsx : layout principal + gestion de l'état global
 * - FileUpload : composant d'upload de PDF (drag & drop)
 * - Dashboard : affichage des résultats (tableau + graphiques)
 * 
 * CONCEPT CLÉ — useState et useEffect :
 * - useState : crée une variable d'état qui, quand elle change,
 *   re-render le composant automatiquement
 * - useEffect : exécute du code APRÈS le rendu (appels API, etc.)
 */

import { useState } from 'react'
import FileUpload from './components/FileUpload'
import Dashboard from './components/Dashboard'

// URL du backend — en dev c'est localhost, en prod c'est l'URL EKS
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'
// import.meta.env.VITE_API_URL : variable d'environnement Vite
// Toutes les variables VITE_* sont accessibles côté client
// ⚠️ NE JAMAIS mettre de secrets dans des variables VITE_ (visible dans le bundle JS)

function App() {
  // État de l'application
  const [result, setResult] = useState(null)       // Résultat de l'analyse
  const [loading, setLoading] = useState(false)     // Indicateur de chargement
  const [error, setError] = useState(null)          // Message d'erreur

  /**
   * Fonction appelée quand l'utilisateur uploade un PDF.
   * 
   * FormData : l'objet standard du navigateur pour envoyer des fichiers
   * via HTTP. C'est le format multipart/form-data que FastAPI attend.
   */
  const handleUpload = async (file) => {
    setLoading(true)
    setError(null)
    setResult(null)

    const formData = new FormData()
    formData.append('file', file)
    // 'file' correspond au paramètre "file: UploadFile" dans la route FastAPI

    try {
      const response = await fetch(`${API_URL}/api/v1/statements/upload`, {
        method: 'POST',
        body: formData,
        // PAS de Content-Type header ici !
        // Le navigateur le met automatiquement avec le boundary multipart
      })

      if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || 'Erreur serveur')
      }

      const data = await response.json()
      setResult(data)
    } catch (err) {
      setError(err.message || 'Impossible de contacter le serveur')
    } finally {
      setLoading(false)
      // finally s'exécute que ça réussisse ou échoue → on arrête le loading
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b border-gray-200">
        <div className="max-w-6xl mx-auto px-4 py-4 flex items-center gap-3">
          <span className="text-2xl">🏦</span>
          <h1 className="text-xl font-bold text-gray-900">BankLens</h1>
          <span className="text-sm text-gray-500">Extraction intelligente de relevés bancaires</span>
        </div>
      </header>

      {/* Contenu principal */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* Zone d'upload */}
        <FileUpload onUpload={handleUpload} loading={loading} />

        {/* Erreur */}
        {error && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-700">
            <p className="font-medium">❌ Erreur</p>
            <p className="text-sm mt-1">{error}</p>
          </div>
        )}

        {/* Dashboard des résultats */}
        {result && <Dashboard data={result} />}
      </main>

      {/* Footer */}
      <footer className="text-center py-6 text-sm text-gray-400">
        BankLens v1.0 — Daemon Craft Inc. — Propulsé par Claude (AWS Bedrock)
      </footer>
    </div>
  )
}

export default App
