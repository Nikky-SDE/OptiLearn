# OptiLearn

OptiLearn is an AI learning companion for organizing classroom materials, indexing documents, and asking questions grounded in your course content.

**Built and developed by Nikky** · [GitHub](https://github.com/Nikky-SDE)

## Features

- Organize courses and study files in virtual classrooms.
- Upload documents and index them for semantic and full-text search.
- Ask an AI tutor questions about course materials and follow responses as they stream.
- Sign in with Google and connect Google Classroom and Drive.
- Keep conversations and learning data in PostgreSQL with pgvector.

## Screenshot

<!-- Add a dashboard screenshot at docs/screenshots/dashboard.png. -->

## Tech stack

- Frontend: Next.js 16, React 19, TypeScript, Tailwind CSS, Radix UI
- Backend: Python 3.11+, FastAPI, SQLAlchemy, LangGraph, LangChain
- Data: PostgreSQL with pgvector
- Integrations: Google OAuth/Classroom/Drive, Groq, Nomic
- Hosting: Vercel frontend and Render backend

## Project structure

```text
app/          FastAPI routes, services, RAG, and document processing
frontend/     Next.js App Router application
```

## Local setup

### Backend

1. Create and activate a virtual environment.
2. Install dependencies with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and replace each placeholder with your PostgreSQL, Google OAuth, Groq, and Nomic settings.
4. Configure a PostgreSQL database with the pgvector extension.
5. Start the API:

```bash
uvicorn app.main:app --reload
```

The API docs are available at `http://localhost:8000/docs` and the health route at `http://localhost:8000/health`.

### Frontend

1. In `frontend/`, run `npm ci`.
2. Copy `frontend/.env.example` to `frontend/.env.local` and set the backend URL.
3. Start Next.js:

```bash
cd frontend
npm run dev
```

Open `http://localhost:3000`.

## Environment variables

Set these in local environment files or the hosting provider’s environment settings. `.env` files are ignored by Git; `.env.example` files contain placeholders only.

| Variable |
| --- |
| `DATABASE_URL` |
| `JWT_SECRET` |
| `SECRET_KEY` |
| `FERNET_KEY` |
| `GOOGLE_CLIENT_ID` |
| `GOOGLE_CLIENT_SECRET` |
| `GOOGLE_REDIRECT_URI` |
| `GROQ_API_KEY` |
| `NOMIC_API_KEY` |
| `FRONTEND_URL` |
| `BACKEND_CORS_ORIGINS` |
| `NEXT_PUBLIC_BACKEND_URL` |
| `BACKEND_URL` |

## Deployment

- Frontend: deploy the `frontend/` directory as a Next.js project on Vercel.
- Backend: deploy the repository root on Render using the included `Dockerfile`.
- Set the Google OAuth redirect URI to `https://<your-frontend-domain>/api/auth/callback`.
- Set `BACKEND_CORS_ORIGINS` to include the Vercel frontend origin.

Live URLs will be added after deployment.

## License

MIT. See [LICENSE](LICENSE).
