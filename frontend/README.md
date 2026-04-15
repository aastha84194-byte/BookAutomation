# 📚 AI-Powered Book Automation Platform

A high-fidelity, full-stack web application that automates book data collection, generates intelligent AI insights, and enables semantic Q&A over the library using a RAG (Retrieval-Augmented Generation) pipeline.

## 🚀 Key Features

*   **🕵️ Automated Scraping**: Uses Selenium and BeautifulSoup to perform deep-scrapes of book data (Title, Author, Genre, Price, Rating).
*   **🤖 AI Book Insights**: Automatically generates summaries, sentiment analysis, and smart genre classifications using Google Gemini API.
*   **🧠 Semantic Q&A (RAG)**: Chat with your library! Ask questions like "What are some contemporary books?" and get answers cited from the specific book descriptions.
*   **📊 Dynamic Dashboard**: Real-time statistics on book counts, AI processing status, and library diversity.
*   **🎨 Premium UI**: A modern, glassmorphic dark-mode interface built with Next.js and custom CSS animations.

---
## 🛠️ Tech Stack

### Frontend
- **Framework**: [Next.js 15 (App Router)](https://nextjs.org/)
- **Styling**: Vanilla CSS (Modern Custom Properties)
- **API Client**: Fetch + Typed Responses

### Backend
- **Framework**: [Django REST Framework](https://www.django-rest-framework.org/)
- **Async Tasks**: [Celery](https://docs.celeryq.dev/) + [Redis (Upstash)](https://upstash.com/)
- **Vector DB**: [pgvector](https://github.com/pgvector/pgvector) on [Neon PostgreSQL](https://neon.tech/)
- **AI Model**: Google Gemini (gemma-3-27b + gemini-embedding-001)

---
## 🏁 Getting Started

### 1. Prerequisites
- Python 3.10+
- Node.js 18+
- [Upstash Redis](https://upstash.com/) account
- [Neon PostgreSQL](https://neon.tech/) account
- [Google AI Studio](https://aistudio.google.com/) API Key

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # venv\Scripts\activate on Windows
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### 3. Frontend Setup
```bash
cd frontend
pnpm install
pnpm dev
```

---

## 🌎 Deployment (Render Free Tier)

This project is optimized for a unified deployment on Render's Free Tier:
1.  **Shared Instance**: Both Django and Celery run in a single Docker container to stay under free tier limits.
2.  **Memory Optimization**: Celery is limited to `--concurrency=1` to fit within 512MB RAM.
3.  **Static Serving**: WhiteNoise is pre-configured to handle static files without a separate server.

Check the `backend/Dockerfile` and `backend/start.sh` for details.
---
## 📄 License
This project is for educational purposes. Book data is sourced from [books.toscrape.com](http://books.toscrape.com).
