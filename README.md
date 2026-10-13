# CreditSense

CreditSense is a React + Vite frontend for financial health, credit guidance, loan affordability and government scheme discovery. Document verification uses the FastAPI backend in `backend/`; the other feature pages still use mock data.

## Run locally

```bash
npm install
npm run dev
```

Open the local URL printed by Vite. Run `npm run build` to create a production build.

## Document verification backend

See [backend/README.md](./backend/README.md) for Python environment setup, Groq configuration, API run instructions and tests. The frontend reads `VITE_API_URL` from the root `.env` file (default: `http://127.0.0.1:8001`).

Uploaded files are temporarily stored for processing and deleted afterward. ID numbers are masked before verification data is returned or persisted.
