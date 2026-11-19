# OptiLearn Frontend

The Next.js user interface for **OptiLearn**, an AI learning companion built and developed by Nikky. It provides the landing page, Google sign-in flow, classrooms, file management, and tutor chat.

## Stack

- Next.js 16 App Router and React 19
- TypeScript and Tailwind CSS v4
- Radix UI components

## Local setup

```bash
npm ci
Copy-Item .env.example .env.local
npm run dev
```

Set `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` in `.env.local` to the backend origin. The server routes use `BACKEND_URL`; browser requests use the Next proxy. The project defaults to `http://localhost:8000` for local development.

Open `http://localhost:3000`.

## Build and lint

```bash
npm run build
npm run lint
```

## Hosting

Configure Vercel with `frontend/` as the project root and set `NEXT_PUBLIC_BACKEND_URL` and `BACKEND_URL` to the Render backend origin. Set the backend `GOOGLE_REDIRECT_URI` to `https://<your-frontend-domain>/api/auth/callback` and include the Vercel origin in backend CORS settings.

## License

MIT. See the repository [LICENSE](../LICENSE).
