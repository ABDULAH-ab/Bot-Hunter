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
- [Tech Stack](#tech-stack)
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

## Tech Stack

| Layer | Technologies |
|-------|-------------|
| **Data Storage** | MongoDB (Atlas), PyMongo, pandas |
| **ML / Deep Learning** | PyTorch, PyTorch Geometric (RGCN), Transformers (BERTweet), scikit-learn |
| **NLP** | BERTweet (`vinai/bertweet-base`), VADER Sentiment |
| **Backend** | FastAPI, Uvicorn, Pydantic, python-jose (JWT), bcrypt, Google Auth |
| **Frontend** | React 18, React Router, Material-UI, Tailwind CSS, Axios |

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

© 2025 Abdullah