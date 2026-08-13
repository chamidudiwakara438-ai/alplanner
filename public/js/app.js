/* AL Planner SPA — hash router, all views */
(function () {
  const $ = (s, r = document) => r.querySelector(s);
  const app = $('#app');
  let deferredPrompt = null;

  function esc(s) {
    return String(s == null ? '' : s).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
  }
  function toast(msg) {
    const t = document.createElement('div');
    t.className = 'toast'; t.textContent = msg;
    document.body.appendChild(t);
    setTimeout(() => t.remove(), 2400);
  }
  function hash() {
    const h = (location.hash || '#/').replace(/^#/, '');
    const [path, qs] = h.split('?');
    const parts = path.split('/').filter(Boolean);
    const q = {};
    new URLSearchParams(qs || '').forEach((v, k) => { q[k] = v; });
    return { parts, q, path: '/' + parts.join('/') };
  }
  function go(p) { location.hash = p; }

  function navHTML() {
    const u = Store.user;
    const items = [
      ['/', 'nav.home'], ['/subjects', 'nav.subjects'], ['/lab', 'nav.lab'],
      ['/practicals', 'nav.practicals'], ['/resources', 'nav.resources'],
      ['/tutors', 'nav.tutors'], ['/planner', 'nav.planner'],
      ['/exam', 'nav.exam'], ['/board', 'nav.board'],
    ];
    if (u) items.push(['/dashboard', 'nav.dashboard']);
    if (u && u.role === 'admin') items.push(['/admin', 'nav.admin']);
    return items.map(([href, k]) => `<a href="#${href}" data-i="${k}">${t(k)}</a>`).join('');
  }
  function authSlot() {
    const u = Store.user;
    if (u) return `<span class="muted">${esc(u.name.split(' ')[0])}</span> <button class="ghost" id="btn-out">${t('nav.logout')}</button>`;
    return `<a class="ghost" href="#/login">${t('nav.login')}</a> <a class="btn" href="#/register">${t('nav.register')}</a>`;
  }
  function tabbar() {
    const u = Store.user;
    const items = [['/', '🏠', 'nav.home'], ['/subjects', '📚', 'nav.subjects'], ['/lab', '🧪', 'nav.lab'], ['/exam', '🎯', 'nav.exam']];
    items.push([u ? '/dashboard' : '/login', '👤', u ? 'nav.dashboard' : 'nav.login']);
    return items.map(([h, ic, k]) => `<a href="#${h}">${ic}<br>${t(k)}</a>`).join('');
  }
  function paintChrome() {
    $('#nav-main').innerHTML = navHTML();
    $('#auth-slot').innerHTML = authSlot();
    $('#tabbar').innerHTML = tabbar();
    const out = $('#btn-out');
    if (out) out.onclick = async () => { await Store.logout(); toast('Signed out'); render(); };
    const pill = document.getElementById('cloud-pill');
    if (pill) {
      pill.textContent = Store.cloud ? 'Firebase' : 'This browser';
      pill.style.background = Store.cloud ? '#059669' : '#64748b';
    }
    applyI18n();
    const { path } = hash();
    document.querySelectorAll('.nav-main a, .tabbar a').forEach((a) => {
      const href = (a.getAttribute('href') || '').replace('#', '');
      if (href === path || (href !== '/' && path.startsWith(href))) a.classList.add('on');
    });
    tickCountdown();
  }
  function tickCountdown() {
    const el = $('#nav-countdown');
    const st = Store.settings();
    if (!st.exam_date) { el.hidden = true; return; }
    const left = new Date(st.exam_date + 'T00:00:00') - Date.now();
    el.hidden = false;
    if (left <= 0) { el.textContent = 'A/L day!'; return; }
    const d = Math.floor(left / 864e5), h = Math.floor((left % 864e5) / 36e5), m = Math.floor((left % 36e5) / 6e4);
    el.textContent = d + 'd ' + h + 'h ' + m + 'm';
  }

  function subjectCard(s) {
    const n = Store.lessons.filter((l) => l.subject_id === s.id).length;
    const u = Store.unitsOf(s.id).length;
    return `<a class="card sub-card tilt" href="#/subject/${s.id}" style="--c:${s.color1}">
      <div class="badge">${esc(s.code)}</div>
      <h3>${esc(s.icon)} ${esc(s.name)}</h3>
      <div class="muted">${esc(s.name_si)} · ${esc(s.name_ta)}</div>
      <p>${u} units · ${n} lessons</p>
    </a>`;
  }

  function viewHome() {
    const st = Store.stats();
    app.innerHTML = `
      <section class="hero">
        <div>
          <h1 data-i="home.h">${t('home.h')}</h1>
          <p class="lead" data-i="home.lead">${t('home.lead')}</p>
          <div class="row">
            <a class="btn" href="#/${Store.user ? 'dashboard' : 'register'}" data-i="home.cta">${t('home.cta')}</a>
            <a class="ghost" href="#/subjects" data-i="home.browse">${t('home.browse')}</a>
          </div>
        </div>
        <div class="hero-art" id="hero-art">
          <span class="chip" style="top:18%;left:10%">⚗️ Chemistry</span>
          <span class="chip" style="top:28%;right:12%">∑ Combined Maths</span>
          <span class="chip" style="bottom:28%;left:18%">⚛️ Physics</span>
          <span class="chip" style="bottom:16%;right:16%">🧬 Biology</span>
        </div>
      </section>
      <div class="grid g4">
        <div class="card"><div class="stat">${st.lessons}</div><div class="muted">Lessons</div></div>
        <div class="card"><div class="stat">${st.videos}</div><div class="muted">Videos</div></div>
        <div class="card"><div class="stat">${st.units}</div><div class="muted">Units</div></div>
        <div class="card"><div class="stat">${st.subjects}</div><div class="muted">Subjects</div></div>
      </div>
      <h2 style="margin-top:32px">Subjects</h2>
      <div class="grid g3">${Store.subjects.map(subjectCard).join('')}</div>
      <h2>Latest videos</h2>
      <div class="grid g3">${Store.lessons.filter((l) => l.youtube_id).slice(0, 6).map((l) =>
        `<a class="card" href="#/lesson/${l.id}"><strong>${esc(l.title)}</strong><p class="muted">${esc(l.teacher_name || l.unit_name)}</p></a>`
      ).join('')}</div>`;
    tilt($('#hero-art'));
  }

  function viewSubjects() {
    app.innerHTML = `<h1 data-i="nav.subjects">${t('nav.subjects')}</h1>
      <input class="search" id="q" placeholder="Search lessons, units, teachers…" />
      <div id="sr"></div>
      <div class="grid g3" style="margin-top:16px">${Store.subjects.map(subjectCard).join('')}</div>`;
    $('#q').oninput = () => {
      const r = Store.search($('#q').value);
      if (!$('#q').value.trim()) { $('#sr').innerHTML = ''; return; }
      $('#sr').innerHTML = `<div class="card">${r.lessons.map((l) =>
        `<div class="lesson"><a href="#/lesson/${l.id}">${esc(l.title)}</a><span class="muted">${esc(l.teacher_name)}</span></div>`
      ).join('') || '<p class="muted">No matches</p>'}</div>`;
    };
  }

  function viewSubject(id) {
    const s = Store.subjectById(id);
    if (!s) return viewNotFound();
    const units = Store.unitsOf(s.id);
    app.innerHTML = `<p><a href="#/subjects">← Subjects</a></p>
      <h1>${esc(s.icon)} ${esc(s.name)}</h1>
      <p class="muted">${esc(s.name_si)} · ${esc(s.name_ta)}</p>
      ${units.map((u) => {
        const ls = Store.lessonsOfUnit(u.id);
        return `<div class="unit card"><h3>${esc(u.name)} <span class="badge">${ls.length}</span></h3>
          ${ls.map((l) => {
            const st = Store.stateOf(l.id);
            return `<div class="lesson">
              <div><a href="#/lesson/${l.id}"><strong>${esc(l.title)}</strong></a>
              <div class="muted">${esc(l.teacher_name || '')}</div></div>
              <div>${st.completed ? '✅' : ''}${st.watched ? ' ▶' : ''}${l.youtube_id ? '' : ' <span class="badge">notes</span>'}</div>
            </div>`;
          }).join('') || '<p class="muted">Lessons coming soon.</p>'}</div>`;
      }).join('')}`;
  }

  function viewLesson(id) {
    const l = Store.lessonById(id);
    if (!l) return viewNotFound();
    const st = Store.stateOf(l.id);
    const sub = Store.subjectById(l.subject_id);
    const rel = Store.related(l);
    const embed = l.youtube_id
      ? `<iframe class="yt" src="https://www.youtube-nocookie.com/embed/${esc(l.youtube_id)}?rel=0" allowfullscreen allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"></iframe>`
      : `<div class="card">No video attached yet — read the notes below.</div>`;
    app.innerHTML = `<p><a href="#/subject/${l.subject_id}">← ${esc(sub ? sub.name : 'Subject')}</a> · ${esc(l.unit_name)}</p>
      <h1>${esc(l.title)}</h1>
      <p class="muted">${esc(l.teacher_name)} ${l.description ? '· ' + esc(l.description) : ''}</p>
      ${embed}
      <div class="row" style="margin:14px 0">
        <button class="ghost" data-f="watched">${t('lesson.watch')}${st.watched ? ' ✓' : ''}</button>
        <button class="ghost" data-f="completed">${t('lesson.done')}${st.completed ? ' ✓' : ''}</button>
        <button class="ghost" data-f="favourite">${t('lesson.fav')}${st.favourite ? ' ★' : ''}</button>
        <button class="btn" id="add-plan">+ Planner</button>
      </div>
      ${l.notes ? `<div class="card note">${esc(l.notes)}</div>` : ''}
      <h3>Related labs</h3>
      <div class="row">${Store.sims.filter((s) => {
        const map = { 1: 'chem', 2: 'maths', 3: 'bio', 4: 'phys', 5: 'ict' };
        return s.subject === map[l.subject_id];
      }).slice(0, 4).map((s) => `<a class="ghost" href="#/sim/${s.type}">${esc(s.title)}</a>`).join('')}</div>
      <h3>Related</h3>
      <div class="grid g3">${rel.map((x) => `<a class="card" href="#/lesson/${x.id}">${esc(x.title)}</a>`).join('')}</div>`;
    app.querySelectorAll('[data-f]').forEach((b) => {
      b.onclick = async () => {
        try { await Store.toggle(l.id, b.getAttribute('data-f')); viewLesson(id); }
        catch (e) { toast(e.message); go('/login'); }
      };
    });
    $('#add-plan').onclick = async () => {
      try {
        await Store.addPlan(l.id, new Date().toISOString().slice(0, 10));
        toast('Added to today\'s plan');
      } catch (e) { toast(e.message); go('/login'); }
    };
  }

  function formAuth(kind) {
    const reg = kind === 'register';
    app.innerHTML = `<div class="card" style="max-width:460px;margin:20px auto">
      <h1>${reg ? t('nav.register') : t('nav.login')}</h1>
      <form id="af">
        ${reg ? `<label class="field">${t('auth.name')}<input name="name" required></label>` : ''}
        <label class="field">${t('auth.email')}<input name="email" type="email" required></label>
        <label class="field">${t('auth.pass')}<input name="password" type="password" required minlength="6"></label>
        ${reg ? `
          <label class="field">${t('auth.school')}<input name="school"></label>
          <label class="field">${t('auth.district')}<select name="district">${Store.districts.map((d) => `<option>${esc(d)}</option>`).join('')}</select></label>
          <label class="field">${t('auth.year')}<select name="al_year">${Store.years.map((y) => `<option>${esc(y)}</option>`).join('')}</select></label>
          <label class="field">${t('auth.stream')}<select name="stream">${Store.streams.map((s) => `<option>${esc(s)}</option>`).join('')}</select></label>
          <label class="field">${t('auth.medium')}<select name="medium"><option value="en">English</option><option value="si">සිංහල</option><option value="ta">தமிழ்</option></select></label>
        ` : ''}
        <p id="err" class="muted" style="color:#b91c1c"></p>
        <button class="btn" type="submit">${t('auth.go')}</button>
      </form>
      <p class="muted">${reg ? 'Already have an account?' : 'New here?'} <a href="#/${reg ? 'login' : 'register'}">${reg ? t('nav.login') : t('nav.register')}</a></p>
    </div>`;
    $('#af').onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target));
      try {
        if (reg) await Store.register(fd);
        else await Store.login(fd.email, fd.password);
        toast('Welcome' + (Store.user.role === 'admin' ? ' — you are admin' : ''));
        go('/dashboard');
      } catch (err) { $('#err').textContent = err.message; }
    };
  }

  function viewDash() {
    if (!Store.user) return go('/login');
    const d = Store.dash();
    const st = Store.settings();
    const xp = Store.xp();
    const leftMs = new Date(st.exam_date + 'T00:00:00') - Date.now();
    const left = Math.max(0, Math.ceil(leftMs / 864e5));
    app.innerHTML = `<h1>${t('dash.hi')}, ${esc(Store.user.name.split(' ')[0])}</h1>
      <p class="muted">${Store.user.school || ''} · ${Store.user.al_year || ''} · ${Store.user.district || ''}</p>
      <div class="grid g4">
        <div class="card"><div class="stat" id="live-cd">${left}d</div><div class="muted">${t('dash.left')}</div></div>
        <div class="card"><div class="stat">${d.completed.length}</div><div class="muted">${t('dash.done')}</div></div>
        <div class="card"><div class="stat">${xp.total}</div><div class="muted">XP</div></div>
        <div class="card"><div class="stat">${d.favourites.length}</div><div class="muted">Favourites</div></div>
      </div>
      <h3>Badges</h3>
      <div class="row">${xp.badges.map((b) => `<span class="chip-static ${b.ok ? '' : 'dim'}">${b.ic} ${esc(b.name)}</span>`).join('')}</div>
      <h3>Progress</h3>
      ${d.subjects.map((s) => {
        const pct = s.total ? Math.round(100 * s.completed / s.total) : 0;
        return `<div class="card" style="margin:8px 0"><div class="row"><strong>${esc(s.name)}</strong><span class="muted">${s.completed}/${s.total}</span></div>
          <div class="progress"><i style="width:${pct}%"></i></div></div>`;
      }).join('')}
      <h3>Continue</h3>
      <div class="grid g2">${d.watched.slice(0, 4).map((l) => `<a class="card" href="#/lesson/${l.id}">${esc(l.title)}</a>`).join('') || '<p class="muted">Watch a lesson to see it here.</p>'}</div>
      <p><a class="ghost" href="#/settings">Exam date & goals</a> · <a class="ghost" href="#/exam">Exam mode</a> · <a class="ghost" href="#/premium">${t('nav.premium')}</a></p>`;
    const cd = $('#live-cd');
    if (cd && leftMs > 0) {
      const tick = () => {
        const ms = new Date(st.exam_date + 'T00:00:00') - Date.now();
        if (ms <= 0) { cd.textContent = 'Go shine!'; return; }
        const d0 = Math.floor(ms / 864e5), h = Math.floor((ms % 864e5) / 36e5), m = Math.floor((ms % 36e5) / 6e4), s = Math.floor((ms % 6e4) / 1000);
        cd.textContent = d0 + 'd ' + h + 'h ' + m + 'm ' + s + 's';
      };
      tick();
      const iv = setInterval(tick, 1000);
      setTimeout(() => clearInterval(iv), 120000);
    }
  }

  function viewLab() {
    app.innerHTML = `<h1 data-i="lab.title">${t('lab.title')}</h1>
      <div class="tabs" id="ltabs">
        <button data-s="" class="on">All</button>
        <button data-s="chem">Chem</button><button data-s="phys">Physics</button>
        <button data-s="maths">Maths</button><button data-s="ict">ICT</button>
      </div>
      <div class="grid g3" id="lgrid"></div>`;
    const draw = (s) => {
      $('#lgrid').innerHTML = Store.sims.filter((x) => !s || x.subject === s).map((sim) =>
        `<a class="card" href="#/sim/${sim.type}"><strong>${esc(sim.title)}</strong><p class="muted">${esc(sim.descr)}</p><span class="badge">+${sim.xp} XP</span></a>`
      ).join('');
    };
    draw('');
    $('#ltabs').onclick = (e) => {
      const b = e.target.closest('button'); if (!b) return;
      $('#ltabs').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
      draw(b.getAttribute('data-s'));
    };
  }
  function viewSim(type) {
    const sim = Store.sims.find((s) => s.type === type);
    app.innerHTML = `<p><a href="#/lab">← Lab</a></p><h1>${esc(sim ? sim.title : type)}</h1>
      <p class="muted">${esc(sim ? sim.descr : '')}</p><div id="stage"></div>`;
    Sims.mount($('#stage'), type);
  }

  function viewPracticals() {
    app.innerHTML = `<h1 data-i="prac.title">${t('prac.title')}</h1>
      <div class="tabs" id="ptabs">
        <button data-s="" class="on">All</button>
        <button data-s="Physics">Physics</button>
        <button data-s="Chemistry">Chemistry</button>
        <button data-s="Biology">Biology</button>
      </div>
      <div class="grid g2" id="pgrid"></div>`;
    const draw = (s) => {
      $('#pgrid').innerHTML = Store.practicals.filter((p) => !s || p.subject === s).map((p) =>
        `<a class="card" href="#/practical/${p.id}"><span class="badge">${esc(p.subject)}</span>
          <h3>${esc(p.en)}</h3><p class="muted">${esc(p.si)} · ${esc(p.category)}</p></a>`
      ).join('');
    };
    draw('');
    $('#ptabs').onclick = (e) => {
      const b = e.target.closest('button'); if (!b) return;
      $('#ptabs').querySelectorAll('button').forEach((x) => x.classList.toggle('on', x === b));
      draw(b.getAttribute('data-s'));
    };
  }
  function viewPractical(id) {
    const p = Store.practicals.find((x) => x.id === +id);
    if (!p) return viewNotFound();
    app.innerHTML = `<p><a href="#/practicals">← Practicals</a></p>
      <h1>${esc(p.en)}</h1><p class="muted">${esc(p.si)} · ${esc(p.subject)} · ${esc(p.category)}</p>
      <div class="card"><h3>Objective</h3><p>${esc(p.obj)}</p></div>
      <div class="card"><h3>Theory</h3><p>${esc(p.theory)}</p></div>
      <div class="card"><h3>Procedure</h3><p class="note">${esc(p.proc)}</p></div>
      <div class="card"><h3>Formula</h3><p><code>${esc(p.formula)}</code></p></div>
      <div class="card"><h3>Viva</h3><ul>${(p.viva || []).map((q) => `<li>${esc(q)}</li>`).join('')}</ul></div>`;
  }

  function viewResources() {
    const list = Store.resources();
    app.innerHTML = `<h1 data-i="nav.resources">${t('nav.resources')}</h1>
      ${Store.user ? `<form id="rf" class="card"><div class="row">
        <input name="title" placeholder="Title" required style="flex:1;padding:8px;border:1px solid var(--line);border-radius:10px">
        <select name="category"><option value="notes">Notes</option><option value="past_papers">Past papers</option><option value="question_papers">Questions</option></select>
        <select name="subject_id">${Store.subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select>
        <button class="btn">Upload listing</button></div>
        <p class="muted">Files stay on your device in this Netlify build (listing only).</p></form>` : '<p><a href="#/login">Sign in</a> to add resources.</p>'}
      <div class="grid g2">${list.map((r) => {
        const s = Store.subjectById(r.subject_id);
        return `<div class="card"><strong>${esc(r.title)}</strong><p class="muted">${esc(r.category)} · ${esc(s ? s.name : '')} · ${esc(r.status)}</p></div>`;
      }).join('')}</div>`;
    const f = $('#rf');
    if (f) f.onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(f));
      await Store.addResource(fd.title, fd.category, fd.subject_id);
      toast('Saved'); viewResources();
    };
  }

  function viewTutors() {
    app.innerHTML = `<h1 data-i="nav.tutors">${t('nav.tutors')}</h1>
      <div class="grid g2">${Store.tutors.map((t0) =>
        `<div class="card"><h3>${esc(t0.name)}</h3>
          <p>${esc(t0.subjects.join(', '))} · ${esc(t0.exp)}</p>
          <p class="muted">${esc(t0.loc)} · ${esc(t0.phone)}</p>
          <p>${esc(t0.bio)}</p>
          <a class="btn" href="https://wa.me/94${t0.phone.replace(/\D/g, '').slice(-9)}" target="_blank" rel="noopener">WhatsApp</a>
        </div>`
      ).join('')}</div>`;
  }

  function viewPlanner() {
    if (!Store.user) return go('/login');
    const plans = Store.plans();
    const today = new Date().toISOString().slice(0, 10);
    app.innerHTML = `<h1 data-i="nav.planner">${t('nav.planner')}</h1>
      <div class="card">
        <h3>Smart weekly timetable</h3>
        <p class="muted">Weak subject gets extra slots + lab + exam + AI day.</p>
        <div class="row">
          <select id="weak">${Store.subjects.map((s) => `<option value="${s.id}">${esc(s.name)}</option>`).join('')}</select>
          <button class="btn" id="gen">Generate week</button>
          <button class="ghost" id="pr">Print</button>
        </div>
        <div id="week"></div>
      </div>
      <h3>My list · ${today}</h3>
      ${plans.map((p) => {
        const l = Store.lessonById(p.lesson_id);
        return `<div class="lesson"><div><strong>${esc(l ? l.title : 'Lesson')}</strong><div class="muted">${esc(p.plan_date)}</div></div>
          <div><button class="ghost" data-t="${p.id}">${p.done ? 'Undo' : 'Done'}</button>
          <button class="danger" data-d="${p.id}">✕</button></div></div>`;
      }).join('') || '<p class="empty">No planned lessons yet. Open a lesson and tap + Planner.</p>'}`;
    $('#gen').onclick = () => {
      const slots = Store.weekPlan($('#weak').value);
      $('#week').innerHTML = `<div class="week">${slots.map((d) =>
        `<div class="card"><strong>${esc(d.day)}</strong>${d.items.map((it) =>
          `<div><a href="${it.href}"><span class="badge">${esc(it.kind)}</span> ${esc(it.title)}</a></div>`).join('')}</div>`
      ).join('')}</div>`;
    };
    $('#pr').onclick = () => window.print();
    app.querySelectorAll('[data-t]').forEach((b) => { b.onclick = async () => { await Store.togglePlan(b.getAttribute('data-t')); viewPlanner(); }; });
    app.querySelectorAll('[data-d]').forEach((b) => { b.onclick = async () => { await Store.delPlan(b.getAttribute('data-d')); viewPlanner(); }; });
  }

  function viewExam() {
    if (!Store.user) return go('/login');
    const hist = Store.examHistory();
    app.innerHTML = `<h1>🎯 Exam mode</h1>
      <p class="muted">Timed MCQs from the A/L bank. Auto-marked.</p>
      <form id="ef" class="card row">
        <select name="subj">
          <option value="mixed">Mixed</option>
          <option value="chem">Chemistry</option>
          <option value="phys">Physics</option>
          <option value="cm">Combined Maths</option>
          <option value="bio">Biology</option>
          <option value="ict">ICT</option>
        </select>
        <select name="n"><option>10</option><option>15</option><option>20</option></select>
        <button class="btn">Start</button>
      </form>
      <div id="epaper"></div>
      <h3>History</h3>
      ${hist.slice(-8).reverse().map((h) => `<div class="lesson"><span>${esc(h.subj)} · ${h.score}/${h.total}</span><span class="muted">${esc((h.at || '').slice(0, 16))}</span></div>`).join('') || '<p class="muted">No attempts yet.</p>'}`;
    $('#ef').onsubmit = (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(e.target));
      const qs = CONTENT.pickExam(fd.subj, +fd.n);
      const t0 = Date.now();
      $('#epaper').innerHTML = `<form id="qz" class="card">${qs.map((q, i) =>
        `<fieldset class="q"><legend>Q${i + 1}. ${esc(q.q)}</legend>
          ${q.opts.map((o) => `<label><input type="radio" name="q${i}" value="${o.k}"> ${esc(o.t)}</label>`).join('')}</fieldset>`
      ).join('')}<button class="btn">Submit</button></form>`;
      $('#qz').onsubmit = async (ev) => {
        ev.preventDefault();
        let score = 0;
        qs.forEach((q, i) => {
          const pick = ($('#qz')['q' + i] && $('#qz')['q' + i].value) || '';
          if (pick === q.ans) score++;
        });
        await Store.saveExam({ subj: fd.subj, score, total: qs.length, seconds: Math.round((Date.now() - t0) / 1000) });
        toast(score + ' / ' + qs.length);
        viewExam();
      };
    };
  }

  function viewBoard() {
    const rows = Store.board();
    app.innerHTML = `<h1>🏆 Leaderboard</h1>
      <p class="muted">XP from completed lessons + exam scores.</p>
      <table class="table"><tr><th>#</th><th>Name</th><th>School</th><th>Lessons</th><th>XP</th></tr>
        ${rows.map((r, i) => `<tr class="${r.me ? 'me' : ''}"><td>${i + 1}</td><td>${esc(r.name)}</td><td>${esc(r.school)}</td><td>${r.done}</td><td>${r.pts}</td></tr>`).join('') || '<tr><td colspan="5">Be the first — complete a lesson or exam.</td></tr>'}
      </table>`;
  }

  function viewSettings() {
    if (!Store.user) return go('/login');
    const st = Store.settings();
    app.innerHTML = `<h1>Settings</h1>
      <form id="sf" class="card" style="max-width:420px">
        <label class="field">Exam date<input type="date" name="exam_date" value="${esc(st.exam_date)}"></label>
        <label class="field">Weekly lesson target<input type="number" name="weekly_target" value="${esc(st.weekly_target)}" min="1" max="100"></label>
        <button class="btn">Save</button>
      </form>`;
    $('#sf').onsubmit = async (e) => {
      e.preventDefault();
      await Store.setSettings(Object.fromEntries(new FormData(e.target)));
      toast('Saved'); tickCountdown();
    };
  }

  function viewPremium() {
    app.innerHTML = `<h1>💎 Premium</h1>
      <div class="card"><p>Unlock higher AI limits and premium sims. Pay by bank slip or eZ Cash — admin approves.</p>
        <p><strong>Rs. 990 / 31 days</strong></p>
        ${Store.user ? `<form id="pf" class="row">
          <select name="method"><option value="slip">Bank slip</option><option value="ezcash">eZ Cash</option></select>
          <input name="note" placeholder="Txn ID / note" required>
          <button class="btn">Submit payment</button>
        </form>` : '<a class="btn" href="#/login">Sign in to upgrade</a>'}
      </div>`;
    const f = $('#pf');
    if (f) f.onsubmit = async (e) => {
      e.preventDefault();
      const fd = Object.fromEntries(new FormData(f));
      await Store.pay(fd.method, fd.note);
      toast('Sent for approval');
    };
  }

  function viewAdmin() {
    if (!Store.user || Store.user.role !== 'admin') return go('/');
    const users = Store.users();
    const pays = Store.payments();
    const st = Store.stats();
    app.innerHTML = `<h1>Admin</h1>
      <div class="grid g4">
        <div class="card"><div class="stat">${st.students}</div><div class="muted">Students</div></div>
        <div class="card"><div class="stat">${st.lessons}</div><div class="muted">Lessons</div></div>
        <div class="card"><div class="stat">${pays.filter((p) => p.status === 'pending').length}</div><div class="muted">Pending pay</div></div>
        <div class="card"><div class="stat">${st.videos}</div><div class="muted">Videos</div></div>
      </div>
      <h3>Students</h3>
      <table class="table"><tr><th>Name</th><th>Email</th><th>Role</th><th></th></tr>
        ${users.map((u) => `<tr><td>${esc(u.name)}</td><td>${esc(u.email)}</td><td>${esc(u.role)}</td>
          <td><button class="ghost" data-role="${u.id}" data-v="${u.role === 'admin' ? 'student' : 'admin'}">Make ${u.role === 'admin' ? 'student' : 'admin'}</button></td></tr>`).join('')}
      </table>
      <h3>Payments</h3>
      ${pays.map((p) => `<div class="lesson"><div>${esc(p.name)} · ${esc(p.method)} · ${esc(p.note)} · Rs.${p.amount}
        <span class="badge">${esc(p.status)}</span></div>
        ${p.status === 'pending' ? `<div><button class="btn" data-ok="${p.id}">Approve</button> <button class="danger" data-no="${p.id}">Reject</button></div>` : ''}</div>`).join('') || '<p class="muted">No payments yet.</p>'}`;
    app.querySelectorAll('[data-role]').forEach((b) => {
      b.onclick = () => { Store.setRole(b.getAttribute('data-role'), b.getAttribute('data-v')); viewAdmin(); };
    });
    app.querySelectorAll('[data-ok]').forEach((b) => { b.onclick = () => { Store.decidePay(b.getAttribute('data-ok'), true); viewAdmin(); }; });
    app.querySelectorAll('[data-no]').forEach((b) => { b.onclick = () => { Store.decidePay(b.getAttribute('data-no'), false); viewAdmin(); }; });
  }

  function viewNotFound() { app.innerHTML = `<div class="empty"><h2>Not found</h2><a href="#/">Go home</a></div>`; }

  function tilt(el) {
    if (!el || matchMedia('(pointer:coarse)').matches || matchMedia('(prefers-reduced-motion:reduce)').matches) return;
    el.onmousemove = (e) => {
      const r = el.getBoundingClientRect();
      const x = (e.clientX - r.left) / r.width - 0.5;
      const y = (e.clientY - r.top) / r.height - 0.5;
      el.style.transform = `rotateY(${x * 10}deg) rotateX(${-y * 10}deg)`;
    };
    el.onmouseleave = () => { el.style.transform = ''; };
  }

  function route() {
    paintChrome();
    const { parts } = hash();
    const a = parts[0] || '';
    const b = parts[1];
    if (!a) return viewHome();
    if (a === 'subjects') return viewSubjects();
    if (a === 'subject' && b) return viewSubject(b);
    if (a === 'lesson' && b) return viewLesson(b);
    if (a === 'login') return formAuth('login');
    if (a === 'register') return formAuth('register');
    if (a === 'dashboard') return viewDash();
    if (a === 'lab') return viewLab();
    if (a === 'sim' && b) return viewSim(b);
    if (a === 'practicals') return viewPracticals();
    if (a === 'practical' && b) return viewPractical(b);
    if (a === 'resources') return viewResources();
    if (a === 'tutors') return viewTutors();
    if (a === 'planner') return viewPlanner();
    if (a === 'exam') return viewExam();
    if (a === 'board') return viewBoard();
    if (a === 'settings') return viewSettings();
    if (a === 'premium') return viewPremium();
    if (a === 'admin') return viewAdmin();
    viewNotFound();
  }

  function bindAI() {
    const sheet = $('#ai-sheet'), log = $('#ai-log');
    $('#ai-fab').onclick = () => { sheet.hidden = !sheet.hidden; };
    $('#ai-close').onclick = () => { sheet.hidden = true; };
    $('#foot-ai').onclick = (e) => { e.preventDefault(); sheet.hidden = false; };
    $('#ai-form').onsubmit = (e) => {
      e.preventDefault();
      const q = $('#ai-input').value.trim();
      if (!q) return;
      $('#ai-input').value = '';
      log.insertAdjacentHTML('beforeend', `<div class="ai-msg user">${esc(q)}</div>`);
      const ans = Store.offlineAnswer(q);
      log.insertAdjacentHTML('beforeend', `<div class="ai-msg bot">${esc(ans)}</div>`);
      log.scrollTop = log.scrollHeight;
    };
  }

  function halo() {
    const h = $('#cursor-halo');
    if (matchMedia('(pointer:coarse)').matches || matchMedia('(prefers-reduced-motion:reduce)').matches) return;
    h.hidden = false;
    let x = 0, y = 0, tx = 0, ty = 0;
    window.addEventListener('mousemove', (e) => { tx = e.clientX; ty = e.clientY; });
    const tick = () => { x += (tx - x) * 0.2; y += (ty - y) * 0.2; h.style.left = x + 'px'; h.style.top = y + 'px'; requestAnimationFrame(tick); };
    tick();
  }

  async function render() { route(); }

  window.addEventListener('hashchange', render);
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault(); deferredPrompt = e;
    const b = $('#install-btn');
    b.hidden = false;
    b.onclick = () => deferredPrompt && deferredPrompt.prompt();
    $('#foot-install').onclick = (ev) => { ev.preventDefault(); if (deferredPrompt) deferredPrompt.prompt(); else toast('Use the browser Install icon'); };
  });
  $('#lang-btn').onclick = () => {
    const cur = localStorage.getItem('al_lang') || 'en';
    const next = cur === 'en' ? 'si' : cur === 'si' ? 'ta' : 'en';
    localStorage.setItem('al_lang', next);
    applyI18n(); render();
  };
  setInterval(tickCountdown, 30000);

  Store.init().then(() => {
    bindAI(); halo(); render();
    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('/sw.js').catch(() => {});
    }
  }).catch((e) => {
    app.innerHTML = `<div class="card"><h2>Could not load lesson data</h2><p>${esc(e.message)}</p>
      <p class="muted">Open this site via Netlify (or a local static server), not as a raw file.</p></div>`;
  });
})();
