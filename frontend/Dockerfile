# === BUILD STAGE (multi-stage build) ===
# On utilise une image Node pour CONSTRUIRE l'app React
# Mais on ne la déploie PAS avec Node — on utilise Nginx (serveur web léger)
FROM node:22-alpine AS builder

WORKDIR /app

# Copie les fichiers de dépendances d'abord (cache Docker)
COPY package.json package-lock.json ./
RUN npm ci
# npm ci ("clean install") : installe les dépendances EXACTES du lockfile
# Plus fiable que "npm install" pour la reproductibilité

# Copie le code source et build
COPY . .

# Variable d'environnement pour l'URL de l'API en production
# Sera overridée par le ConfigMap Kubernetes
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build
# npm run build → Vite compile le JSX en HTML/CSS/JS statique dans dist/

# === PRODUCTION STAGE ===
# Nginx : serveur web ultra-léger et performant (~25MB)
# Il sert les fichiers statiques (HTML/CSS/JS) générés par Vite
FROM nginx:alpine

# Copie les fichiers buildés depuis l'étape précédente
COPY --from=builder /app/dist /usr/share/nginx/html

# Config Nginx personnalisée
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 3000

CMD ["nginx", "-g", "daemon off;"]
# "daemon off" : Nginx tourne au premier plan (nécessaire pour Docker/K8s)
# Sans ça, Nginx se met en arrière-plan et le container s'arrête immédiatement
