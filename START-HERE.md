# AL Planner — මෙතනින් පටන් ගන්න

Python ඕන නැහැ. Flask ඕන නැහැ. SQLite ඕන නැහැ.

## PC එකේ බලන්න

```bash
node scripts/preview.js
```

Browser එකේ http://localhost:3000

## Netlify එකට දාන හැටි (ළමයිගේ details SAVE වෙන්න)

**වැරදි:** `public` zip එක Netlify Drop වලට දාන එක — site එක පේනවා, accounts save වෙන්නේ නැහැ.

**හරි:** මුළු GitHub repo එක Netlify එකට Import කරන්න.

1. https://app.netlify.com → Add new site → Import an existing project → GitHub
2. `chamidudiwakara438-ai/alplanner`
3. Branch: `arena/019ffb5a-alplanner`
4. Publish directory = `public` · Functions = `netlify/functions` · Build command හිස්
5. Deploy site
6. Site configuration → Access → **Visitor access = Public**
7. Site එක open කරලා **Ctrl+F5**
8. Footer එකේ **Saved online** (කොළ) ද කියලා බලන්න
9. **Register** — පළවෙනි කෙනා Admin

තව විස්තර: `NETLIFY.md`

## Zip එක

`AL-Planner-netlify.zip` = site + Functions + `netlify.toml`.

GitHub එකට unzip කරලා Netlify Git connect කරන්න. Drop කරන්න එපා.
