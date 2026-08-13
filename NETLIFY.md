# Netlify — ළමයිගේ details SAVE වෙන විදිහ

පරණ site එකේ ළමයි register උනාම server database එකේ තිබුණා.
**Zip එක විතරක් Drop කළොත් browser එකේ විතරයි** — ඒක තමයි details save නොවුණේ.

දැන් accounts **Netlify Functions + Blobs** වල තියෙනවා. ඒත් **මුළු GitHub repo එක** deploy කරන්න ඕන.

## හරි deploy එක

1. https://app.netlify.com → **Add new site** → **Import an existing project** → GitHub
2. `chamidudiwakara438-ai/alplanner` select කරන්න
3. Branch: `arena/019ffb5a-alplanner`
4. Settings:
   - **Build command:** හිස් (plugins දාන්න එපා)
   - **Publish directory:** `public`
   - **Functions directory:** `netlify/functions`
5. Deploy
6. **Site configuration → Access → Public** (private නම් ළමයිට login වෙන්න බැහැ)
7. Hard refresh: Ctrl+F5

Footer එකේ **Saved online** (කොළ) පේන්න ඕන.
**This browser only** (කහ) නම් Functions load වෙලා නැහැ — repo එකම import කරලා තියෙනවද බලන්න.

ඊට පස්සේ ළමයෙක් register උනාම ඕනම phone/PC එකකින් ඒ email/password එකෙන් login වෙන්න පුළුවන්.

පළවෙනි register = Admin.

## වැරදි ක්‍රමය

`public` folder zip එක Netlify Drop වලට දැම්මොත් site එක පේනවා — **ළමයිගේ details save වෙන්නේ නැහැ.**
Functions එන්නේ Git deploy එකෙන් විතරයි.
