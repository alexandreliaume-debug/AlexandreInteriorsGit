# Alexandre Interiors

Static website for [alexandreinteriors.com](https://www.alexandreinteriors.com), built with [Astro](https://astro.build) and deployed to GitHub Pages.

## Local development

```bash
npm install
npm run dev
```

Open [http://localhost:4321](http://localhost:4321).

## Build

```bash
npm run build
npm run preview
```

## Deploy

Pushes to `main` automatically build and deploy via GitHub Actions (`.github/workflows/deploy.yml`).

### Enable GitHub Pages (one-time)

1. Repo **Settings → Pages**
2. **Build and deployment → Source:** GitHub Actions
3. After the first workflow run, set custom domain to `www.alexandreinteriors.com`

## Project structure

- `src/pages/` — site routes matching the original Squarespace URLs
- `src/content/blog/` — blog posts (markdown)
- `public/images/` — migrated images from the live site
- `legacy/` — original Squarespace Bedford template export (reference only)

## URL map

| Path | Page |
|------|------|
| `/` | Home |
| `/about` | About |
| `/services` | Services |
| `/portfolio` | Portfolio index |
| `/russell-square-flat` | Russell Square project |
| `/portfolio/hoxton` | Hoxton project |
| `/inspiration` | Inspiration |
| `/blog` | Blog index |
| `/press` | Press |
| `/contact-us` | Contact |
