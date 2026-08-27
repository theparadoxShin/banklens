import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),  // Active TailwindCSS comme plugin Vite
  ],
  server: {
    host: '0.0.0.0',  // Écoute sur toutes les interfaces (nécessaire pour Docker)
    port: 3000,
  }
})
