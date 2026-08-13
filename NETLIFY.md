# Netlify එකට දාන හැටි (Python ඕන නැහැ)

මේ site එක **static** — HTML/CSS/JS විතරයි. Netlify free account එකකින් වැඩ.

## හොඳම ක්‍රමය: GitHub → Netlify

1. මේ repo එක GitHub එකේ තියෙනවා නම් Netlify.com → **Add new site** → **Import from Git**
2. repo එක select කරන්න
3. Settings:
   - **Build command:** හිස් තියන්න
   - **Publish directory:** `public`
4. **Deploy site**

විනාඩි 1න් `https://random-name.netlify.app` එනවා.

## නැත්නම්: folder එක drag-and-drop

1. Computer එකේ **`public`** folder එක විතරක් zip කරන්න (ඇතුළේ `index.html`, `css/`, `js/`, `data/` තියෙන්න ඕන)
2. [app.netlify.com/drop](https://app.netlify.com/drop) වලට zip එක හෝ `public` folder එක දාන්න

⚠️ මුළු repo එක (server.py සමඟ) drop කරන්න එපා — ඒකෙන් හිස් page එකක් එනවා. **`public` folder එක විතරක්** drop කරන්න. GitHub import එකේදී `publish = public` automatically වැඩ.

## Sign in

Demo passwords page එකේ නැහැ.

- **පළවෙනි register වෙන කෙනා = Admin**
- ඊට පස්සේ register වෙන හැමෝම students
- Admin panel එකෙන් role මාරු කරන්න පුළුවන්

**Accounts / progress:** Firebase යොදන්න (නිදහස්). Steps: `FIREBASE.md`.
Keys නැත්නම් site එක තාම වැඩ — ඒත් data ටික ඒ browser එකේ විතරයි.

## Local test

```bash
cd public
python3 -m http.server 3000
```

ඊට පස්සේ http://localhost:3000
