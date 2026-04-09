# Free-Tier Cloud Deployment Guide

Deploy Ask My Docs to the cloud using entirely free tiers. This guide uses:

| Service | Provider | Purpose |
|---------|----------|---------|
| Frontend | [Vercel](https://vercel.com) | React SPA hosting |
| Database + pgvector | [Supabase](https://supabase.com) | PostgreSQL with pgvector |
| Redis | [Upstash](https://upstash.com) | Celery broker + result backend |
| Backend + Workers | [Render](https://render.com) | FastAPI + Celery |
| LLM | [Groq](https://console.groq.com) | Fast LLM inference (free tier) |

> **Note on Render free tier:** The free tier spins down after 15 minutes of inactivity, causing a ~30 second cold start on the first request. Upgrade to the $7/mo Starter plan to keep the service warm.

---

## Step 1: Supabase (PostgreSQL + pgvector)

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project (choose a region close to your users)
3. Go to **Settings → Database** and enable the `pgvector` extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Copy your **Connection string** from **Settings → Database → Connection string → URI**
   - Use the `Transaction pooler` URL for the app (port 6543)
   - Format: `postgresql+asyncpg://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:6543/postgres`
5. Set `DATABASE_URL` in your Render environment variables (Step 3)

---

## Step 2: Upstash (Redis)

1. Create a free account at [upstash.com](https://upstash.com)
2. Create a new **Redis** database (select a region)
3. Copy the **Redis URL** from the database details page
   - Format: `rediss://default:[password]@[host]:6379`
4. Set `REDIS_URL` in your Render environment variables (Step 3)

---

## Step 3: Groq (LLM)

1. Create a free account at [console.groq.com](https://console.groq.com)
2. Go to **API Keys** and create a new key
3. Note the key — you'll set `GROQ_API_KEY` in Render (Step 4)
4. The default model is `llama3-70b-8192` (fast, high quality)

---

## Step 4: Render (FastAPI + Celery)

1. Create a free account at [render.com](https://render.com)
2. Connect your GitHub account and select the `read-my-doc` repository

### Deploy the Backend API

3. Click **New → Web Service**
4. Select the `read-my-doc` repository
5. Configure:
   - **Name:** `read-my-doc-backend`
   - **Root Directory:** `backend`
   - **Runtime:** Docker
   - **Dockerfile path:** `backend/Dockerfile`
6. Set environment variables:
   ```
   DATABASE_URL=<your Supabase connection string>
   REDIS_URL=<your Upstash Redis URL>
   JWT_SECRET_KEY=<generate with: openssl rand -hex 32>
   LLM_PROVIDER=groq
   GROQ_API_KEY=<your Groq API key>
   GROQ_MODEL=llama3-70b-8192
   CORS_ORIGINS=https://<your-vercel-domain>.vercel.app
   APP_ENV=production
   ```
7. After deploy, run migrations via the Render Shell:
   ```bash
   alembic upgrade head
   ```

### Deploy the Celery Worker

8. Click **New → Background Worker**
9. Same repository, same root directory
10. Set the same environment variables as the API
11. Override the start command: `celery -A tasks.celery_app worker --loglevel=info`

### Get the Deploy Hook URL

12. In your Render service settings → **Deploy Hooks**, create a hook
13. Copy the URL and add it as `RENDER_DEPLOY_HOOK_URL` in your GitHub repository secrets

---

## Step 5: Vercel (Frontend)

1. Create a free account at [vercel.com](https://vercel.com)
2. Click **Add New → Project** and import the `read-my-doc` repository
3. Configure:
   - **Framework Preset:** Vite
   - **Root Directory:** `frontend`
   - **Build Command:** `npm run build`
   - **Output Directory:** `dist`
4. Set environment variable:
   ```
   VITE_API_URL=https://<your-render-service>.onrender.com
   ```
5. Deploy

### Add GitHub Secrets for Auto-Deploy

6. In your Vercel project → **Settings → General**, copy the **Project ID** and **Org ID**
7. Generate a Vercel token at [vercel.com/account/tokens](https://vercel.com/account/tokens)
8. Add to your GitHub repository secrets:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

---

## Step 6: Verify Deployment

```bash
# Health check
curl https://<your-render-service>.onrender.com/health

# API docs
open https://<your-render-service>.onrender.com/docs
```

Visit your Vercel URL to use the application.

---

## Cost Summary (Free Tiers)

| Provider | Free Limits | Next Tier |
|----------|-------------|-----------|
| Vercel | 100 GB bandwidth/mo, unlimited deployments | $20/mo |
| Supabase | 500 MB database, 5 GB bandwidth | $25/mo |
| Upstash | 10,000 requests/day, 256 MB | $0.20/100K requests |
| Render | 750 hrs/mo (one service), 100 GB bandwidth | $7/mo per service |
| Groq | ~14,400 req/day on free tier | Pay-as-you-go |
