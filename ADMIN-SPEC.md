# 🛡️ AL Planner — Complete Admin Panel Specification (Master Checklist)

Source: Team Akoit spec (2026-08-11). Status updated each build.
Legend: ✅ done · 🟡 partial · ❌ not yet · ⛔ not planned (why)

## 1. 📊 Dashboard
- ✅ Total students / active / new registrations (30d)
- ✅ Total teachers / tutors / lessons / resources / past papers
- ✅ Pending student uploads · pending comments · pending slips
- ✅ Revenue (total) → **today / 7d / 30d cards: v p**
- ✅ Student growth chart · activity chart · popular subjects donut
- ✅ Recent activity feed · top-5 students · system status
- ✅ Exams sat / exam average
- ❌ Total challenges card → **v p** (with Weekly Challenge)
- ✅ AI questions today → **v p**
- ❌ Pending essay marking (needs Essays, section 18/19)
- ❌ Revenue chart per-day (has activity chart; per-day revenue later)

## 2. 👨‍🎓 Student Management
- ✅ View all / search / view full profile (stats + recent activity)
- ✅ See account creation date + last seen
- ✅ Rankings view
- 🟡 Filters → **v p: A/L year + district + medium filters**
- ✅ Suspend / restore → **v p** (login blocked while suspended)
- ✅ Reset password (admin generates temp password; share manually) → **v p**
- ✅ **Login as Student (impersonate + safe exit)** → **v p**
- ✅ Delete account
- ❌ Send password reset EMAIL (needs email system, sec. 32)
- 🔐 Passwords are NEVER visible to admin (hash only) ✅ by design

## 3. 👨‍🏫 Teacher Management
- ✅ Add / edit / delete / photo / bio / subjects
- ✅ Lessons-taught link (lessons have teacher)
- ❌ Teacher public registration + approve/reject (teachers are admin-added today)
- ❌ Ratings / reviews · verification badge

## 4. 🧑‍🏫 Tutor Marketplace
- ✅ Tutor add/edit/delete · subjects · A/L-O/L level · medium · online/physical · district
- ✅ Contact details · qualification/experience · featured ⭐
- ✅ Student inquiries (admin Messages tab)
- ❌ Tutor self-registration + approve flow (admin-managed today)
- ❌ Leads pipeline / commission tracking (needs payments gateway phase)

## 📚 CONTENT
## 5. Subjects — ✅ add/edit/delete/icon/colors (code change නැතුව)
- ❌ enable/disable toggle + custom order (delete exists)

## 6. A/L Years — ✅ dynamic add/edit/enable (Years tab)

## 7. Mediums — 🟡 EN/SI/TA built-in; dynamic adding later (needs translation work per medium)

## 8. Sections — ❌ single-level Units today; Sections = bigger refactor (planned v q+)

## 9. Units — ✅ per subject, order ✅; ❌ tri-lingual names (single name + site-wide i18n today)

## 10. Lessons — ✅ title/desc/unit/teacher/video/notes/theory/order + sims
- ❌ difficulty / estimated time / objectives / exam-tips fields (structured metadata later)

## 11. 🎥 YouTube Videos — ✅ URL/playlist, auto-thumbnail via YouTube, publish = lesson visibility
- ❌ teacher-specific video list view (per-teacher page shows lessons)

## 📄 RESOURCES
## 12. Resource Management — ✅ categories/upload/edit/publish/unpublish/delete/downloads count
- ✅ Copyright note in START-HERE (admin responsibility)

## 13. Past Papers — ✅ subject/year/medium/PDF/marking scheme (category)
## 14. Model Papers — ✅ same flow (category + author via title)

## 🏆 EXAM / COMPETITION
## 15. Weekly Challenge → **v p (lean)**: admin schedules title/subject/mode/dates + 1st-2nd-3rd prizes; students sit timed paper; one attempt; auto leaderboard.
- ❌ paid challenges (needs gateway)

## 16. Question Bank — ✅ QBank tab (real Q&A typed by admin) + per-lesson MCQs + 46 sim banks
- 🟡 difficulty/marks/tags fields — partial

## 17. MCQ Exam — ✅ Exam Mode: random questions + shuffled options + timer + auto marking + grades
- 🟡 admin-curated paper (schedule/publish) = Weekly Challenge lean covers scheduling

## 18. Structured Essay — ❌ (upload answer + assign marker + feedback) — planned v q+
## 19. Essay — ❌ same workflow — planned v q+

## 20. 📤 Student Resource Upload — ✅ pending→review→approve/publish + reject reason

## 🏅 RANKING
## 21. Ranking System — ✅ leaderboard (weekly minutes + lessons), exam avg in Rankings tab
- ❌ district/school/subject boards (data exists — boards later)
- ❌ tie-break rules editor (default: minutes→lessons→id)

## 22. 🎁 Prize Management → **v p (lean)**: prizes on challenge (text) + winner status Pending→Verified→Sent→Delivered on top-3 rows

## 💳 MONEY
## 23. Payment Management — ✅ slips: ID/student/amount/date/status (Pending/Approved/Rejected)
- ❌ gateway (PayHere) + auto unlock — when merchant account arrives
## 24. Revenue → **v p**: today/7d/30d/total cards
- ❌ gateway fees / refunds / expenses / net (needs gateway)
## 25. 🎟️ Coupons → **v p (lean)**: create % or fixed, expiry, usage limit, activate/deactivate — applies to Premium price

## 🤖 AI
## 26. AI Tutor — ✅ EN/SI/TA, A/L-scoped, per-day limits
## 27. AI Admin Controls → **v p**: on/off ✅, key/CLEAR ✅, **+ free/pro daily limits, model, extra system prompt**
## 28. AI Knowledge Base → **v p**: admin adds syllabus notes/facts → injected into AI answers
## 29. AI Reports → **v p**: student "🚩 Report" on any AI answer → admin reviews → mark resolved

## 🔔 COMMUNICATION
## 30. Notifications — 🟡 admin bell ✅ (unread messages/comments); student in-app notifications later
## 31. Announcements — ✅ announcement bar (Site tab, scheduled not yet)
## 32. Email System — ❌ (needs SMTP — later phase; all flows work in-app for now)

## 📈 ANALYTICS
## 33. Student Analytics — ✅ growth/active/retention-ish (7d active) charts
## 34. Content Analytics — ✅ downloads count; most-viewed lessons later
## 35. Exam Analytics — ✅ per-user stats + admin avg; per-question difficulty later
## 36. AI Analytics → **v p**: today/total counts; topic/language breakdown later

## 🗂️ FILES
## 37. Media Manager → **v p**: browse uploads (size/date), delete files safely

## 🌐 WEBSITE CONTROL
## 38. Website Settings — ✅ name/contacts/announcement/switches (register/upload/leaderboard/comments/AI)
- ❌ logo/favicon uploader (files exist in assets; uploader later)
- ❌ maintenance mode screen

## 39. Homepage Content — 🟡 announcement + AI hero card + stats auto-real; testimonials/FAQ editor later

## 👥 ADMIN SYSTEM
## 40. Admin Users & Roles — ❌ single Super Admin today; role matrix = big phase (with sec. 41 2FA)

## 🔐 SECURITY
## 41. Authentication — ✅ secure sessions (httponly), password hashing (scrypt)
- ❌ email verification / 2FA — with email system
## 42. Student passwords — ✅ never visible; ✅ reset + login-as (v p)
## 43. API Security — ✅ Gemini key server-secret (never sent to browser) ✅ leak-tested
## 44. Payment Security — ✅ slip = human-verify; gateway callback verify comes with gateway

## 📋 AUDIT LOG
## 45. Admin Activity Log → **v p**: admin/action/target/time for all key mutations + Logs tab

## 💾 BACKUP
## 46. Backup & Export — ✅ one-click DB backup (10 kept) + download
- ✅ **CSV exports: students / payments / exam results / questions → v p**

## ⚙️ SYSTEM SETTINGS
## 47. Dynamic Settings — ✅ years/subjects/switches/AI/premium price & bank without code edits

---
### Phase queue after v p
1. Weekly Challenge v2 (paid entry, question-bank papers, subject boards)
2. Essays (structured + essay) with marker workflow
3. Admin roles + email system + 2FA
4. Sections (subject → section → unit), lesson metadata fields
5. Notifications for students + homepage CMS blocks

---

## ✅ Simulator System Spec (2026-08-11q) — status

- ✅ Interactive Labs page: 5 subject cards (icon, sim count, difficulty range, "Explore Lab"), safety notice, per-sim difficulty dots
- ✅ Combined Maths Lab — 8 sims: gplot, gtrans, deriv, integr, vector, trig, prob, stats (graphs/calculus/vectors/probability)
- ✅ ICT Lab — 8 sims: binary, logic, truthtab, cpu, network, ipaddr, sortvis, webplay (safe sandboxed iframe, **no code execution**)
- ✅ Challenge Mode per sim (goal text + ✅ Check + hints; 🎉 +15 XP first win / +2 repeat, server-validated, unique-per-student)
- ✅ Badges: 🎖️ chal_first, 🏆 chal_10, 📐 maths_solver, 💻 ict_explorer (+ existing 🧪 etc.)
- ✅ Ask-AI inside every sim (chips + free text + live slider context; guest → login prompt; premium limits respected)
- ✅ DB-driven simulator catalog (sim_catalog) — admin Simulators tab: edit metadata, difficulty, XP, badge, unit/lesson pinning, enable/disable/publish, preview
- ✅ Analytics: launches, unique students, completions, challenge wins, today/week/month cards, 8-day usage chart
- ✅ Related simulators chips on lesson pages (via ?unit_id= pins in catalog)
- ✅ New tables: sim_catalog, sim_launches, sim_challenge_wins (no duplicate student systems; reuses sim_progress for quiz stats)
**v r (2026-08-12) — Simulator Library COMPLETE, 87 total:**
- ✅ Bio +6 (meiosis, natural selection, population growth, enzyme kinetics, respiration map, food-chain pyramid) → **Bio hits 17/17 from the list**
- ✅ Chem +2 (Equilibrium & Le Chatelier — Haber / NO₂ tube / esterification presets; Virtual Chemistry Bench with real reaction matrix)
- ✅ Physics +7 (free fall, friction, plane-mirror reflection, resistor colour code, RC charge/discharge, transformer, energy-conservation track)
- ✅ Maths +5 (matrix 2×2 live plane-transform, complex Argand plane, coordinate geometry, sequences & series, projectile parametric)
- ✅ ICT +5 (offline SQL playground engine, flowchart tracer, Boolean algebra lab, memory/storage units, program step visualizer)
- ✅ Physics lesson auto-rules: "free fall" → freefall, "capacit" / "time constant" → rc, "transformer" → transformer
- ✅ eZ Cash payments (r2): Premium page method tabs (🏦 slip / 📱 eZ Cash), admin-settable eZ Cash number
  (Site → 💎 section), Transaction-ID + mobile submit → pending; unique-txn & mobile validation, 3-pending cap;
  admin Approve/Reject on the same Payments tab (method shown as 📱 eZ Cash chip with txn + mobile)
- ✅ Every new sim: 🎖️ challenges (+15/+2 XP), 🤖 Ask-AI context, 5-question MCQ bank, lab/CSV table support
- ⏳ Still queued from the spec: weekly sim leaderboard screen, per-language challenge text,
  AI-daily-challenge generator, mobile fullscreen pass

## v2026.08.12s — Chemistry Virtual Practical Laboratory
- New sim type `chemlab` (subject chem, difficulty hard) — 12 database-driven practicals in one engine (sims-chemlab.js).
- New tables: `lab_notes (user_id, prac, data JSON, PK user+prac)` · `lab_progress (user_id, prac, best, done, PK user+prac)` — mirrored in db.js (Node mode).
- New APIs: `GET /api/chemdb` (public teacher profiles) · `POST /api/admin/chemdb` {kind: flame|precip, ...validated, true-colour hex enforced, max 60} · `POST /api/admin/chemdb/del` {idx} · `GET /api/lab/state` · `POST /api/lab/note` {prac, data{8 fields, 2000 chars each}} · `POST /api/lab/progress` {prac, score 0-100, done} (best=MAX).
- Teacher profiles persist in site_settings key `chemdb_extra` (JSON list) and merge into the flame/precipitation shelves at mount.
- Admin UI: ⚙️ Site → 🧪 Chem lab database (list + delete + two add forms).
# 🛡️ AL Planner — Complete Admin Panel Specification (Master Checklist)

Source: Team Akoit spec (2026-08-11). Status updated each build.
Legend: ✅ done · 🟡 partial · ❌ not yet · ⛔ not planned (why)

## 1. 📊 Dashboard
- ✅ Total students / active / new registrations (30d)
- ✅ Total teachers / tutors / lessons / resources / past papers
- ✅ Pending student uploads · pending comments · pending slips
- ✅ Revenue (total) → **today / 7d / 30d cards: v p**
- ✅ Student growth chart · activity chart · popular subjects donut
- ✅ Recent activity feed · top-5 students · system status
- ✅ Exams sat / exam average
- ❌ Total challenges card → **v p** (with Weekly Challenge)
- ✅ AI questions today → **v p**
- ❌ Pending essay marking (needs Essays, section 18/19)
- ❌ Revenue chart per-day (has activity chart; per-day revenue later)

## 2. 👨‍🎓 Student Management
- ✅ View all / search / view full profile (stats + recent activity)
- ✅ See account creation date + last seen
- ✅ Rankings view
- 🟡 Filters → **v p: A/L year + district + medium filters**
- ✅ Suspend / restore → **v p** (login blocked while suspended)
- ✅ Reset password (admin generates temp password; share manually) → **v p**
- ✅ **Login as Student (impersonate + safe exit)** → **v p**
- ✅ Delete account
- ❌ Send password reset EMAIL (needs email system, sec. 32)
- 🔐 Passwords are NEVER visible to admin (hash only) ✅ by design

## 3. 👨‍🏫 Teacher Management
- ✅ Add / edit / delete / photo / bio / subjects
- ✅ Lessons-taught link (lessons have teacher)
- ❌ Teacher public registration + approve/reject (teachers are admin-added today)
- ❌ Ratings / reviews · verification badge

## 4. 🧑‍🏫 Tutor Marketplace
- ✅ Tutor add/edit/delete · subjects · A/L-O/L level · medium · online/physical · district
- ✅ Contact details · qualification/experience · featured ⭐
- ✅ Student inquiries (admin Messages tab)
- ❌ Tutor self-registration + approve flow (admin-managed today)
- ❌ Leads pipeline / commission tracking (needs payments gateway phase)

## 📚 CONTENT
## 5. Subjects — ✅ add/edit/delete/icon/colors (code change නැතුව)
- ❌ enable/disable toggle + custom order (delete exists)

## 6. A/L Years — ✅ dynamic add/edit/enable (Years tab)

## 7. Mediums — 🟡 EN/SI/TA built-in; dynamic adding later (needs translation work per medium)

## 8. Sections — ❌ single-level Units today; Sections = bigger refactor (planned v q+)

## 9. Units — ✅ per subject, order ✅; ❌ tri-lingual names (single name + site-wide i18n today)

## 10. Lessons — ✅ title/desc/unit/teacher/video/notes/theory/order + sims
- ❌ difficulty / estimated time / objectives / exam-tips fields (structured metadata later)

## 11. 🎥 YouTube Videos — ✅ URL/playlist, auto-thumbnail via YouTube, publish = lesson visibility
- ❌ teacher-specific video list view (per-teacher page shows lessons)

## 📄 RESOURCES
## 12. Resource Management — ✅ categories/upload/edit/publish/unpublish/delete/downloads count
- ✅ Copyright note in START-HERE (admin responsibility)

## 13. Past Papers — ✅ subject/year/medium/PDF/marking scheme (category)
## 14. Model Papers — ✅ same flow (category + author via title)

## 🏆 EXAM / COMPETITION
## 15. Weekly Challenge → **v p (lean)**: admin schedules title/subject/mode/dates + 1st-2nd-3rd prizes; students sit timed paper; one attempt; auto leaderboard.
- ❌ paid challenges (needs gateway)

## 16. Question Bank — ✅ QBank tab (real Q&A typed by admin) + per-lesson MCQs + 46 sim banks
- 🟡 difficulty/marks/tags fields — partial

## 17. MCQ Exam — ✅ Exam Mode: random questions + shuffled options + timer + auto marking + grades
- 🟡 admin-curated paper (schedule/publish) = Weekly Challenge lean covers scheduling

## 18. Structured Essay — ❌ (upload answer + assign marker + feedback) — planned v q+
## 19. Essay — ❌ same workflow — planned v q+

## 20. 📤 Student Resource Upload — ✅ pending→review→approve/publish + reject reason

## 🏅 RANKING
## 21. Ranking System — ✅ leaderboard (weekly minutes + lessons), exam avg in Rankings tab
- ❌ district/school/subject boards (data exists — boards later)
- ❌ tie-break rules editor (default: minutes→lessons→id)

## 22. 🎁 Prize Management → **v p (lean)**: prizes on challenge (text) + winner status Pending→Verified→Sent→Delivered on top-3 rows

## 💳 MONEY
## 23. Payment Management — ✅ slips: ID/student/amount/date/status (Pending/Approved/Rejected)
- ❌ gateway (PayHere) + auto unlock — when merchant account arrives
## 24. Revenue → **v p**: today/7d/30d/total cards
- ❌ gateway fees / refunds / expenses / net (needs gateway)
## 25. 🎟️ Coupons → **v p (lean)**: create % or fixed, expiry, usage limit, activate/deactivate — applies to Premium price

## 🤖 AI
## 26. AI Tutor — ✅ EN/SI/TA, A/L-scoped, per-day limits
## 27. AI Admin Controls → **v p**: on/off ✅, key/CLEAR ✅, **+ free/pro daily limits, model, extra system prompt**
## 28. AI Knowledge Base → **v p**: admin adds syllabus notes/facts → injected into AI answers
## 29. AI Reports → **v p**: student "🚩 Report" on any AI answer → admin reviews → mark resolved

## 🔔 COMMUNICATION
## 30. Notifications — 🟡 admin bell ✅ (unread messages/comments); student in-app notifications later
## 31. Announcements — ✅ announcement bar (Site tab, scheduled not yet)
## 32. Email System — ❌ (needs SMTP — later phase; all flows work in-app for now)

## 📈 ANALYTICS
## 33. Student Analytics — ✅ growth/active/retention-ish (7d active) charts
## 34. Content Analytics — ✅ downloads count; most-viewed lessons later
## 35. Exam Analytics — ✅ per-user stats + admin avg; per-question difficulty later
## 36. AI Analytics → **v p**: today/total counts; topic/language breakdown later

## 🗂️ FILES
## 37. Media Manager → **v p**: browse uploads (size/date), delete files safely

## 🌐 WEBSITE CONTROL
## 38. Website Settings — ✅ name/contacts/announcement/switches (register/upload/leaderboard/comments/AI)
- ❌ logo/favicon uploader (files exist in assets; uploader later)
- ❌ maintenance mode screen

## 39. Homepage Content — 🟡 announcement + AI hero card + stats auto-real; testimonials/FAQ editor later

## 👥 ADMIN SYSTEM
## 40. Admin Users & Roles — ❌ single Super Admin today; role matrix = big phase (with sec. 41 2FA)

## 🔐 SECURITY
## 41. Authentication — ✅ secure sessions (httponly), password hashing (scrypt)
- ❌ email verification / 2FA — with email system
## 42. Student passwords — ✅ never visible; ✅ reset + login-as (v p)
## 43. API Security — ✅ Gemini key server-secret (never sent to browser) ✅ leak-tested
## 44. Payment Security — ✅ slip = human-verify; gateway callback verify comes with gateway

## 📋 AUDIT LOG
## 45. Admin Activity Log → **v p**: admin/action/target/time for all key mutations + Logs tab

## 💾 BACKUP
## 46. Backup & Export — ✅ one-click DB backup (10 kept) + download
- ✅ **CSV exports: students / payments / exam results / questions → v p**

## ⚙️ SYSTEM SETTINGS
## 47. Dynamic Settings — ✅ years/subjects/switches/AI/premium price & bank without code edits

---
### Phase queue after v p
1. Weekly Challenge v2 (paid entry, question-bank papers, subject boards)
2. Essays (structured + essay) with marker workflow
3. Admin roles + email system + 2FA
4. Sections (subject → section → unit), lesson metadata fields
5. Notifications for students + homepage CMS blocks

---

## ✅ Simulator System Spec (2026-08-11q) — status

- ✅ Interactive Labs page: 5 subject cards (icon, sim count, difficulty range, "Explore Lab"), safety notice, per-sim difficulty dots
- ✅ Combined Maths Lab — 8 sims: gplot, gtrans, deriv, integr, vector, trig, prob, stats (graphs/calculus/vectors/probability)
- ✅ ICT Lab — 8 sims: binary, logic, truthtab, cpu, network, ipaddr, sortvis, webplay (safe sandboxed iframe, **no code execution**)
- ✅ Challenge Mode per sim (goal text + ✅ Check + hints; 🎉 +15 XP first win / +2 repeat, server-validated, unique-per-student)
- ✅ Badges: 🎖️ chal_first, 🏆 chal_10, 📐 maths_solver, 💻 ict_explorer (+ existing 🧪 etc.)
- ✅ Ask-AI inside every sim (chips + free text + live slider context; guest → login prompt; premium limits respected)
- ✅ DB-driven simulator catalog (sim_catalog) — admin Simulators tab: edit metadata, difficulty, XP, badge, unit/lesson pinning, enable/disable/publish, preview
- ✅ Analytics: launches, unique students, completions, challenge wins, today/week/month cards, 8-day usage chart
- ✅ Related simulators chips on lesson pages (via ?unit_id= pins in catalog)
- ✅ New tables: sim_catalog, sim_launches, sim_challenge_wins (no duplicate student systems; reuses sim_progress for quiz stats)
**v r (2026-08-12) — Simulator Library COMPLETE, 87 total:**
- ✅ Bio +6 (meiosis, natural selection, population growth, enzyme kinetics, respiration map, food-chain pyramid) → **Bio hits 17/17 from the list**
- ✅ Chem +2 (Equilibrium & Le Chatelier — Haber / NO₂ tube / esterification presets; Virtual Chemistry Bench with real reaction matrix)
- ✅ Physics +7 (free fall, friction, plane-mirror reflection, resistor colour code, RC charge/discharge, transformer, energy-conservation track)
- ✅ Maths +5 (matrix 2×2 live plane-transform, complex Argand plane, coordinate geometry, sequences & series, projectile parametric)
- ✅ ICT +5 (offline SQL playground engine, flowchart tracer, Boolean algebra lab, memory/storage units, program step visualizer)
- ✅ Physics lesson auto-rules: "free fall" → freefall, "capacit" / "time constant" → rc, "transformer" → transformer
- ✅ eZ Cash payments (r2): Premium page method tabs (🏦 slip / 📱 eZ Cash), admin-settable eZ Cash number
  (Site → 💎 section), Transaction-ID + mobile submit → pending; unique-txn & mobile validation, 3-pending cap;
  admin Approve/Reject on the same Payments tab (method shown as 📱 eZ Cash chip with txn + mobile)
- ✅ Every new sim: 🎖️ challenges (+15/+2 XP), 🤖 Ask-AI context, 5-question MCQ bank, lab/CSV table support
- ⏳ Still queued from the spec: weekly sim leaderboard screen, per-language challenge text,
  AI-daily-challenge generator, mobile fullscreen pass

## v2026.08.12s — Chemistry Virtual Practical Laboratory
- New sim type `chemlab` (subject chem, difficulty hard) — 12 database-driven practicals in one engine (sims-chemlab.js).
- New tables: `lab_notes (user_id, prac, data JSON, PK user+prac)` · `lab_progress (user_id, prac, best, done, PK user+prac)` — mirrored in db.js (Node mode).
- New APIs: `GET /api/chemdb` (public teacher profiles) · `POST /api/admin/chemdb` {kind: flame|precip, ...validated, true-colour hex enforced, max 60} · `POST /api/admin/chemdb/del` {idx} · `GET /api/lab/state` · `POST /api/lab/note` {prac, data{8 fields, 2000 chars each}} · `POST /api/lab/progress` {prac, score 0-100, done} (best=MAX).
- Teacher profiles persist in site_settings key `chemdb_extra` (JSON list) and merge into the flame/precipitation shelves at mount.
- Admin UI: ⚙️ Site → 🧪 Chem lab database (list + delete + two add forms).

## v2026.08.12t — Offline syllabus Guru + chem-lab polish
- `offline_kb.json` (root) — shared syllabus knowledge bank loaded by server.js.
- `/api/ai/chat`: no key → offline match reply (`engine:'offline'`, no quota burn); Gemini HTTP/network failure → `engine:'offline_fallback'` answer instead of 502; success → `engine:'gemini'`. Gemini failures logged as `ai_gemini_err` in admin logs.
- admin lore (ai_knowledge) is also searched by the offline matcher.
- Chem lab: NaBr/NaI added (cream AgBr, yellow AgI + NH₃ follow-ups); fixed flame sample log + cell right-electrode chip state.
