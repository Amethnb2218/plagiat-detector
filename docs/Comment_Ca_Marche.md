# Comment fonctionne PlagiatDetect ?

Ce document explique de manière accessible le fonctionnement du système de détection de plagiat, de l'upload du document jusqu'au score final.

---

## Vue d'ensemble

PlagiatDetect ne se contente pas de chercher des mots identiques entre deux textes. Il **comprend le sens** des phrases grâce à l'intelligence artificielle, ce qui lui permet de détecter :
- Les reformulations (paraphrases)
- Les traductions non sourcées
- Les réorganisations de structure

C'est comme avoir un correcteur qui a lu tous les documents du corpus et qui se souvient du sens de chaque phrase, pas juste des mots.

---

## Etape 1 : Upload et extraction du texte

Quand un enseignant dépose un fichier PDF ou DOCX :

1. Le fichier est validé (type, taille max 50 Mo)
2. Le texte brut est extrait :
   - **PDF** : via `pdfplumber` qui respecte l'ordre de lecture visuel
   - **DOCX** : via `python-docx` qui lit paragraphe par paragraphe
3. Le texte est nettoyé :
   - Suppression des sauts de page, espaces multiples
   - Reconstitution des mots coupés en fin de ligne ("informa-\ntion" → "information")
   - Suppression des numéros de page isolés

**Resultat** : Un texte propre et continu, prêt à être analysé.

---

## Etape 2 : Segmentation en phrases

Le texte est découpé en phrases individuelles par le modèle SpaCy français (`fr_core_news_lg`).

**Pourquoi SpaCy et pas un simple split sur les points ?**

Parce que le français académique est plein de pièges :
- "M. Dupont" → le point après "M" n'est PAS une fin de phrase
- "et al. (2024)" → idem
- "cf. section 3.2" → idem
- "les résultats (p < 0.05) confirment..." → les points dans les parenthèses ne coupent pas

SpaCy a été entraîné sur du texte français et sait gérer tous ces cas.

**Resultat** : Une liste de phrases avec leur position exacte dans le texte (pour pouvoir les surligner plus tard).

---

## Etape 3 : Transformation en vecteurs (embeddings)

C'est l'étape clé qui rend le système intelligent.

### Le concept

Chaque phrase est transformée en un **vecteur de 768 nombres** par le modèle LaBSE (Language-agnostic BERT Sentence Embedding). Ce vecteur représente le **sens** de la phrase dans un espace mathématique à 768 dimensions.

### Pourquoi c'est puissant ?

Deux phrases qui disent la même chose auront des vecteurs proches, même si :
- Les mots sont complètement différents (paraphrase)
- La langue est différente (traduction)

**Exemple concret** :

```
Phrase A : "Le réchauffement climatique menace les espèces"
   → Vecteur : [0.23, -0.15, 0.87, 0.02, ..., 0.41]  (768 nombres)

Phrase B : "Climate change threatens biodiversity"
   → Vecteur : [0.22, -0.14, 0.86, 0.03, ..., 0.40]  (768 nombres)

Phrase C : "Le marché boursier a chuté hier"
   → Vecteur : [-0.45, 0.72, -0.11, 0.55, ..., -0.33]  (768 nombres)
```

Les vecteurs de A et B sont très proches (même sens) → similarité = 0.91
Les vecteurs de A et C sont éloignés (sens différent) → similarité = 0.12

### Pourquoi LaBSE spécifiquement ?

- Il comprend **109 langues** nativement
- Il a été entraîné sur des millions de paires de traductions
- Il place automatiquement les traductions au même endroit dans l'espace vectoriel
- Pas besoin de traduire quoi que ce soit : on compare directement les vecteurs français et anglais

---

## Etape 4 : Indexation FAISS

### Le problème

Si le corpus contient 100 000 phrases, comparer chaque phrase du document suspect avec les 100 000 phrases prendrait trop de temps.

### La solution : FAISS (Facebook AI Similarity Search)

FAISS crée un **index optimisé** qui permet de retrouver les 10 phrases les plus similaires en moins de 1 milliseconde, même dans un corpus de 100 000+ phrases.

C'est comme un annuaire téléphonique : au lieu de lire toutes les pages pour trouver un nom, on va directement à la bonne lettre.

### Comment l'index est organisé

- **Petit corpus (< 1000 phrases)** : Recherche exacte (`IndexFlatIP`) — on compare avec toutes les phrases, c'est assez rapide
- **Grand corpus (≥ 1000 phrases)** : Recherche approximative (`IndexIVFFlat`) — on divise l'espace en clusters et on ne cherche que dans les clusters proches

---

## Etape 5 : Détection de plagiat (4 détecteurs)

Une fois les vecteurs calculés et indexés, 4 détecteurs spécialisés analysent le document :

### Detecteur 1 : Copie directe (seuil ≥ 90%)

**Ce qu'il cherche** : Du texte quasi-identique, copié-collé avec au plus quelques mots changés.

**Comment** : Comparaison caractère par caractère avec l'algorithme SequenceMatcher. Si 90% ou plus des caractères correspondent → copie directe.

**Exemple détecté** :
- Original : "Les changements climatiques représentent un défi majeur pour l'humanité"
- Suspect : "Les changements climatiques représentent un grand défi pour l'humanité"
- Ratio : 93% → PLAGIAT

### Detecteur 2 : Paraphrase sémantique (seuil ≥ 75%)

**Ce qu'il cherche** : Des phrases qui disent la même chose avec des mots différents.

**Comment** : Calcul de la similarité cosinus entre les vecteurs LaBSE. Si la similarité dépasse 75% → paraphrase détectée.

**Exemple détecté** :
- Original : "La biodiversité est menacée par les activités humaines"
- Suspect : "Les espèces vivantes sont en danger à cause de l'homme"
- Similarité : 82% → PARAPHRASE

### Detecteur 3 : Cross-lingue (seuil ≥ 72%)

**Ce qu'il cherche** : Du texte traduit d'une autre langue sans citer la source.

**Comment** : Comme LaBSE comprend 109 langues et place les traductions au même endroit dans l'espace vectoriel, on compare simplement les vecteurs. Pas besoin de traducteur.

**Exemple détecté** :
- Source anglaise : "Artificial intelligence is transforming healthcare delivery"
- Suspect (français) : "L'intelligence artificielle transforme la prestation des soins de santé"
- Similarité : 88% → TRADUCTION NON CITEE

Le seuil est plus bas (72% au lieu de 75%) car la traduction introduit naturellement plus de variation.

### Detecteur 4 : Réorganisation structurelle (seuil > 30%)

**Ce qu'il cherche** : Un document dont les paragraphes ont été réorganisés (sections déplacées, inversées).

**Comment** :
1. Chaque document est modélisé comme un **graphe** (noeuds = paragraphes, liens = ordre séquentiel)
2. On calcule la similarité sémantique entre chaque paragraphe des deux documents
3. On identifie les correspondances (paragraphe 3 du suspect = paragraphe 7 de l'original)
4. On compte les **inversions d'ordre**
5. Score = couverture × taux d'inversion

**Exemple détecté** :
- Original : Introduction → Méthode → Résultats → Discussion
- Suspect : Introduction → Résultats → Méthode → Discussion (mêmes contenus, ordre changé)
- Score structurel : 45% → REORGANISATION

---

## Etape 6 : Calcul du score global

Les 4 scores élémentaires sont combinés avec une pondération qui reflète la gravité de chaque type :

```
Score final = 40% × paraphrase
            + 25% × copie directe
            + 20% × cross-lingue
            + 15% × structurel
```

**Pourquoi cette pondération ?**

- La **paraphrase** (40%) est la forme la plus courante et la plus difficile à détecter manuellement
- La **copie directe** (25%) est grave mais facile à repérer à l'oeil
- Le **cross-lingue** (20%) est de plus en plus fréquent avec les outils de traduction en ligne
- Le **structurel** (15%) est le moins fiable (parfois deux documents ont naturellement une structure similaire)

### Interpretation du score

| Score | Couleur | Interpretation | Action recommandée |
|-------|---------|---------------|-------------------|
| 0-24% | Vert | Pas de plagiat significatif | Aucune action nécessaire |
| 25-49% | Orange | Passages suspects détectés | Vérification manuelle conseillée |
| 50-100% | Rouge | Taux de similarité élevé | Vérification manuelle indispensable |

---

## Etape 7 : Restitution des résultats

L'enseignant voit :

1. **Le score global** avec un code couleur clair
2. **Les passages suspects** listés avec :
   - Le texte du document suspect
   - Le texte source correspondant
   - Le type de plagiat (copie, paraphrase, traduction, structurel)
   - Le pourcentage de similarité
3. **Un rapport PDF** téléchargeable contenant toutes ces informations

---

## Schema récapitulatif complet

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     PIPELINE PLAGIATDETECT                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  UPLOAD              L'enseignant dépose un PDF ou DOCX                  │
│    │                                                                     │
│    ▼                                                                     │
│  EXTRACTION          Le texte brut est extrait et nettoyé                │
│    │                 (pdfplumber / python-docx)                           │
│    ▼                                                                     │
│  SEGMENTATION        Le texte est découpé en phrases                     │
│    │                 (SpaCy fr_core_news_lg)                              │
│    ▼                                                                     │
│  VECTORISATION       Chaque phrase → vecteur 768D (son "sens")           │
│    │                 (modèle LaBSE, 109 langues)                         │
│    ▼                                                                     │
│  INDEXATION          Les vecteurs sont stockés dans un index rapide       │
│    │                 (FAISS - recherche en < 1ms)                         │
│    ▼                                                                     │
│  DETECTION           4 détecteurs cherchent le plagiat :                  │
│    │                 • Copie directe ≥ 90%                               │
│    │                 • Paraphrase ≥ 75%                                  │
│    │                 • Traduction ≥ 72%                                  │
│    │                 • Réorganisation > 30%                              │
│    ▼                                                                     │
│  SCORING             Score final = 40% para + 25% copie                  │
│    │                              + 20% trad + 15% struct                │
│    ▼                                                                     │
│  RESULTAT            Score coloré + passages suspects + rapport PDF       │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Questions fréquentes

### Le système peut-il se tromper ?

Oui, comme tout outil automatisé. Le score est un **indicateur**, pas une preuve absolue :
- **Faux positifs possibles** : Deux étudiants qui citent la même source correctement, ou qui utilisent des formulations standard du domaine
- **Faux négatifs possibles** : Un plagiat très habilement reformulé avec changement complet de structure et de vocabulaire

C'est pourquoi le rapport indique "vérification manuelle recommandée" et non "plagiat confirmé".

### Pourquoi le premier document prend plus de temps ?

Au premier lancement, le système télécharge le modèle LaBSE (~1.8 Go). Ce modèle est ensuite conservé en cache et réutilisé pour toutes les analyses suivantes.

### Le système a-t-il besoin d'internet ?

- **Premier lancement** : Oui, pour télécharger les modèles IA
- **Ensuite** : Non, tout fonctionne en local. Les documents ne quittent jamais votre serveur.

### Quelles langues sont supportées ?

LaBSE supporte 109 langues. Le système est optimisé pour la détection **français ↔ anglais** mais peut théoriquement détecter des traductions entre n'importe quelle paire de langues supportées.

### Quelle est la taille maximale d'un document ?

50 Mo par fichier. Un document de 100 pages est traité en moins de 3 minutes.
