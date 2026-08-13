# AL Planner — Plan Today, Achieve Tomorrow

Sri Lanka's A/L learning site: videos, labs, practicals, exam mode, planner.

**No Python. No Flask. No SQLite.** The live site is `public/` + one Netlify Function that saves student accounts in the cloud.

## Run on your PC

```bash
node scripts/preview.js
# → http://localhost:3000
```

First person who **Register**s becomes Admin. No demo passwords.

## Deploy to Netlify (this is how students SAVE)

Zip-only drag-and-drop shows the website but **does not save accounts**.

1. Push this whole repo to GitHub (already done).
2. Netlify → **Import an existing project** → this repo.
3. Branch: `arena/019ffb5a-alplanner` (or `main` after you merge).
4. Publish directory: `public`
5. Functions directory: `netlify/functions`
6. Build command: **leave empty**
7. Deploy → set **Visitor access = Public**

Footer must say **Saved online** (green). Then a student can register on a phone and log in on a PC.

See **NETLIFY.md**.

## Layout

```
public/                 website (HTML/CSS/JS + videos.json)
netlify/functions/api.js   register / login / progress / admin
netlify.toml            routes /api/* → the function
scripts/preview.js      local server (same API as Netlify)
legacy/                 old Express + SQLite server (not used on Netlify)
```

## Zip

`AL-Planner-netlify.zip` is the full Netlify project (site + Functions + toml).
Import that folder to GitHub / Netlify Git — do **not** drop only `public/`.
