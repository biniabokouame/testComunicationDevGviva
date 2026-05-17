# FileManager - Gestion des fichiers sans redondance

## Contexte

L’application doit gérer un grand volume de fichiers sans perte de données ni ralentissements majeurs.

L’objectif est de :

- détecter les doublons ;
- détecter les fichiers fortement similaires ;
- éviter les traitements lourds synchrones ;
- assurer une architecture scalable.

---

# Fonctionnalités

## Cas 1 — Fichier totalement différent

Le fichier est enregistré normalement.

## Cas 2 — Fichier identique

Le système refuse l’upload.

## Cas 3 — Fichier fortement similaire ≥ 90 %

Le fichier :

- n’est pas enregistré directement ;
- nécessite une validation administrateur ;
- affiche une comparaison ancien/nouveau.

## Remplacement conditionnel

- validation → remplacement ;
- refus → suppression du nouveau fichier.

---

# Architecture technique

## Backend

- Django
- Celery
- Redis

## Base de données

- SQLite

## Traitement asynchrone

Les traitements lourds sont exécutés avec Celery :

- calcul hash ;
- extraction contenu ;
- comparaison ;
- validation métier.

Redis est utilisé comme broker.

---

# Gestion mémoire

Le projet évite les blocages mémoire grâce à :

- lecture par chunks ;
- tâches asynchrones ;
- séparation des responsabilités.

---

# Formats supportés


- txt
- pdf
- docx
- xls
- xlsx
- csv
- json

---

# Installation

## Cloner le projet

```bash
git clone <repo_url>

```
## Aller dans le projet

```bash
cd development/filemanager

```

## Lancer Docker

```bash

docker compose up --build

```

## Application accessible au http://127.0.0.1:8000/


# Services Docker

## Django
Application web principale.

## Redis
Broker Celery.

## Celery
Traitement asynchrone des fichiers.

---

# Choix techniques

## Docker
Utilisation de Docker pour :
- standardiser l’environnement de développement ;
- faciliter le déploiement des services ;
- simplifier l’orchestration entre Django, Redis et Celery.

## SQLite
- Choisi pour simplifier le développement local.
- Architecture compatible PostgreSQL.

## Celery + Redis
Permet :
- le traitement parallèle ;
- la suppression des traitements lourds HTTP ;
- une meilleure scalabilité ;
- la reprise après erreur.

## Architecture `services/tasks`
Séparation des responsabilités :
- `views`
- `services`
- `tasks`
- `utils`

---

# Limites actuelles

- pas encore d’authentification complète ;
- pas de système OCR ;

---

# Axes d’amélioration

- PostgreSQL ;
- Docker production ;
- Kubernetes ;
- stockage S3 ;
- OCR ;
- comparaison IA ;
- monitoring ;
- tests unitaires ;
- API REST ;
- websocket temps réel.

# Auteur
Abo Kouamé Bini