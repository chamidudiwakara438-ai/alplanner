/* Client-side store — no Python / no SQLite. Persists in localStorage. */
(function () {
  const KEY = 'alplanner-v1';
  const DISTRICTS = ['Ampara','Anuradhapura','Badulla','Batticaloa','Colombo','Galle','Gampaha','Hambantota','Jaffna','Kalutara','Kandy','Kegalle','Kilinochchi','Kurunegala','Mannar','Matale','Matara','Monaragala','Mullaitivu','Nuwara Eliya','Polonnaruwa','Puttalam','Ratnapura','Trincomalee','Vavuniya'];
  const STREAMS = ['Physical Science','Biological Science','Commerce','Arts','Engineering Technology','Bio Systems Technology'];
  const YEARS = ['A/L 2027','A/L 2028','A/L 2029'];

  const SUBJECTS = [
    { id: 1, name: 'Chemistry', name_si: 'රසායන විද්‍යාව', name_ta: 'வேதியியல்', code: 'CHEM', icon: '⚗️', color1: '#8b5cf6', color2: '#22d3ee' },
    { id: 2, name: 'Combined Mathematics', name_si: 'සංයුක්ත ගණිතය', name_ta: 'இணை கணிதம்', code: 'CM', icon: '∑', color1: '#6366f1', color2: '#ec4899' },
    { id: 3, name: 'Biology', name_si: 'ජීව විද්‍යාව', name_ta: 'உயிரியல்', code: 'BIO', icon: '🧬', color1: '#22c55e', color2: '#a3e635' },
    { id: 4, name: 'Physics', name_si: 'භෞතික විද්‍යාව', name_ta: 'இயற்பியல்', code: 'PHY', icon: '⚛️', color1: '#f97316', color2: '#e11d48' },
    { id: 5, name: 'ICT', name_si: 'තොරතුරු තාක්ෂණය', name_ta: 'தகவல் தொழில்நுட்பம்', code: 'ICT', icon: '💻', color1: '#06b6d4', color2: '#3b82f6' },
  ];
  const CHEM_UNITS = ['Atomic Structure','Chemical Bonding','Chemical Calculations','Matter and Its Properties','Energetics','Inorganic Chemistry','Organic Chemistry','Chemical Kinetics','Chemical Equilibrium','Electrochemistry','Industrial Chemistry'];
  const CM_UNITS = [
    'Real Numbers, Functions & Inequalities','Quadratics & Polynomials','Indices, Logarithms & Rational Functions','Binomial Expansion','Series, Induction & Notations','Trigonometry','Limits & Continuity','Differentiation & Applications','Integration & Applications','Complex Numbers','Matrices','Straight Line & Circle','Permutations & Combinations','Probability & Statistics','Vectors','Forces, Equilibrium & Friction','Motion: Straight Line, Relative & Projectiles','Work, Energy, Power, Impulse & Collision','Circular Motion, SHM & Centre of Mass',
  ];
  const BIO_UNITS = ['Molecular & Cellular Biology','Plant & Animal Systems'];
  const PHY_UNITS = ['Measurement','Mechanics','Oscillations and Waves','Thermal Physics','Gravitational Field','Electrostatic Field','Magnetic Field','Current Electricity','Electronics','Mechanical Properties of Matter','Matter and Radiation'];
  const ICT_UNITS = ['Concept of ICT','Introduction to Computer','Data Representation','Fundamentals of Digital Circuits','Computer Operating Systems','Data Communication and Networking','System Analysis and Design','Database Management','Programming','Web Development','Internet of Things','ICT in Business','New Trends and Future Directions of ICT','Project'];

  const BIO_SEED = [
    [1, 'Cell Structure & Function', '1aJBToJrlvA', 'Dr. Tharushi Jayasinghe'],
    [1, 'Biological Molecules', 'j5VA6YrqTNs', 'Dr. Tharushi Jayasinghe'],
    [1, 'Photosynthesis & Cellular Respiration', 'nbDV6dRnEy8', 'Dr. Tharushi Jayasinghe'],
    [2, 'Plant Cells, Tissues & Transport', 'd9GkH4vpK3w', 'Mr. Ruwan Gunasekara'],
    [2, 'Human Circulatory System', '9fxm85Fy4sQ', 'Mr. Ruwan Gunasekara'],
    [2, 'Genetics & Inheritance', 'CBezq1fFUEA', 'Mr. Ruwan Gunasekara'],
  ];
  const ICT_SEED = [
    [1, 'What is ICT?', 'iuZFnijQcrE', 'ICT Desk'],
    [3, 'Binary & Number Systems', 'LpuPe81bc2w', 'ICT Desk'],
    [4, 'Logic Gates', 'InxV9SP92mw', 'ICT Desk'],
    [6, 'Computer Networks', '3QhU9jd03a0', 'ICT Desk'],
    [8, 'Introduction to Databases', 'FR4QIeZaPeM', 'ICT Desk'],
    [9, 'Programming Basics', 'zOjov-2OZ0E', 'ICT Desk'],
    [10, 'HTML & CSS Crash', 'G3e-cpL7ofc', 'ICT Desk'],
  ];

  const TUTORS = [
    { id: 1, name: 'Eng. Pradeep Kumara', subjects: ['Combined Mathematics'], exp: '12 years', loc: 'Colombo 05 + Online', phone: '077 123 4567', bio: 'Engineering graduate. Step-by-step pure and applied maths.' },
    { id: 2, name: 'Ms. Nadeesha Silva', subjects: ['Chemistry'], exp: '8 years', loc: 'Kandy + Online', phone: '071 555 2890', bio: 'B.Sc. Chemistry. Colourful summaries and past-paper discussion.' },
    { id: 3, name: 'Dr. Kavindu Rathnayake', subjects: ['Biology'], exp: '10 years', loc: 'Gampaha + Online', phone: '076 442 1188', bio: 'Medical faculty graduate. Diagram-first biology.' },
    { id: 4, name: 'Mr. S. Thayalan', subjects: ['Combined Mathematics'], exp: '14 years', loc: 'Jaffna + Online', phone: '077 890 3345', bio: 'Bilingual Tamil/English classes. Weekly problem sheets.' },
    { id: 5, name: 'Ms. Fathima Rizna', subjects: ['Chemistry'], exp: '6 years', loc: 'Colombo 03 + Online', phone: '075 667 9021', bio: 'Organic mechanisms and MCQ speed technique.' },
    { id: 6, name: 'Mr. Chaminda Herath', subjects: ['Biology', 'Chemistry'], exp: '15 years', loc: 'Kurunegala + Online', phone: '070 234 8876', bio: 'Bio/chem combination teacher. Printed tutes included.' },
  ];

  const PRACTICALS = [
    { id: 1, subject: 'Physics', category: 'Measurement', en: 'Vernier caliper', si: 'වර්නියර් කැලිපරය', obj: 'Measure internal/external dimensions and depth to 0.02 mm.', theory: 'LC = 1 MSD − 1 VSD. Typical: 50 VSD = 49 mm → LC = 0.02 mm.', proc: '1. Note zero error.\n2. Close jaws on object.\n3. Read main scale + coinciding vernier division × LC.\n4. Correct for zero error.', formula: 'Reading = MSR + (n × LC) ± zero error', viva: ['What is least count?', 'Why is zero error subtracted?'] },
    { id: 2, subject: 'Physics', category: 'Measurement', en: 'Micrometer screw gauge', si: 'මයික්‍රොමීටර්', obj: 'Measure diameter of a wire to 0.01 mm.', theory: 'Pitch 0.5 mm, 50 divisions → LC = 0.01 mm.', proc: 'Close gently with ratchet. Read sleeve + thimble. Apply zero error.', formula: 'Reading = sleeve + (thimble × 0.01) ± ZE', viva: ['Why use the ratchet?', 'What is backlash error?'] },
    { id: 3, subject: 'Physics', category: 'Mechanics', en: 'Simple pendulum — g', si: 'සරල අවලම්බය', obj: 'Find g from T² vs l graph.', theory: 'T = 2π√(l/g) so T² = (4π²/g) l. Slope = 4π²/g.', proc: 'Time 20 oscillations for 5 lengths. Plot T² against l. g = 4π² / slope.', formula: 'g = 4π² / gradient', viva: ['Why small amplitude?', 'Why time 20 swings?'] },
    { id: 4, subject: 'Physics', category: 'Waves', en: 'Resonance tube', si: 'අනුනාද නළය', obj: 'Find speed of sound and end correction.', theory: 'L₁ + e = λ/4; L₂ + e = 3λ/4 → v = 2f(L₂−L₁).', proc: 'Slide water until loudest resonance at known f. Record L₁, L₂.', formula: 'v = 2f(L₂−L₁); e = (L₂−3L₁)/2', viva: ['What is end correction?'] },
    { id: 5, subject: 'Physics', category: 'Electricity', en: 'Metre bridge', si: 'මීටර් සේතුව', obj: 'Find unknown resistance by Wheatstone null.', theory: 'X/R = (100−l)/l at balance.', proc: 'Connect X and known R. Slide jockey to null. Repeat swapping.', formula: 'X = R(100−l)/l', viva: ['Why is the wire uniform?'] },
    { id: 6, subject: 'Chemistry', category: 'Physical', en: 'Titration — NaOH vs HCl', si: 'ටයිටේෂන්', obj: 'Find concentration of NaOH using standard HCl.', theory: 'At end point moles acid = moles base (1:1). Phenolphthalein colourless→pink.', proc: 'Pipette 25.00 cm³ NaOH. Titrate with HCl to faint pink. Concordant titres ±0.10.', formula: 'C₁V₁ = C₂V₂', viva: ['Why rinse the burette with the solution?'] },
    { id: 7, subject: 'Chemistry', category: 'Inorganic', en: 'Flame tests', si: 'ජ්වාලා පරීක්ෂා', obj: 'Identify metal ions by flame colour.', theory: 'Heat excites electrons; drop emits characteristic λ.', proc: 'Clean nichrome in conc. HCl. Dip in sample. Hold in blue Bunsen flame.', formula: 'E = hν', viva: ['Why does Na mask other colours?'] },
    { id: 8, subject: 'Chemistry', category: 'Inorganic', en: 'Anion tests (Cl⁻, SO₄²⁻, CO₃²⁻)', si: 'ඇනායන පරීක්ෂා', obj: 'Identify common anions.', theory: 'AgCl white dissolves in NH₃. BaSO₄ acid-insoluble. Carbonate fizzes with acid.', proc: 'Add reagents dropwise. Record ppt colour and solubility.', formula: 'Ag⁺ + Cl⁻ → AgCl(s)', viva: ['How do you distinguish SO₄²⁻ from CO₃²⁻?'] },
  ];

  const SIMS = [
    { type: 'pendulum', subject: 'phys', title: 'Simple Pendulum', descr: 'Time swings, fit T²–l, find g.', xp: 15 },
    { type: 'titration', subject: 'chem', title: 'Titration bench', descr: 'Reach the 25.00 cm³ end point.', xp: 20 },
    { type: 'flametest', subject: 'chem', title: 'Flame tests', descr: 'Drag the wire into the flame.', xp: 12 },
    { type: 'projectile', subject: 'phys', title: 'Projectile motion', descr: 'Vary u and θ. Watch the parabola.', xp: 15 },
    { type: 'ohmslaw', subject: 'phys', title: "Ohm's law", descr: 'Slide V and R. Live I = V/R.', xp: 10 },
    { type: 'gaslaws', subject: 'chem', title: 'Boyle’s law piston', descr: 'pV stays constant as you squeeze.', xp: 12 },
    { type: 'gplot', subject: 'maths', title: 'Quadratic graphs', descr: 'Tune a, b, c and watch y = ax²+bx+c.', xp: 12 },
    { type: 'binary', subject: 'ict', title: 'Binary workshop', descr: 'Convert bits ↔ decimal live.', xp: 10 },
    { type: 'waves', subject: 'phys', title: 'Transverse wave', descr: 'Change f and A. v = fλ.', xp: 12 },
    { type: 'springshm', subject: 'phys', title: 'Spring SHM', descr: 'Mass-spring. T = 2π√(m/k).', xp: 14 },
    { type: 'freefall', subject: 'phys', title: 'Free fall', descr: 'Drop a ball. s = ½gt².', xp: 10 },
    { type: 'rescolor', subject: 'phys', title: 'Resistor colour code', descr: 'Read the four bands.', xp: 10 },
    { type: 'reflect', subject: 'phys', title: 'Plane mirror', descr: 'i = r. Drag the ray.', xp: 10 },
    { type: 'trig', subject: 'maths', title: 'Unit circle', descr: 'sin, cos, tan of a live angle.', xp: 12 },
    { type: 'deriv', subject: 'maths', title: 'Derivative explorer', descr: 'Tangent on y = x².', xp: 14 },
    { type: 'vector', subject: 'maths', title: 'Vector playground', descr: 'Add two arrows. See the resultant.', xp: 12 },
    { type: 'logic', subject: 'ict', title: 'Logic gates', descr: 'AND / OR / XOR / NOT live.', xp: 12 },
    { type: 'enzyme', subject: 'bio', title: 'Enzyme rate', descr: 'Temperature vs rate curve.', xp: 12 },
    { type: 'equil', subject: 'chem', title: 'Le Chatelier tube', descr: 'Heat the NO₂ ⇌ N₂O₄ mix.', xp: 14 },
  ];

  function loadLS() {
    try { return JSON.parse(localStorage.getItem(KEY) || '{}'); } catch (_) { return {}; }
  }
  function saveLS(part) {
    const cur = loadLS();
    localStorage.setItem(KEY, JSON.stringify(Object.assign(cur, part)));
  }
  async function sha(s) {
    const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('al|' + s));
    return [...new Uint8Array(buf)].map((b) => b.toString(16).padStart(2, '0')).join('');
  }
  function cloudOn() { return typeof window.firebaseReady === 'function' && window.firebaseReady(); }
  function fs() { return firebase.firestore(); }
  function auth() { return firebase.auth(); }

  function buildUnits() {
    const units = [];
    let id = 1;
    const add = (sid, names) => names.forEach((name, i) => units.push({ id: id++, subject_id: sid, name, ord: i + 1 }));
    add(1, CHEM_UNITS); add(2, CM_UNITS); add(3, BIO_UNITS); add(4, PHY_UNITS); add(5, ICT_UNITS);
    return units;
  }

  function uniqYt(list) {
    const seen = new Set();
    return list.filter((v) => {
      const id = v.yt;
      if (!id || seen.has(id)) return false;
      seen.add(id);
      return true;
    });
  }

  function buildLessons(units, pack) {
    const bySidOrd = {};
    units.forEach((u) => { bySidOrd[u.subject_id + ':' + u.ord] = u; });
    const bySidName = {};
    units.forEach((u) => { bySidName[u.subject_id + ':' + u.name] = u; });
    const lessons = [];
    let id = 1;
    const push = (unit, title, yt, teacher, notes) => {
      lessons.push({
        id: id++, unit_id: unit.id, subject_id: unit.subject_id, title, youtube_id: yt || '',
        teacher_name: teacher || '', notes: notes || '', description: teacher ? ('Taught by ' + teacher) : '',
        unit_name: unit.name, ord: 0,
      });
    };
    uniqYt(pack.chemistryVideos || []).forEach((v) => {
      const u = bySidName['1:' + v.unit];
      if (!u) return;
      const n = lessons.filter((l) => l.unit_id === u.id).length + 1;
      const tag = v.tag ? v.tag + ' ' : 'Lesson ';
      push(u, (v.unit + ' — ' + tag + String(n).padStart(2, '0') + (v.teacher ? ' (' + v.teacher + ')' : '')), v.yt, v.teacher);
    });
    uniqYt(pack.physicsVideos || []).forEach((v) => {
      const u = bySidOrd['4:' + v.unitOrd];
      if (!u) return;
      push(u, v.title, v.yt, v.teacher);
    });
    uniqYt(pack.cmVideos || []).forEach((v) => {
      const u = bySidOrd['2:' + v.unitOrd];
      if (!u) return;
      push(u, v.title, v.yt, v.teacher);
    });
    BIO_SEED.forEach(([ord, title, yt, teacher]) => {
      const u = bySidOrd['3:' + ord];
      if (u) push(u, title, yt, teacher);
    });
    ICT_SEED.forEach(([ord, title, yt, teacher]) => {
      const u = bySidOrd['5:' + ord];
      if (u) push(u, title, yt, teacher);
    });
    const counts = {};
    lessons.forEach((l) => { counts[l.unit_id] = (counts[l.unit_id] || 0) + 1; l.ord = counts[l.unit_id]; });
    return lessons;
  }

  const S = {
    ready: false,
    cloud: false,
    user: null,
    units: [],
    lessons: [],
    subjects: SUBJECTS,
    tutors: TUTORS,
    practicals: PRACTICALS,
    sims: SIMS,
    kb: null,
    districts: DISTRICTS,
    streams: STREAMS,
    years: YEARS,
    _cache: { progress: {}, plans: [], resources: [], payments: [], users: [], settings: { exam_date: '2027-08-09', weekly_target: '10' } },
  };

  function sessionUser() {
    const ls = loadLS();
    if (!ls.sid || !ls.users) return null;
    return ls.users.find((u) => u.sid === ls.sid) || null;
  }
  function publicUser(u) {
    if (!u) return null;
    return { id: u.id, name: u.name, email: u.email, role: u.role, school: u.school, district: u.district, al_year: u.al_year, medium: u.medium, stream: u.stream, premium_until: u.premium_until || '' };
  }
  function profileFrom(uid, data) {
    return publicUser(Object.assign({ id: uid }, data || {}));
  }

  async function hydrateCloud(fbUser) {
    if (!fbUser) { S.user = null; return; }
    const ref = fs().collection('users').doc(fbUser.uid);
    const snap = await ref.get();
    let data = snap.exists ? snap.data() : null;
    if (!data) {
      data = { name: fbUser.displayName || 'Student', email: fbUser.email, role: 'student', school: '', district: '', al_year: 'A/L 2027', medium: 'en', stream: '', premium_until: '' };
      await ref.set(data);
    }
    S.user = profileFrom(fbUser.uid, data);
    const [prog, plans, sets] = await Promise.all([
      ref.collection('progress').get(),
      ref.collection('plans').get(),
      ref.collection('settings').doc('me').get(),
    ]);
    S._cache.progress = {};
    prog.forEach((d) => { S._cache.progress[fbUser.uid + ':' + d.id] = d.data(); });
    S._cache.plans = plans.docs.map((d) => Object.assign({ id: d.id }, d.data()));
    if (sets.exists) S._cache.settings = Object.assign(S._cache.settings, sets.data());
    if (S.user.role === 'admin') {
      const [users, pays, res] = await Promise.all([
        fs().collection('users').get(),
        fs().collection('payments').get(),
        fs().collection('resources').get(),
      ]);
      S._cache.users = users.docs.map((d) => profileFrom(d.id, d.data()));
      S._cache.payments = pays.docs.map((d) => Object.assign({ id: d.id }, d.data()));
      S._cache.resources = res.docs.map((d) => Object.assign({ id: d.id }, d.data()));
    } else {
      const [pays, res] = await Promise.all([
        fs().collection('payments').where('uid', '==', fbUser.uid).get(),
        fs().collection('resources').get(),
      ]);
      S._cache.payments = pays.docs.map((d) => Object.assign({ id: d.id }, d.data()));
      S._cache.resources = res.docs.map((d) => Object.assign({ id: d.id }, d.data()));
    }
  }

  async function api(method, path, body) {
    const r = await fetch('/api' + path, {
      method,
      credentials: 'include',
      headers: body ? { 'Content-Type': 'application/json' } : {},
      body: body ? JSON.stringify(body) : undefined,
    });
    let data = {};
    try { data = await r.json(); } catch (_) {}
    if (!r.ok) throw new Error(data.error || 'Request failed');
    return data;
  }
  async function hydrateApi() {
    const st = await api('GET', '/state');
    S.user = st.user;
    S._cache.progress = st.progress || {};
    S._cache.plans = st.plans || [];
    S._cache.settings = st.settings || { exam_date: '2027-08-09', weekly_target: '10' };
    S._cache.payments = st.payments || [];
    S._cache.resources = st.resources || [];
    S._cache.users = st.users || [];
    S._cache.exams = st.exams || [];
    try {
      const board = await api('GET', '/leaderboard');
      S._cache.board = board.rows || [];
    } catch (_) { S._cache.board = S._cache.board || []; }
  }

  S.init = async function () {
    const [vids, kb] = await Promise.all([
      fetch('/data/videos.json').then((r) => r.json()),
      fetch('/data/offline_kb.json').then((r) => r.json()).catch(() => ({ topics: [], guide: '' })),
    ]);
    S.units = buildUnits();
    S.lessons = buildLessons(S.units, vids);
    S.kb = kb;
    if (window.CONTENT && CONTENT.extraPracticals) {
      S.practicals = PRACTICALS.concat(CONTENT.extraPracticals);
    }
    try {
      const h = await fetch('/api/health', { credentials: 'include' });
      if (h.ok) {
        const info = await h.json();
        if (info && info.ok) {
          S.api = true;
          S.cloud = true;
          await hydrateApi();
          S.ready = true;
          return S;
        }
      }
    } catch (_) {}
    if (cloudOn()) {
      S.cloud = true;
      try {
        if (!firebase.apps.length) firebase.initializeApp(window.FIREBASE_CONFIG);
        await new Promise((resolve) => {
          const unsub = auth().onAuthStateChanged(async (u) => {
            unsub();
            try { await hydrateCloud(u); } catch (e) { console.warn(e); }
            resolve();
          });
        });
      } catch (e) {
        console.warn('Firebase init failed, using local mode', e);
        S.cloud = false;
      }
    }
    if (!S.cloud) {
      const ls = loadLS();
      if (!ls.users) saveLS({ users: [], progress: {}, plans: [], resources: [], messages: [], payments: [], settings: { exam_date: '2027-08-09' } });
      S.user = publicUser(sessionUser());
    }
    S.ready = true;
    return S;
  };

  S.subjectById = (id) => S.subjects.find((s) => s.id === +id);
  S.unitsOf = (sid) => S.units.filter((u) => u.subject_id === +sid);
  S.lessonsOfUnit = (uid) => S.lessons.filter((l) => l.unit_id === +uid);
  S.lessonById = (id) => S.lessons.find((l) => l.id === +id);
  S.related = (lesson) => S.lessons.filter((l) => l.subject_id === lesson.subject_id && l.id !== lesson.id).slice(0, 8);
  S.search = (q) => {
    q = (q || '').toLowerCase().trim();
    if (q.length < 2) return { lessons: [], units: [], subjects: [], tutors: [] };
    return {
      lessons: S.lessons.filter((l) => (l.title + ' ' + l.teacher_name).toLowerCase().includes(q)).slice(0, 16),
      units: S.units.filter((u) => u.name.toLowerCase().includes(q)).slice(0, 8),
      subjects: S.subjects.filter((s) => (s.name + s.name_si + s.name_ta).toLowerCase().includes(q)),
      tutors: S.tutors.filter((t) => (t.name + t.subjects.join(' ')).toLowerCase().includes(q)),
    };
  };

  S.register = async function (b) {
    const email = String(b.email || '').trim().toLowerCase();
    if (!email.includes('@')) throw new Error('Enter a valid email');
    if (String(b.password || '').length < 6) throw new Error('Password must be 6+ characters');
    const name = String(b.name || '').trim() || 'Student';
    if (S.api) {
      const out = await api('POST', '/auth/register', Object.assign({}, b, { email, name }));
      await hydrateApi();
      return S.user || out.user;
    }
    if (S.cloud) {
      try {
        const cred = await auth().createUserWithEmailAndPassword(email, b.password);
        await cred.user.updateProfile({ displayName: name });
        const adminWanted = (window.FIREBASE_CONFIG.adminEmail || '').toLowerCase() === email;
        let role = 'student';
        if (adminWanted) role = 'admin';
        else {
          const n = await fs().collection('users').limit(1).get();
          if (n.empty) role = 'admin';
        }
        const data = {
          name, email, role, school: b.school || '', district: b.district || '',
          al_year: b.al_year || 'A/L 2027', medium: b.medium || 'en', stream: b.stream || '',
          premium_until: '', created_at: new Date().toISOString(),
        };
        await fs().collection('users').doc(cred.user.uid).set(data);
        await hydrateCloud(cred.user);
        return S.user;
      } catch (e) {
        const msg = (e && e.message) || 'Register failed';
        if (/email-already/i.test(msg)) throw new Error('That email is already registered');
        if (/weak-password/i.test(msg)) throw new Error('Password must be 6+ characters');
        throw new Error(msg.replace(/^Firebase: /i, '').replace(/ \(auth\/.*/, ''));
      }
    }
    const ls = loadLS();
    if ((ls.users || []).some((u) => u.email === email)) throw new Error('That email is already registered');
    const user = {
      id: Date.now(), name, email,
      pass: await sha(b.password), role: (ls.users || []).length === 0 ? 'admin' : 'student',
      school: b.school || '', district: b.district || '', al_year: b.al_year || 'A/L 2027',
      medium: b.medium || 'en', stream: b.stream || '', sid: crypto.randomUUID(),
    };
    ls.users = ls.users || [];
    ls.users.push(user);
    ls.sid = user.sid;
    saveLS(ls);
    S.user = publicUser(user);
    return S.user;
  };
  S.login = async function (email, password) {
    if (S.api) {
      await api('POST', '/auth/login', { email, password });
      await hydrateApi();
      return S.user;
    }
    if (S.cloud) {
      try {
        const cred = await auth().signInWithEmailAndPassword(String(email || '').toLowerCase(), password);
        await hydrateCloud(cred.user);
        return S.user;
      } catch (e) {
        throw new Error('Incorrect email or password');
      }
    }
    const ls = loadLS();
    const hash = await sha(password);
    const u = (ls.users || []).find((x) => x.email === String(email || '').toLowerCase() && x.pass === hash);
    if (!u) throw new Error('Incorrect email or password');
    u.sid = crypto.randomUUID();
    ls.sid = u.sid;
    saveLS(ls);
    S.user = publicUser(u);
    return S.user;
  };
  S.logout = async function () {
    if (S.api) { try { await api('POST', '/auth/logout'); } catch (_) {} }
    if (S.cloud && !S.api) { try { await auth().signOut(); } catch (_) {} }
    const ls = loadLS(); delete ls.sid; saveLS(ls);
    S.user = null;
    S._cache.progress = {};
    S._cache.plans = [];
  };

  S.prog = function () { return S.cloud ? S._cache.progress : (loadLS().progress || {}); };
  S.toggle = async function (lessonId, field) {
    if (!S.user) throw new Error('Please sign in');
    const key = S.user.id + ':' + lessonId;
    const row = Object.assign({ completed: 0, watched: 0, favourite: 0 }, S.stateOf(lessonId));
    row[field] = row[field] ? 0 : 1;
    if (field === 'completed' && row.completed) row.completed_at = new Date().toISOString();
    if (S.api) {
      const saved = await api('POST', '/progress/toggle', { lessonId, field });
      S._cache.progress[key] = saved;
      return saved;
    }
    if (S.cloud) {
      S._cache.progress[key] = row;
      await fs().collection('users').doc(String(S.user.id)).collection('progress').doc(String(lessonId)).set(row);
      return row;
    }
    const ls = loadLS();
    ls.progress = ls.progress || {};
    ls.progress[key] = row;
    saveLS(ls);
    return row;
  };
  S.stateOf = function (lessonId) {
    if (!S.user) return { completed: 0, watched: 0, favourite: 0 };
    const map = S.prog();
    return map[S.user.id + ':' + lessonId] || { completed: 0, watched: 0, favourite: 0 };
  };
  S.stats = function () {
    const students = S.cloud
      ? (S._cache.users || []).filter((u) => u.role === 'student').length
      : (loadLS().users || []).filter((u) => u.role === 'student').length;
    return {
      subjects: S.subjects.length,
      units: S.units.length,
      lessons: S.lessons.length,
      videos: S.lessons.filter((l) => l.youtube_id).length,
      tutors: S.tutors.length,
      students,
    };
  };
  S.dash = function () {
    if (!S.user) return null;
    const prog = S.prog();
    const mine = Object.entries(prog).filter(([k]) => k.startsWith(S.user.id + ':'));
    const byField = (f) => mine.filter(([, v]) => v[f]).map(([k]) => S.lessonById(+k.split(':')[1])).filter(Boolean);
    const subjects = S.subjects.map((s) => {
      const lsns = S.lessons.filter((l) => l.subject_id === s.id);
      const done = lsns.filter((l) => (prog[S.user.id + ':' + l.id] || {}).completed).length;
      return Object.assign({}, s, { total: lsns.length, completed: done });
    });
    return { subjects, completed: byField('completed'), watched: byField('watched'), favourites: byField('favourite') };
  };
  S.settings = function () {
    if (S.cloud) return Object.assign({ exam_date: '2027-08-09', weekly_target: '10' }, S._cache.settings || {});
    return Object.assign({ exam_date: '2027-08-09', weekly_target: '10' }, loadLS().settings || {});
  };
  S.setSettings = async function (p) {
    const next = Object.assign(S.settings(), p);
    if (S.api) {
      const out = await api('PUT', '/settings', next);
      S._cache.settings = out.settings || next;
      return S._cache.settings;
    }
    if (S.cloud && S.user) {
      S._cache.settings = next;
      await fs().collection('users').doc(String(S.user.id)).collection('settings').doc('me').set(next);
      return next;
    }
    const ls = loadLS(); ls.settings = next; saveLS(ls); return next;
  };
  S.plans = function () {
    if (S.cloud) return S._cache.plans || [];
    return (loadLS().plans || []).filter((p) => S.user && p.uid === S.user.id);
  };
  S.addPlan = async function (lessonId, date) {
    if (!S.user) throw new Error('Please sign in');
    const row = { uid: S.user.id, lesson_id: +lessonId, plan_date: date, done: 0 };
    if (S.api) {
      const out = await api('POST', '/planner', { lessonId, date });
      S._cache.plans.push(out.plan);
      return;
    }
    if (S.cloud) {
      const ref = await fs().collection('users').doc(String(S.user.id)).collection('plans').add(row);
      S._cache.plans.push(Object.assign({ id: ref.id }, row));
      return;
    }
    const ls = loadLS();
    ls.plans = ls.plans || [];
    ls.plans.push(Object.assign({ id: Date.now() }, row));
    saveLS(ls);
  };
  S.togglePlan = async function (id) {
    if (S.api) {
      await api('POST', '/planner/' + id + '/toggle');
      const p = (S._cache.plans || []).find((x) => String(x.id) === String(id));
      if (p) p.done = p.done ? 0 : 1;
      return;
    }
    if (S.cloud && S.user) {
      const p = (S._cache.plans || []).find((x) => String(x.id) === String(id));
      if (!p) return;
      p.done = p.done ? 0 : 1;
      await fs().collection('users').doc(String(S.user.id)).collection('plans').doc(String(id)).update({ done: p.done });
      return;
    }
    const ls = loadLS();
    const p = (ls.plans || []).find((x) => x.id === +id);
    if (p) p.done = p.done ? 0 : 1;
    saveLS(ls);
  };
  S.delPlan = async function (id) {
    if (S.api) {
      await api('DELETE', '/planner/' + id);
      S._cache.plans = (S._cache.plans || []).filter((x) => String(x.id) !== String(id));
      return;
    }
    if (S.cloud && S.user) {
      S._cache.plans = (S._cache.plans || []).filter((x) => String(x.id) !== String(id));
      await fs().collection('users').doc(String(S.user.id)).collection('plans').doc(String(id)).delete();
      return;
    }
    const ls = loadLS(); ls.plans = (ls.plans || []).filter((x) => x.id !== +id); saveLS(ls);
  };
  const SEED_RES = [
    { id: 's1', title: 'Atomic Structure — Short Notes', category: 'notes', subject_id: 1, status: 'approved', href: '/data/notes/chem-atom.html' },
    { id: 's2', title: 'Mole Concept — Calculation Pack', category: 'question_papers', subject_id: 1, status: 'approved', href: '/data/notes/chem-atom.html' },
    { id: 's3', title: 'Limits & Continuity — Worked Examples', category: 'notes', subject_id: 2, status: 'approved', href: '/data/notes/cm-limits.html' },
    { id: 's4', title: 'Integration formula sheet', category: 'short_notes', subject_id: 2, status: 'approved', href: '/data/notes/cm-limits.html' },
    { id: 's5', title: 'Cell Structure — Illustrated Notes', category: 'notes', subject_id: 3, status: 'approved', href: '/data/notes/bio-cell.html' },
    { id: 's6', title: 'AL Physics Model Paper 2026', category: 'model_papers', subject_id: 4, status: 'approved', href: '/data/notes/phy-model.html' },
  ];
  S.fileUrl = function (r) {
    if (r.href) return r.href;
    if (r.hasFile) return '/api/resources/' + r.id + '/file';
    return '';
  };
  S.resources = function (subjectId) {
    const extra = S.cloud ? (S._cache.resources || []) : (loadLS().resources || []);
    return SEED_RES.concat(extra).filter((r) => {
      if (subjectId && Number(r.subject_id) !== Number(subjectId)) return false;
      return r.status === 'approved' || (S.user && (S.user.role === 'admin' || String(S.user.id) === String(r.uid)));
    });
  };
  async function fileToB64(file) {
    const buf = await file.arrayBuffer();
    const bytes = new Uint8Array(buf);
    const chunk = 0x8000;
    let bin = '';
    for (let i = 0; i < bytes.length; i += chunk) {
      bin += String.fromCharCode.apply(null, bytes.subarray(i, i + chunk));
    }
    return btoa(bin);
  }
  S.addResource = async function (title, category, subjectId, file) {
    if (!S.user) throw new Error('Please sign in');
    if (file && file.size > 3.5 * 1024 * 1024) throw new Error('File must be under 3.5 MB');
    const row = { title, category, subject_id: +subjectId || null, status: S.user.role === 'admin' ? 'approved' : 'pending', by: S.user.name, uid: S.user.id, hasFile: !!file, fileName: file ? file.name : '' };
    const payload = { title, category, subjectId };
    if (file) {
      payload.fileName = file.name;
      payload.mime = file.type || 'application/octet-stream';
      payload.data = await fileToB64(file);
    }
    if (S.api) {
      const out = await api('POST', '/resources', payload);
      S._cache.resources.push(out.resource);
      return out.resource;
    }
    if (S.cloud) {
      const ref = await fs().collection('resources').add(row);
      S._cache.resources.push(Object.assign({ id: ref.id }, row));
      return;
    }
    const ls = loadLS();
    ls.resources = ls.resources || [];
    ls.resources.push(Object.assign({ id: Date.now() }, row));
    saveLS(ls);
  };
  S.approveResource = async function (id, status) {
    if (S.api) {
      await api('PUT', '/resources/' + id, { status });
      const r = (S._cache.resources || []).find((x) => String(x.id) === String(id));
      if (r) r.status = status;
      return;
    }
    if (S.cloud) {
      const r = (S._cache.resources || []).find((x) => String(x.id) === String(id));
      if (r) r.status = status;
      await fs().collection('resources').doc(String(id)).update({ status });
      return;
    }
    const ls = loadLS();
    const r = (ls.resources || []).find((x) => x.id === +id);
    if (r) r.status = status;
    saveLS(ls);
  };
  S.users = function () {
    if (S.cloud) return S._cache.users || [];
    return (loadLS().users || []).map(publicUser);
  };
  S.changePassword = async function (oldPass, password) {
    if (S.api) {
      await api('POST', '/auth/password', { old: oldPass, password });
      return;
    }
    if (S.cloud && !S.api) {
      const u = auth().currentUser;
      if (!u) throw new Error('Please sign in');
      const cred = firebase.auth.EmailAuthProvider.credential(u.email, oldPass);
      await u.reauthenticateWithCredential(cred);
      await u.updatePassword(password);
      return;
    }
    const ls = loadLS();
    const u = sessionUser();
    if (!u || u.pass !== await sha(oldPass)) throw new Error('Current password is wrong');
    if (String(password || '').length < 6) throw new Error('Password must be 6+ characters');
    u.pass = await sha(password);
    saveLS(ls);
  };
  S.deleteUser = async function (id) {
    if (!S.user || S.user.role !== 'admin') throw new Error('Admins only');
    if (String(id) === String(S.user.id)) throw new Error('You cannot delete yourself');
    if (S.api) {
      await api('DELETE', '/users/' + id);
      await hydrateApi();
      return;
    }
    if (S.cloud) {
      S._cache.users = (S._cache.users || []).filter((x) => String(x.id) !== String(id));
      await fs().collection('users').doc(String(id)).delete();
      return;
    }
    const ls = loadLS();
    ls.users = (ls.users || []).filter((x) => String(x.id) !== String(id));
    saveLS(ls);
  };
  S.setRole = async function (id, role) {
    const next = role === 'admin' ? 'admin' : 'student';
    if (S.api) {
      await api('PUT', '/users/' + id, { role: next });
      const u = (S._cache.users || []).find((x) => String(x.id) === String(id));
      if (u) u.role = next;
      return;
    }
    if (S.cloud) {
      const u = (S._cache.users || []).find((x) => String(x.id) === String(id));
      if (u) u.role = next;
      await fs().collection('users').doc(String(id)).update({ role: next });
      return;
    }
    const ls = loadLS();
    const u = (ls.users || []).find((x) => x.id === +id);
    if (u) u.role = next;
    saveLS(ls);
  };
  S.offlineAnswer = function (text) {
    const t2 = (' ' + String(text || '').toLowerCase().replace(/[^a-z0-9+\- ]+/g, ' ') + ' ');
    let best = null, bestSc = 0;
    ((S.kb && S.kb.topics) || []).forEach((tp) => {
      let sc = 0;
      (tp.keys || []).forEach((k) => { const k2 = String(k).toLowerCase().trim(); if (k2 && t2.includes(k2)) sc += 1 + k2.split(' ').length; });
      if (sc > bestSc) { best = tp; bestSc = sc; }
    });
    if (!best) return '🧠 ' + ((S.kb && S.kb.guide) || 'Ask about mole, titration, projectile, differentiation, DNA, binary…');
    return '🧠 AL Guru — ' + best.title + ' [' + best.subj + ']\n\n' + best.body;
  };
  S.pay = async function (method, note) {
    if (!S.user) throw new Error('Please sign in');
    const row = { uid: S.user.id, name: S.user.name, method, note, status: 'pending', amount: 990, created_at: new Date().toISOString() };
    if (S.api) {
      const out = await api('POST', '/premium', { method, note });
      S._cache.payments.push(out.payment);
      return;
    }
    if (S.cloud) {
      const ref = await fs().collection('payments').add(row);
      S._cache.payments.push(Object.assign({ id: ref.id }, row));
      return;
    }
    const ls = loadLS();
    ls.payments = ls.payments || [];
    ls.payments.push(Object.assign({ id: Date.now() }, row));
    saveLS(ls);
  };
  S.payments = function () { return S.cloud ? (S._cache.payments || []) : (loadLS().payments || []); };
  S.decidePay = async function (id, ok) {
    const status = ok ? 'approved' : 'rejected';
    if (S.api) {
      await api('PUT', '/payments/' + id, { ok: !!ok });
      await hydrateApi();
      return;
    }
    if (S.cloud) {
      const p = (S._cache.payments || []).find((x) => String(x.id) === String(id));
      if (!p) return;
      p.status = status;
      await fs().collection('payments').doc(String(id)).update({ status });
      if (ok) {
        const until = new Date(Date.now() + 31 * 864e5).toISOString().slice(0, 10);
        await fs().collection('users').doc(String(p.uid)).update({ premium_until: until });
        const u = (S._cache.users || []).find((x) => String(x.id) === String(p.uid));
        if (u) u.premium_until = until;
      }
      return;
    }
    const ls = loadLS();
    const p = (ls.payments || []).find((x) => x.id === +id);
    if (!p) return;
    p.status = status;
    if (ok) {
      const u = (ls.users || []).find((x) => x.id === p.uid);
      if (u) u.premium_until = new Date(Date.now() + 31 * 864e5).toISOString().slice(0, 10);
    }
    saveLS(ls);
  };

  S.examHistory = function () {
    const uid = S.user ? S.user.id : 'guest';
    const local = (loadLS().exams || []).filter((e) => String(e.uid) === String(uid));
    if (S.api && S.user) return (S._cache.exams || []).concat(local.filter((e) => e.uid === 'guest'));
    return local;
  };
  S.saveExam = async function (row) {
    const rec = Object.assign({ uid: S.user ? S.user.id : 'guest', at: new Date().toISOString() }, row);
    if (S.api && S.user) {
      await api('POST', '/exam', rec);
      S._cache.exams = S._cache.exams || [];
      S._cache.exams.push(rec);
      try {
        const board = await api('GET', '/leaderboard');
        S._cache.board = board.rows || [];
      } catch (_) {}
      return rec;
    }
    const ls = loadLS();
    ls.exams = ls.exams || [];
    ls.exams.push(rec);
    saveLS(ls);
    return rec;
  };
  S.xp = function () {
    if (!S.user) return { total: 0, by: {}, badges: [], exams: 0, done: 0, watch: 0 };
    const prog = S.prog();
    const keys = Object.keys(prog).filter((k) => k.startsWith(S.user.id + ':'));
    const done = keys.filter((k) => prog[k].completed).length;
    const watch = keys.filter((k) => prog[k].watched).length;
    const exams = S.examHistory();
    const examPts = exams.reduce((a, e) => a + (e.score || 0) * 2, 0);
    const by = { lessons: done * 20, videos: watch * 5, exams: examPts };
    const total = Object.values(by).reduce((a, b) => a + b, 0);
    const badges = [
      { id: 'first', ic: '🎬', name: 'First lesson', ok: done >= 1 },
      { id: 'ten', ic: '📚', name: '10 lessons', ok: done >= 10 },
      { id: 'quiz', ic: '🎯', name: 'First exam', ok: exams.length >= 1 },
      { id: 'ace', ic: '🏆', name: '80%+ exam', ok: exams.some((e) => e.total && e.score / e.total >= 0.8) },
      { id: 'lab', ic: '🧪', name: 'Lab explorer', ok: watch + done >= 5 },
    ];
    return { total, by, badges, exams: exams.length, done, watch };
  };
  S.weekPlan = function (weakSid) {
    const days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'];
    const pool = S.lessons.filter((l) => !weakSid || l.subject_id === +weakSid);
    const extra = S.lessons.filter((l) => weakSid && l.subject_id !== +weakSid);
    return days.map((d, i) => ({
      day: d,
      items: [
        pool.length ? { title: pool[i % pool.length].title, href: '#/lesson/' + pool[i % pool.length].id, kind: 'Lesson' } : null,
        i === 3 ? { title: 'Virtual lab day', href: '#/lab', kind: 'Lab' } : null,
        i === 5 ? { title: 'Timed past-paper (Exam mode)', href: '#/exam', kind: 'Exam' } : null,
        i === 6 ? { title: 'Quantum AI doubt clearing', href: '#/', kind: 'AI' } : null,
        extra.length && i % 2 === 0 ? { title: extra[i % extra.length].title, href: '#/lesson/' + extra[i % extra.length].id, kind: 'Balance' } : null,
      ].filter(Boolean),
    }));
  };
  S.board = function () {
    if (S.api && (S._cache.board || []).length) {
      return (S._cache.board || []).map((r) => Object.assign({}, r, {
        me: S.user && String(r.id) === String(S.user.id),
      }));
    }
    const users = S.cloud ? (S._cache.users || []) : (loadLS().users || []).map(publicUser);
    const exams = (S.api || S.cloud) ? (S._cache.exams || []) : (loadLS().exams || []);
    const prog = S.prog();
    return users.filter((u) => u && u.role !== 'admin').map((u) => {
      const done = Object.keys(prog).filter((k) => k.startsWith(u.id + ':') && prog[k].completed).length;
      const mine = exams.filter((e) => String(e.uid) === String(u.id));
      const pts = done * 20 + mine.reduce((a, e) => a + (e.score || 0) * 2, 0);
      return { id: u.id, name: (u.name || 'Student').split(' ')[0], school: u.school || '', pts, done, me: S.user && String(u.id) === String(S.user.id) };
    }).sort((a, b) => b.pts - a.pts).slice(0, 20);
  };

  window.Store = S;
})();
