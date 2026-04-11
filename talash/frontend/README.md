# Talash Frontend (React + Vite)

This frontend talks to FastAPI backend at `http://localhost:8000`.

## Install

```bash
cd C:\Projects\Talash\talash\frontend
npm install
```

## Run Dev Server

```bash
cd C:\Projects\Talash\talash\frontend
npm run dev
```

## Build

```bash
cd C:\Projects\Talash\talash\frontend
npm run build
```

## Implemented UI

- Fixed dark sidebar with two pages:
	- Upload CV
	- View Candidates
- Upload page:
	- drag-drop or click-select PDF
	- upload spinner
	- success and error cards
- Candidates page:
	- load from `GET /api/cv/candidates`
	- search-by-name filter
	- clickable rows with detail modal

## API Client

`src/api/client.js` uses:

```js
baseURL: 'http://localhost:8000'
```
