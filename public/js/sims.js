/* Interactive canvas simulators */
window.Sims = {
  mount(el, type) {
    el.innerHTML = '';
    const wrap = document.createElement('div');
    wrap.className = 'sim-stage';
    const canvas = document.createElement('canvas');
    canvas.width = 720; canvas.height = 360;
    wrap.appendChild(canvas);
    const ctrl = document.createElement('div');
    ctrl.style.cssText = 'padding:12px;background:#111827;color:#e5e7eb;display:flex;flex-wrap:wrap;gap:10px;align-items:center';
    el.appendChild(wrap); el.appendChild(ctrl);
    const ctx = canvas.getContext('2d');
    const sliders = {};
    const add = (name, min, max, val, step) => {
      const lab = document.createElement('label');
      lab.style.cssText = 'font-size:13px;display:flex;gap:6px;align-items:center';
      const inp = document.createElement('input');
      inp.type = 'range'; inp.min = min; inp.max = max; inp.value = val; inp.step = step || 1;
      const out = document.createElement('span');
      out.textContent = val;
      inp.oninput = () => { out.textContent = inp.value; };
      lab.append(name, inp, out);
      ctrl.appendChild(lab);
      sliders[name] = inp;
      return inp;
    };
    const loop = (fn) => {
      let raf;
      const tick = () => { fn(); raf = requestAnimationFrame(tick); };
      tick();
      return () => cancelAnimationFrame(raf);
    };
    const bg = () => { ctx.fillStyle = '#0b1220'; ctx.fillRect(0, 0, canvas.width, canvas.height); };

    if (type === 'pendulum') {
      const L = add('L (m)', 0.4, 2, 1, 0.05);
      const g = add('g', 1.6, 24.8, 9.8, 0.1);
      let th = 0.4, w = 0, last = performance.now();
      loop(() => {
        const now = performance.now(); const dt = Math.min(0.03, (now - last) / 1000); last = now;
        const acc = -(+g.value / +L.value) * Math.sin(th);
        w += acc * dt; th += w * dt;
        bg();
        const ox = 360, oy = 30, len = +L.value * 140;
        const x = ox + Math.sin(th) * len, y = oy + Math.cos(th) * len;
        ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 2; ctx.beginPath(); ctx.moveTo(ox, oy); ctx.lineTo(x, y); ctx.stroke();
        ctx.fillStyle = '#38bdf8'; ctx.beginPath(); ctx.arc(x, y, 16, 0, 6.28); ctx.fill();
        const T = 2 * Math.PI * Math.sqrt(+L.value / +g.value);
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        ctx.fillText('T = 2π√(l/g) = ' + T.toFixed(2) + ' s', 20, 330);
      });
    } else if (type === 'projectile') {
      const u = add('u (m/s)', 5, 40, 20, 1);
      const ang = add('θ (°)', 10, 80, 45, 1);
      loop(() => {
        bg();
        const th = +ang.value * Math.PI / 180, uu = +u.value, G = 9.81;
        const R = uu * uu * Math.sin(2 * th) / G, H = (uu * uu * Math.sin(th) ** 2) / (2 * G);
        ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2; ctx.beginPath();
        for (let t = 0; t < 8; t += 0.02) {
          const x = uu * Math.cos(th) * t;
          const y = uu * Math.sin(th) * t - 0.5 * G * t * t;
          if (y < 0 && t > 0) break;
          const px = 40 + x * (640 / Math.max(R, 1));
          const py = 320 - y * (260 / Math.max(H * 1.3, 1));
          if (t === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
        ctx.fillStyle = '#e2e8f0'; ctx.font = '15px Outfit,sans-serif';
        ctx.fillText('R = u² sin2θ / g = ' + R.toFixed(1) + ' m    H = ' + H.toFixed(1) + ' m', 20, 340);
      });
    } else if (type === 'ohmslaw') {
      const V = add('V (V)', 0, 12, 6, 0.1);
      const R = add('R (Ω)', 1, 50, 10, 0.5);
      loop(() => {
        bg();
        const I = +V.value / +R.value;
        ctx.fillStyle = '#38bdf8';
        ctx.fillRect(80, 200 - I * 20, 80, I * 20);
        ctx.fillStyle = '#a78bfa';
        ctx.fillRect(220, 200 - +V.value * 10, 80, +V.value * 10);
        ctx.fillStyle = '#34d399';
        ctx.fillRect(360, 200 - +R.value * 3, 80, +R.value * 3);
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        ctx.fillText('I = V / R = ' + I.toFixed(2) + ' A', 20, 330);
        ctx.fillText('I', 105, 220); ctx.fillText('V', 250, 220); ctx.fillText('R', 390, 220);
      });
    } else if (type === 'gaslaws') {
      const V = add('V', 20, 100, 60, 1);
      loop(() => {
        bg();
        const p = 2400 / +V.value;
        const w = +V.value * 4;
        ctx.fillStyle = '#1e293b'; ctx.fillRect(80, 80, 400, 200);
        ctx.fillStyle = '#38bdf8'; ctx.fillRect(80, 80, w, 200);
        for (let i = 0; i < 30; i++) {
          ctx.fillStyle = '#fbbf24';
          ctx.beginPath();
          ctx.arc(100 + Math.random() * (w - 20), 100 + Math.random() * 160, 4, 0, 6.28);
          ctx.fill();
        }
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        ctx.fillText('pV = const    p ≈ ' + p.toFixed(1) + '  (Boyle)', 20, 330);
      });
    } else if (type === 'gplot') {
      const a = add('a', -3, 3, 1, 0.1);
      const b = add('b', -5, 5, 0, 0.1);
      const c = add('c', -5, 5, 0, 0.1);
      loop(() => {
        bg();
        ctx.strokeStyle = '#334155'; ctx.beginPath(); ctx.moveTo(0, 180); ctx.lineTo(720, 180); ctx.moveTo(360, 0); ctx.lineTo(360, 360); ctx.stroke();
        ctx.strokeStyle = '#38bdf8'; ctx.lineWidth = 2; ctx.beginPath();
        for (let px = 0; px < 720; px++) {
          const x = (px - 360) / 40;
          const y = (+a.value) * x * x + (+b.value) * x + (+c.value);
          const py = 180 - y * 28;
          if (px === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
        }
        ctx.stroke();
        const d = (+b.value) ** 2 - 4 * (+a.value) * (+c.value);
        ctx.fillStyle = '#e2e8f0'; ctx.font = '15px Outfit,sans-serif';
        ctx.fillText('y = ax² + bx + c     Δ = ' + d.toFixed(2), 20, 340);
      });
    } else if (type === 'binary') {
      const bits = [0, 0, 0, 0, 1, 1, 0, 1];
      const draw = () => {
        bg();
        let dec = 0;
        bits.forEach((b, i) => {
          const x = 40 + i * 80;
          ctx.fillStyle = b ? '#22d3ee' : '#1e293b';
          ctx.fillRect(x, 80, 64, 80);
          ctx.fillStyle = '#fff'; ctx.font = '28px Outfit,sans-serif'; ctx.textAlign = 'center';
          ctx.fillText(String(b), x + 32, 132);
          ctx.font = '12px Outfit,sans-serif'; ctx.fillStyle = '#94a3b8';
          ctx.fillText(String(2 ** (7 - i)), x + 32, 180);
          if (b) dec += 2 ** (7 - i);
        });
        ctx.textAlign = 'left'; ctx.fillStyle = '#e2e8f0'; ctx.font = '20px Outfit,sans-serif';
        ctx.fillText('Decimal = ' + dec + '     Hex = ' + dec.toString(16).toUpperCase(), 40, 250);
      };
      canvas.onclick = (e) => {
        const r = canvas.getBoundingClientRect();
        const x = (e.clientX - r.left) * (canvas.width / r.width);
        const i = Math.floor((x - 40) / 80);
        if (i >= 0 && i < 8) bits[i] = bits[i] ? 0 : 1;
        draw();
      };
      ctrl.innerHTML = '<span>Tap a bit to flip it</span>';
      draw();
    } else if (type === 'waves') {
      const f = add('f (Hz)', 0.3, 3, 1, 0.1);
      const A = add('A', 10, 80, 40, 1);
      let t = 0;
      loop(() => {
        t += 0.04; bg();
        ctx.strokeStyle = '#22d3ee'; ctx.lineWidth = 2; ctx.beginPath();
        for (let x = 0; x < 720; x++) {
          const y = 180 + (+A.value) * Math.sin((x / 80) * +f.value * 2 + t);
          if (x === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.fillStyle = '#e2e8f0'; ctx.font = '15px Outfit,sans-serif';
        ctx.fillText('v = fλ   (shape travels; particles oscillate ⊥ travel)', 20, 340);
      });
    } else if (type === 'springshm') {
      const m = add('m (kg)', 0.2, 3, 1, 0.1);
      const k = add('k (N/m)', 5, 40, 16, 1);
      let t = 0;
      loop(() => {
        t += 0.03; bg();
        const om = Math.sqrt(+k.value / +m.value);
        const y = 80 + 70 * Math.sin(om * t);
        ctx.strokeStyle = '#94a3b8'; ctx.lineWidth = 2; ctx.beginPath();
        for (let i = 0; i < 12; i++) {
          const yy = 20 + (y - 20) * i / 12;
          ctx.lineTo(360 + ((i % 2) ? 18 : -18), yy);
        }
        ctx.stroke();
        ctx.fillStyle = '#f97316'; ctx.fillRect(330, y, 60, 40);
        const T = 2 * Math.PI * Math.sqrt(+m.value / +k.value);
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        ctx.fillText('T = 2π√(m/k) = ' + T.toFixed(2) + ' s', 20, 330);
      });
    } else if (type === 'flametest') {
      const salts = [
        { ion: 'Na⁺', col: '#ffc81e', name: 'golden yellow' },
        { ion: 'K⁺', col: '#c4b5fd', name: 'lilac' },
        { ion: 'Ca²⁺', col: '#f87171', name: 'brick-red' },
        { ion: 'Ba²⁺', col: '#86efac', name: 'apple-green' },
        { ion: 'Cu²⁺', col: '#22d3ee', name: 'blue-green' },
        { ion: 'Li⁺', col: '#fb7185', name: 'crimson' },
      ];
      let pick = 0, inFlame = false;
      salts.forEach((s, i) => {
        const b = document.createElement('button');
        b.className = 'ghost'; b.textContent = s.ion;
        b.onclick = () => { pick = i; };
        ctrl.appendChild(b);
      });
      canvas.onpointerdown = () => { inFlame = true; };
      canvas.onpointerup = () => { inFlame = false; };
      loop(() => {
        bg();
        ctx.fillStyle = '#334155'; ctx.fillRect(300, 220, 120, 18);
        const grd = ctx.createRadialGradient(360, 160, 10, 360, 180, 80);
        grd.addColorStop(0, inFlame ? salts[pick].col : '#fb923c');
        grd.addColorStop(1, 'rgba(0,0,0,0)');
        ctx.fillStyle = grd; ctx.beginPath(); ctx.ellipse(360, 170, 40, 70, 0, 0, 6.28); ctx.fill();
        ctx.strokeStyle = '#cbd5e1'; ctx.lineWidth = 3; ctx.beginPath(); ctx.moveTo(200, 80); ctx.lineTo(340, 150); ctx.stroke();
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        ctx.fillText(salts[pick].ion + ' → ' + salts[pick].name + (inFlame ? '  (hold to heat)' : '  — press & hold'), 20, 330);
      });
    } else if (type === 'titration') {
      const rate = add('stopcock', 0, 2, 0, 1);
      let vol = 0, done = false;
      const reset = document.createElement('button');
      reset.className = 'ghost'; reset.textContent = 'Reset';
      reset.onclick = () => { vol = 0; done = false; };
      ctrl.appendChild(reset);
      loop(() => {
        if (+rate.value && vol < 40) vol += +rate.value * 0.08;
        const over = vol >= 25;
        bg();
        ctx.fillStyle = '#64748b'; ctx.fillRect(330, 20, 20, 160);
        ctx.fillStyle = over ? '#f9a8d4' : '#e0f2fe';
        const h = Math.min(120, vol * 4);
        ctx.fillRect(300, 300 - h, 120, h);
        ctx.strokeStyle = '#94a3b8'; ctx.strokeRect(300, 180, 120, 120);
        ctx.fillStyle = '#e2e8f0'; ctx.font = '16px Outfit,sans-serif';
        const msg = vol < 24.5 ? 'Keep going…' : vol < 25.2 ? 'END POINT — faint pink!' : 'Overshot! Reset.';
        if (vol >= 24.5 && vol < 25.2) done = true;
        ctx.fillText('V = ' + vol.toFixed(2) + ' cm³   ' + msg, 20, 340);
      });
    } else {
      bg();
      ctx.fillStyle = '#e2e8f0'; ctx.font = '18px Outfit,sans-serif';
      ctx.fillText('Open this simulator from the Lab page.', 40, 180);
    }
  },
};
