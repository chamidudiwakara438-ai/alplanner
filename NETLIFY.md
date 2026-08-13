# Netlify — student details SAVE වෙන විදිහ

පරණ site එකේ ළමයි register උනාම database එකේ තිබුණා. Zip එක විතරක් drop කළොත් **browser එකේ විතරයි** තියෙන්නේ — ඒක තමයි details save නොවුණේ.

දැන් accounts **Netlify cloud database** එකේ තියෙනවා. ඒත් **මුළු GitHub repo එක** deploy කරන්න ඕන.

## හරි deploy එක (මේක තමයි ඕනේ)

1. https://app.netlify.com → **Add new site** → **Import an existing project** → GitHub
2. `chamidudiwakara438-ai/alplanner` select කරන්න
3. Branch: `arena/019ffb5a-alplanner` (හෝ main එකට merge කරලා තියෙනවා නම් main)
4. Settings:
   - **Build command:** හිස්
   - **Publish directory:** `public`
5. Deploy

Footer එකේ **Saved online** (කොළ) පේන්න ඕන. ඒක **This browser only** (කහ) නම් functions load වෙලා නැහැ — repo එකම import කරලා තියෙනවද බලන්න.

ඊට පස්සේ ළමයෙක් register උනාම ඕනම phone/PC එකකින් ඒ email/password එකෙන් login වෙන්න පුළුවන්.

පළවෙනි register = Admin.

## වැරදි ක්‍රමය

`public` folder zip එක Netlify Drop වලට දැම්මොත් site එක පේනවා — **ඒත් ළමයිගේ details save වෙන්නේ නැහැ.** Functions එන්නේ Git deploy එකෙන් විතරයි.
