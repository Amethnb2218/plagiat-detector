# PlagiatDetect - Système de Détection de Plagiat par Analyse Sémantique

Plateforme web de détection intelligente de plagiat dans les rapports académiques utilisant l'analyse sémantique profonde (LaBSE) et l'apprentissage cross-lingue.

---

## Prérequis

**La seule chose à installer** : [Docker Desktop](https://www.docker.com/products/docker-desktop/)

- Windows : Télécharger et installer Docker Desktop depuis docker.com
- Le programme doit tourner en arrière-plan (icône dans la barre des tâches)
- Vérifier avec : `docker --version` dans un terminal

**Configuration minimale requise** :
- 8 Go de RAM minimum (16 Go recommandé)
- 15 Go d'espace disque libre
- Windows 10/11 64-bit

---

## Installation et lancement (3 commandes)

```bash
# 1. Cloner le projet
git clone https://github.com/Amethnb2218/plagiat-detector.git
cd plagiat-detector

# 2. Lancer tous les services (première fois : ~5-10 minutes pour télécharger les images)
docker-compose up --build -d

# 3. Créer le compte administrateur
docker-compose exec backend python scripts/create_superuser.py
```

C'est tout. L'application est accessible sur : **http://localhost**

---

## Installation sans Docker (développement)

Si Docker n'est pas disponible, le projet peut tourner directement avec Python et Node.js :

### Prérequis

- Python 3.11+ : [python.org](https://www.python.org/downloads/)
- Node.js 20+ : [nodejs.org](https://nodejs.org/)
- 8 Go de RAM minimum (pour les modèles IA)
- ~5 Go d'espace disque (modèles ML)

### Installation

```bash
# Backend
cd backend
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Linux/Mac

pip install -r requirements.txt
python -m spacy download fr_core_news_lg

# Frontend
cd ../frontend
npm install
```

### Lancement (mode SQLite, sans PostgreSQL/Redis)

```bash
# Terminal 1 - Backend Django
cd backend
venv\Scripts\activate
set USE_SQLITE=True            # Windows cmd
# export USE_SQLITE=True       # Linux/Mac/Git Bash
python manage.py migrate
python manage.py runserver 8000

# Terminal 2 - Frontend React
cd frontend
npm run dev
```

L'application est accessible sur **http://localhost:3000**

> **Note** : En mode SQLite sans Redis/Celery, l'analyse de plagiat fonctionne en mode synchrone (pas de file d'attente). Pour la production ou les gros documents, utiliser Docker ou installer PostgreSQL + Redis séparément.

### Créer un compte administrateur (mode SQLite)

```bash
cd backend
set USE_SQLITE=True
python manage.py createsuperuser
```

---

## Accès à l'application

| URL | Description |
|-----|------------|
| http://localhost | Interface principale (React) |
| http://localhost:8000/api/docs/ | Documentation API Swagger |
| http://localhost:8000/admin/ | Panel d'administration Django |

**Identifiants par défaut** :
- Utilisateur : `admin`
- Mot de passe : `admin123`

---

## Utilisation

### 1. Se connecter
Ouvrir http://localhost et entrer les identifiants admin.

### 2. Téléverser un document
- Aller dans "Documents"
- Glisser-déposer un fichier PDF ou DOCX
- Attendre que le statut passe de "Téléversé" → "En cours" → "Traité"

### 3. Lancer une analyse de plagiat
- Aller dans "Analyses"
- Cliquer "Nouvelle analyse"
- Sélectionner le document à analyser
- (Optionnel) Choisir un document de comparaison
- Cliquer "Lancer l'analyse"

### 4. Consulter les résultats
- Le score global s'affiche avec un code couleur (vert/orange/rouge)
- Les passages suspects sont listés avec le type de plagiat détecté
- Télécharger le rapport PDF via l'icône de téléchargement

---

## Comment ça marche ?

PlagiatDetect utilise l'intelligence artificielle pour comprendre le **sens** des phrases, pas seulement les mots. Voici le principe simplifié :

### Le processus en 4 étapes

```
  DOCUMENT UPLOADÉ           ANALYSE IA              COMPARAISON           RÉSULTAT
  ┌──────────┐          ┌──────────────┐         ┌──────────────┐      ┌──────────┐
  │  PDF ou  │  ──────▶ │ Extraction + │ ──────▶ │ Recherche de │ ───▶ │  Score   │
  │   DOCX   │          │ Découpe en   │         │  similitudes │      │  global  │
  │          │          │   phrases    │         │  dans le     │      │    +     │
  └──────────┘          └──────────────┘         │   corpus     │      │ passages │
                                                  └──────────────┘      └──────────┘
```

1. **Extraction** : Le système lit le PDF/DOCX et en extrait le texte propre
2. **Segmentation** : Le texte est découpé en phrases grâce à SpaCy (qui comprend les abréviations françaises comme "M.", "et al.", etc.)
3. **Vectorisation** : Chaque phrase est transformée en un vecteur de 768 nombres par le modèle LaBSE — ce vecteur représente le **sens** de la phrase, pas ses mots exacts
4. **Comparaison** : Les vecteurs sont comparés avec ceux des autres documents du corpus pour trouver les passages similaires

### Pourquoi c'est plus intelligent qu'une recherche de mots ?

| Situation | Détection classique | PlagiatDetect |
|-----------|-------------------|---------------|
| Copie mot-à-mot | Oui | Oui |
| Reformulation avec synonymes | Non | **Oui** (même sens = vecteurs proches) |
| Traduction depuis l'anglais | Non | **Oui** (LaBSE comprend 109 langues) |
| Paragraphes réorganisés | Non | **Oui** (analyse de la structure) |

### Les 4 détecteurs

| Détecteur | Ce qu'il cherche | Exemple |
|-----------|-----------------|---------|
| **Copie directe** | Texte quasi-identique (≥90%) | "Le climat change" → "Le climat change rapidement" |
| **Paraphrase** | Même sens, mots différents (≥75%) | "Le climat change" → "Les conditions météorologiques se transforment" |
| **Cross-lingue** | Traduction non citée (≥72%) | "Le climat change" → "Climate is changing" |
| **Structurel** | Paragraphes déplacés (>30%) | Mêmes sections mais dans un ordre différent |

### Le score final

```
Score = 40% × paraphrase + 25% × copie directe + 20% × cross-lingue + 15% × structurel
```

- **Vert (< 25%)** : Pas de plagiat significatif
- **Orange (25-49%)** : Passages suspects, vérification conseillée
- **Rouge (≥ 50%)** : Taux élevé, vérification manuelle recommandée

> Pour une explication technique complète, voir [docs/Comment_Ca_Marche.md](docs/Comment_Ca_Marche.md)

---

## Commandes utiles

```bash
# Voir les logs en temps réel
docker-compose logs -f

# Voir les logs d'un service spécifique
docker-compose logs -f backend
docker-compose logs -f celery

# Arrêter l'application
docker-compose down

# Redémarrer
docker-compose up -d

# Tout supprimer (base de données incluse)
docker-compose down -v

# Reconstruire après modification du code
docker-compose up --build -d
```

---

## Architecture technique

```
┌─────────────────────────────────────────────────────┐
│                   NAVIGATEUR                         │
│              http://localhost                         │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              NGINX (Reverse Proxy)                    │
│         Port 80 → Frontend / API                     │
└────┬─────────────────────────────────────┬──────────┘
     │                                     │
┌────▼────────┐                  ┌─────────▼──────────┐
│  FRONTEND   │                  │      BACKEND       │
│   React +   │                  │  Django REST API   │
│ Material UI │                  │    Port 8000       │
└─────────────┘                  └────┬────────┬──────┘
                                      │        │
                          ┌───────────▼─┐  ┌───▼──────┐
                          │ PostgreSQL  │  │  Redis   │
                          │  Port 5432  │  │ Port 6379│
                          └─────────────┘  └────┬─────┘
                                                │
                                    ┌───────────▼───────┐
                                    │  CELERY WORKER    │
                                    │ (Modèles IA)      │
                                    │ LaBSE + FAISS +   │
                                    │ SpaCy + NetworkX  │
                                    └───────────────────┘
```

---

## Technologies utilisées

| Couche | Technologies |
|--------|-------------|
| Frontend | React 18, Material UI 5, TanStack Query, Zustand, Recharts |
| Backend | Django 5.1, Django REST Framework, JWT (SimpleJWT) |
| IA/NLP | LaBSE (768D, 109 langues), Sentence-BERT, SpaCy, PyTorch |
| Recherche vectorielle | FAISS (Facebook AI Similarity Search) |
| Analyse structurelle | NetworkX (isomorphisme de graphes) |
| Base de données | PostgreSQL 16 |
| File de tâches | Celery + Redis |
| Déploiement | Docker Compose + Nginx |

---

## Types de plagiat détectés

1. **Copie directe** (seuil 90%) - Correspondances mot-à-mot
2. **Paraphrase sémantique** (seuil 75%) - Reformulations avec synonymes
3. **Traduction cross-lingue** (seuil 72%) - Texte traduit FR↔EN sans citation
4. **Réorganisation structurelle** (seuil 30%) - Paragraphes déplacés/inversés

**Formule du score global** :
```
Score = 40% × paraphrase + 25% × copie_directe + 20% × cross_lingue + 15% × structurel
```
