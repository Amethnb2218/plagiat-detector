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
