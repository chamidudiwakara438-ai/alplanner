# 🚂 Full AL Planner එක online — PythonAnywhere guide (FREE)

**Mokakda meka?** Netlify eka Python run karanna bae (static files witharak). Ape full app eka
(accounts, sims 110, leaderboard, admin, premium) wada karanne **Python server** ekakin — eka
locahost eke `server.py` run wena wage ma online damanna **PythonAnywhere** free account eken.

- 💰 **Rs. 0** — credit card naa
- 🗄️ Ape SQLite database eka **ekama** wada karanawa (Firebase walata maru wenna na!)
- 🌐 Address eka: `OYAAGE-NAME.pythonanywhere.com` (HTTPS free)
- ⏳ Free account limits: storage 512 MB (ape zip ~3 MB 😅), CPU 100 seconds/day (class ekata OK),
  **mase 3 k පාරක් "Renew" button** eka click karanna (free tier rule ekak — click karama tri mase
  na add wenawa — email ekakin matak karanawa)

---

## 🪜 Steps (~15 min)

### 1) Account eka
1. **pythonanywhere.com** → top "Start running Python online" → **Register** (free).
2. Username eka hodhata thiyaganna — eka thamai oyaage site address eka:
   `username.pythonanywhere.com`.

### 2) Files upload
1. Dashboard → **Files** (left menu).
2. `Upload a file` → me zip eka select karala upload: `AL-Planner-...-hosting-ready.zip`
3. Dan Files page eke top "Open **Bash console** here" click karala, type karanna:
   ```bash
   unzip AL-Planner-*.zip -d al-planner
   cd al-planner
   ls        # server.py, wsgi.py, public/ wagenawa pennanna ona
   ```

### 3) Flask install
Free tier eke Flask preinstalled thiyenawa, but safe-side:
```bash
pip3 install --user flask werkzeug
```

### 4) Web app eka hadanna
1. Dashboard → **Web** → **Add a new web app** → Next.
2. ⚠️ **"Flask" eka CLICK KARANNA EPA!** → **"Manual configuration"** select karanna (ape app eka
   already Flask app ekak; manual eken thamai ape code wadda).
3. Python version: **3.10** (koheadera latest) → Next → ඉවරයි.

### 5) WSGI file eka set karanna (🔑 wadagathama step eka)
1. Web page eke "WSGI configuration file" link eka click karanna
   (eken pahala file ekak open wenawa — `var/www/username_pythonanywhere_com_wsgi.py` wagan).
2. **Okkoma DELETE** karala, ape `wsgi.py` eke thiyena dekama paste karanna:
   ```python
   import os, sys
   project_home = '/home/OYAAGE-USERNAME/al-planner'   # 👈 username eka maru karanna!
   if project_home not in sys.path:
       sys.path.insert(0, project_home)
   os.chdir(project_home)
   os.environ.setdefault('AL_DATA_DIR', project_home + '/data')
   os.environ.setdefault('AL_UPLOAD_DIR', project_home + '/uploads')
   os.environ.setdefault('AL_PUBLIC_DIR', project_home + '/public')
   from server import app as application
   ```
   👉 `OYAAGE-USERNAME` තැනට oyaage PythonAnywhere username eka danna.
3. **Save**.

### 6) Reload & open 🎉
1. Web tab top **🔄 Reload username.pythonanywhere.com** (loku green button).
2. Open: **https://username.pythonanywhere.com**
3. Logins (bat eke wage ma):
   - Student: `student@alplanner.lk / student123`
   - Admin: `admin@alplanner.lk / admin123`

Palamu boot eka seconds kihipayak gannawa (database seed wenawa — normal).

---

## 🛠 Waradi una nang

| Problem | Fix |
|---|---|
| Site eka "Something went wrong" | Web tab → **Error log** link eka open karala last line eka balanna — saadhaaranen path ekak waradi (step 5 username eka!) |
| `ModuleNotFoundError: flask` | Bash console: `pip3 install --user flask werkzeug` anik Reload |
| Blank page / no styles | Hard refresh `Ctrl+F5`; wsgi eke `AL_PUBLIC_DIR` line eka thiyenawada balanna |
| DB/data nathi unama | `AL_DATA_DIR` path eka correct da balanna; data eka persist wenawa redeploys wala (PA files delete wenne na) |
| 🤖 Quantum AI "offline" kiyana | Free tier eken **outbound internet** restrict — external AI API block una nis. Built-in offline answers wada; unlock karanna paid plan (=$5/mo) |
| 3-masikana site eka off | Account dashboard eke **"Run until 3 months from today"** button eka click | 

## 💡 Tips
- Students-ta dennam admin password eka maru karanna (Settings / admin) — public site ekak nisa!
- Zip aluthen upload karanna: Files eke old folder eka rename karala ("al-planner-old") aluth eka `al-planner` widihata danna → Reload. (User data `data/alplanner.db` eke — old file copy karala tiyaganna.)
- Domain eka change karanna puluwan paid plan walata; free eke `username.pythonanywhere.com` witharak.
