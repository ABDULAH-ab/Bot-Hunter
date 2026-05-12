# Bot-Hunter

An AI-powered platform for detecting bot accounts on Twitter/X. Bot-Hunter combines a **Graph Neural Network (GNN)** classification model with a **full-stack web application** to analyze and surface bot activity in real time.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Modules](#modules)
  - [1. ML Model (TMTM)](#1-ml-model-tmtm)
  - [2. Web Application](#2-web-application)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
- [Usage](#usage)
- [Evaluation & Results](#evaluation--results)
- [API Documentation](#api-documentation)
- [Deployment](#deployment)
- [Tech Stack](#tech-stack)
- [Documentation](#documentation)
- [License](#license)

---

## Overview

Bot-Hunter tackles the problem of bot detection on social media through two core components:

1. **TMTM Model** — A Relational Graph Convolutional Network (RGCN) that classifies users as *human* or *bot* using profile metadata, tweet text embeddings (BERTweet), and social-graph structure.
2. **Web Application** — A React + FastAPI platform where users can submit accounts for bot-detection analysis and view results through an interactive dashboard.

---

## Architecture

```
┌───────────────────────────────────────────────────────────────────┐
│                     PREPROCESSING & MODEL                        │
│  Feature engineering · BERTweet embeddings · RGCN (TMTM)         │
│  Train on TwiBot-22 → Fine-tune on custom data                   │
│  → checkpoints/best_model.pt                                     │
└────────────────────────────┬──────────────────────────────────────┘
                             │ trained checkpoint
                             ▼
┌───────────────────────────────────────────────────────────────────┐
│                       WEB APPLICATION                            │
│  Frontend: React · Material-UI · Tailwind CSS                    │
│  Backend:  FastAPI · MongoDB · JWT + Google OAuth                 │
│  BotPredictor loads checkpoint → real-time predictions            │
└───────────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
Bot-Hunter/
│
├── model/                       # ML model module
│   ├── model.py                 # TMTM architecture (RGCN)
│   ├── Dataset.py               # PyG dataset loader (TwiBot-22)
│   ├── train_test.py            # Grid-search training with checkpoints
│   ├── finetune.py              # Fine-tune on custom data
│   ├── preprocess.py            # Entry-point preprocessor
│   ├── preprocess_features.py   # Numerical & categorical features
│   ├── preprocess_text.py       # BERTweet text embeddings
│   ├── preprocess_relations.py  # Social graph edge construction
│   ├── preprocess_tweet_features.py  # Tweet-level behavioral features
│   ├── utils.py                 # Mask & weight init helpers
│   ├── checkpoints/             # Saved model weights
│   ├── processed_data/          # Preprocessed tensors (.pt files)
│   └── results.txt              # Training logs
│
├── Web/                         # Full-stack web application
│   ├── backend/                 # FastAPI server
│   │   ├── main.py              # App entry point
│   │   ├── database.py          # MongoDB connection
│   │   ├── models.py            # Pydantic schemas
│   │   ├── auth_utils.py        # JWT & password hashing
│   │   ├── bot_predictor.py     # Model inference service
│   │   ├── manage_admins.py     # Admin management CLI
│   │   └── routers/             # API route handlers
│   │       ├── auth.py
│   │       ├── users.py
│   │       └── admin.py
│   ├── frontend/                # React SPA
│   │   └── src/
│   │       ├── pages/           # Landing, Login, Signup, Dashboard, ...
│   │       ├── components/      # Navbar, Logo, PrivateRoute, UI atoms
│   │       ├── context/         # AuthContext (global state)
│   │       └── config/          # Token & API settings
│   └── PROJECT_OVERVIEW.md      # Detailed web-app documentation
│
├── preprocessing.py             # Standalone tweet preprocessing (MongoDB)
├── requirements.txt             # Root-level Python dependencies
├── LICENSE                      # MIT License
└── README.md                    # ← You are here
```

---

## Modules

### 1. ML Model (TMTM)

A **T**witter **M**ultimodal **T**wibot **M**odel based on Relational Graph Convolutional Networks (RGCN).

**Architecture:**
- **Input branches:** 4 parallel feature branches
  - Categorical properties (12 dims) — verified, protected, default profile, etc.
  - Numerical properties (41 dims) — follower ratios, growth rates, entropy, etc.
  - Description embedding (768 dims) — BERTweet (`vinai/bertweet-base`)
  - Tweet embedding (768 dims) — mean-pooled BERTweet
- **Graph layers:** 2× RGCN with residual connections + LayerNorm
- **Output:** Binary classification (human vs. bot)

**Training pipeline:**
```bash
cd model

# 1. Preprocess TwiBot-22 dataset
python preprocess.py

# 2. Train with grid search over hyperparameters (5 seeds × 108 configs)
python train_test.py

# 3. Fine-tune best model on custom data
python finetune.py --checkpoint checkpoints/best_model.pt
```

**Hyperparameter search space:**
| Parameter | Values |
|-----------|--------|
| Hidden dimension | 64, 128, 256 |
| Dropout | 0.2, 0.3, 0.4 |
| Epochs | 100, 150, 200 |
| Learning rate | 1e-2, 1e-3, 1e-4 |

The training script supports **checkpoint resumption** — it skips already-completed configurations automatically.

---

### 2. Web Application

A full-stack platform built with **React** (frontend) and **FastAPI** (backend).

**Features:**
- User authentication (email/password + Google OAuth 2.0)
- JWT-based session management with auto-expiry
- Bot detection scans via the `BotPredictor` service
- User dashboard with scan history and analytics
- Admin panel for user management and platform monitoring
- Dark-themed UI with cyan/green accent palette

**API endpoints:**

| Route | Method | Description |
|-------|--------|-------------|
| `/api/auth/signup` | POST | Register |
| `/api/auth/login` | POST | Login |
| `/api/auth/google` | POST | Google OAuth |
| `/api/auth/me` | GET | Current user |
| `/api/users/profile` | GET/PUT | Profile management |
| `/api/admin/users` | GET | List all users (admin) |
| `/api/admin/stats` | GET | Platform stats (admin) |

**Running locally:**
```bash
# Backend
cd Web/backend
python3 -m venv venv && source venv/bin/activate
pip install -r ../../requirements.txt
cp env.example .env   # edit with your credentials
python3 main.py       # → http://localhost:8000

# Frontend
cd Web/frontend
npm install
npm start             # → http://localhost:3000
```

See [`Web/PROJECT_OVERVIEW.md`](Web/PROJECT_OVERVIEW.md) for detailed web-app documentation.

---

## Getting Started

### Prerequisites

- **Python** 3.8+
- **Node.js** 16+
- **MongoDB** Atlas account (or local instance)
- **Google Cloud Console** project (for OAuth, optional)

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/ABDULAH-ab/Bot-Hunter-.git
   cd Bot-Hunter-
   ```

2. **Create and activate a virtual environment:**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # macOS/Linux
   # venv\Scripts\activate    # Windows
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   - Root `.env` — MongoDB URI (`MONGO_URI`)
   - `Web/backend/.env` — MongoDB URL, JWT secret, Google OAuth keys
   - `Web/frontend/.env` — Google OAuth client ID

---

## Usage

### End-to-end workflow

```bash
# Step 1: Preprocess & train the model
cd model
python preprocess.py
python train_test.py

# Step 2: Fine-tune on custom data (optional)
python finetune.py --checkpoint checkpoints/best_model.pt

# Step 3: Launch the web app
cd ../Web/backend
python3 main.py &
cd ../frontend
npm start
```

---

## Evaluation & Results

The **TMTM model** is trained on the **TwiBot-22 dataset** (1M+ labeled accounts) using a grid-search optimization strategy:

- **Validation metric:** Macro-F1 (accounts for class imbalance)
- **Training strategy:** Class-weighted CrossEntropyLoss to address the imbalanced bot/human distribution
- **Regularization:** Early stopping on validation macro-F1 (patience=20 epochs)
- **Multi-seed approach:** 5 random seeds × 108 hyperparameter configurations to ensure robustness
- **Best checkpoint:** Saved as `model/checkpoints/best_model.pt`

**Reliability measures:**
- Multimodal input (profile features + text embeddings + social graph) reduces single-modality bias
- Relational GCN leverages bot-propagation patterns in the graph structure
- Class weighting mitigates false negatives on small bot clusters
- Cross-validation across seeds ensures reproducibility

For detailed preprocessing, architecture, runtime input/output specifications, and evaluation defense, see [model/prepare.md](model/prepare.md).

---

## API Documentation

### Authentication Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/auth/signup` | POST | Register a new user | ✗ |
| `/api/auth/login` | POST | Login with email/password | ✗ |
| `/api/auth/google` | POST | Google OAuth 2.0 login | ✗ |
| `/api/auth/me` | GET | Get current authenticated user | ✓ |

### Bot Prediction Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/predict/from-mongodb` | GET | Predict bot score for a user (from MongoDB) | ✓ |
| `/api/predict/hashtag` | GET | Run hashtag scan + aggregate bot scores | ✓ |
| `/api/predict/hashtag-suggestions` | GET | Get trending hashtag suggestions | ✓ |

### User & Admin Endpoints

| Endpoint | Method | Description | Auth |
|----------|--------|-------------|------|
| `/api/users/profile` | GET/PUT | Get/update user profile | ✓ |
| `/api/admin/users` | GET | List all users (admin only) | ✓ Admin |
| `/api/admin/stats` | GET | Platform usage statistics (admin only) | ✓ Admin |

**Request example:**
```bash
curl -X GET "http://localhost:8000/api/predict/from-mongodb?username=example_user" \
  -H "Authorization: Bearer <JWT_TOKEN>"
```

---

## Deployment

### Local Development (Docker Compose)

```bash
# Build and run all services
docker-compose up --build

# Services will be available at:
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# MongoDB:  localhost:27017
```

### Cloud Deployment (Production)

**Recommended infrastructure:**
- **Container registry:** GitHub Container Registry / DockerHub / AWS ECR
- **Backend:** AWS ECS Fargate, DigitalOcean App Platform, or Google Cloud Run
- **Database:** MongoDB Atlas (managed cloud instance)
- **Storage:** AWS S3 for model artifacts and logs
- **Frontend:** Netlify / Vercel / AWS S3 + CloudFront
- **Monitoring:** Prometheus + Grafana, Sentry for error tracking

**Deployment checklist:**
```bash
# 1. Build images
docker build -t bothunter-backend:v1.0 -f Web/backend/Dockerfile Web/backend
docker build -t bothunter-frontend:v1.0 -f Web/frontend/Dockerfile Web/frontend

# 2. Push to registry
docker push <registry>/bothunter-backend:v1.0
docker push <registry>/bothunter-frontend:v1.0

# 3. Deploy to orchestration platform (ECS / K8s / App Platform)
# ... (platform-specific commands)

# 4. Run smoke tests
curl -X GET http://<deployed-backend>/health
```

**Model deployment:**
- Store trained models in S3 as versioned artifacts (e.g., `s3://bucket/models/v1.0/best_model.pt`)
- Update backend to load from S3 on startup
- Implement canary deployments: route 5–10% traffic to new model version, monitor metrics, then promote or roll back

See [deployment guide](DEPLOYMENT.md) for step-by-step cloud setup (AWS/GCP/Azure).

---

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Data Storage** | MongoDB (Atlas), PyMongo, pandas |
| **ML / Deep Learning** | PyTorch, PyTorch Geometric (RGCN), Transformers (BERTweet), scikit-learn |
| **NLP** | BERTweet (`vinai/bertweet-base`), VADER Sentiment |
| **Backend** | FastAPI, Uvicorn, Pydantic, python-jose (JWT), bcrypt, Google Auth |
| **Frontend** | React 18, React Router, Material-UI, Tailwind CSS, Axios |

---

## Documentation

For deeper technical insights, see:
- **[model/prepare.md](model/prepare.md)** — Preprocessing pipeline, feature engineering, model architecture, runtime examples, and evaluation defense
- **[Web/PROJECT_OVERVIEW.md](Web/PROJECT_OVERVIEW.md)** — Full-stack web app design, API flows, authentication, and database schema
- **[model/IMPROVEMENTS.md](model/IMPROVEMENTS.md)** — Potential enhancements and optimization strategies
- **[model/processed_data_report.md](model/processed_data_report.md)** — Data processing audit and tensor specifications

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

© 2025–2026 Abdullah