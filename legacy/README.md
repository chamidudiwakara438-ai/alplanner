# Legacy local server (not used on Netlify)

These files are the old **Express + SQLite** app (`server.js` + `db.js`).
Netlify cannot run them (no persistent disk, no native `better-sqlite3`).

The live site uses:

- `public/` — website
- `netlify/functions/api.js` — student accounts in Netlify Blobs

Keep this folder only if you want to run the old desktop SQLite edition:

```bash
npm install better-sqlite3 express bcryptjs multer
node server.js
```
