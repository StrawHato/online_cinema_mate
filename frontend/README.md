# Cinema Club frontend

React, TypeScript and Vite client for the FastAPI service in this repository.

## Run locally

1. Start the API at `http://localhost:8000` (for example, with the project's Docker Compose setup).
2. In this directory run `npm install`, then `npm run dev`.
3. Open the URL printed by Vite, usually `http://localhost:5173`.

Set `FRONTEND_URL` in the backend environment to the frontend's public origin so account activation emails return to the `/activate` screen.

Vite proxies `/api` to the local API, so development does not need a CORS change. Set `VITE_API_URL` in `.env.local` only when the deployed API uses a different origin. The backend's Nginx deployment currently proxies every path to FastAPI; serve the built `dist` files from the frontend host and proxy `/api` requests to that Nginx/API host.

## Build

Run `npm run build`; the production assets are written to `dist/`. `npm run preview` serves that build locally.

## API coverage

- Movie catalog, search, genre filter, sorting, pagination and detail pages
- Registration, login, access token refresh and logout
- Favorites, ratings and comments
- Profile read/update, cart, order creation and Stripe checkout redirect
- Order history
- Profile avatar upload to MinIO and an administrator workspace for adding films, genres and cast members

The current movie response schema does not include a poster image URL. Until the backend exposes one, the UI uses editorial cinema stills from Unsplash. Query and account data always comes from the API. Set `VITE_S3_PUBLIC_URL` to the browser-reachable MinIO bucket URL to display uploaded avatars; for the local compose setup this is `http://localhost:9000/online-cinema`.
