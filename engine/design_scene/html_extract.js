// PPT Smith fixed layout extractor. Injected by `engine design html-import`; never authored per task.
// Reads the browser's computed layout of #slide and emits native-object candidates as JSON.
(function () {
  'use strict';
  const slide = document.getElementById('slide');
  const out = { version: 1, items: [], warnings: [] };
  if (!slide) { out.error = 'SLIDE_ROOT_MISSING'; return finish(); }
  const S = slide.getBoundingClientRect();
  out.width = S.width; out.height = S.height;
  out.background = getComputedStyle(slide).backgroundColor;
  const R = (r) => ({ x: r.left - S.left, y: r.top - S.top, w: r.width, h: r.height });
  const visible = (c) => !!c && c !== 'transparent' && !/rgba\([^)]*,\s*0\)$/.test(c);
  const warn = (code, el) => out.warnings.push({ code, at: describe(el) });
  function describe(el) {
    if (!el || !el.tagName) return '';
    const r = el.getBoundingClientRect();
    return el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).join('.') : '') +
      ' @' + Math.round(r.left - S.left) + ',' + Math.round(r.top - S.top);
  }
  function attrUp(el, name) {
    for (let e = el; e && e !== document.body; e = e.parentElement) if (e.hasAttribute && e.hasAttribute(name)) return e.getAttribute(name);
    return null;
  }
  const font = (cs) => ({
    stack: cs.fontFamily.split(',').map(s => s.replace(/["']/g, '').trim()).filter(Boolean),
    size: parseFloat(cs.fontSize), weight: parseInt(cs.fontWeight, 10), italic: cs.fontStyle === 'italic',
    color: cs.color, letterSpacing: cs.letterSpacing === 'normal' ? 0 : parseFloat(cs.letterSpacing),
    lineHeight: cs.lineHeight === 'normal' ? parseFloat(cs.fontSize) * 1.3 : parseFloat(cs.lineHeight),
  });
  const isInline = (el) => getComputedStyle(el).display.startsWith('inline') && el.tagName.toLowerCase() !== 'svg';
  const hasOwnText = (el) => [...el.childNodes].some(n => n.nodeType === 3 && n.textContent.trim());

  function runsOf(el) {
    const runs = [];
    for (const n of el.childNodes) {
      if (n.nodeType === 3) { if (n.textContent.length) runs.push({ text: n.textContent.replace(/\s+/g, ' '), ...font(getComputedStyle(el)) }); }
      else if (n.nodeType === 1 && isInline(n)) runs.push(...runsOf(n));
    }
    return runs;
  }
  function trimRuns(runs) {
    if (runs.length) { runs[0].text = runs[0].text.replace(/^\s+/, ''); runs[runs.length - 1].text = runs[runs.length - 1].text.replace(/\s+$/, ''); }
    return runs.filter(r => r.text.length);
  }
  function meta(el) {
    return { cid: el.getAttribute('data-cid'), src: attrUp(el, 'data-src'), authored: attrUp(el, 'data-authored') };
  }
  function textItem(el) {
    const cs = getComputedStyle(el);
    const rg = document.createRange(); rg.selectNodeContents(el);
    const rects = [...rg.getClientRects()].filter(r => r.width > 0.5);
    if (!rects.length) return null;
    const lh = font(cs).lineHeight; const lines = [];
    rects.map(r => (r.top + r.bottom) / 2).sort((a, b) => a - b).forEach(c => { if (!lines.length || c - lines[lines.length - 1] > lh * 0.6) lines.push(c); });
    const u = rg.getBoundingClientRect(), er = el.getBoundingClientRect();
    const pl = parseFloat(cs.paddingLeft) + parseFloat(cs.borderLeftWidth), pr = parseFloat(cs.paddingRight) + parseFloat(cs.borderRightWidth);
    const runs = trimRuns(runsOf(el));
    if (!runs.length) return null;
    if (cs.writingMode && !cs.writingMode.startsWith('horizontal')) warn('VERTICAL_WRITING_MODE_UNSUPPORTED', el);
    return { kind: 'text', ...R(u), lines: lines.length, container: container(el),
      overflow: { x: el.scrollWidth - el.clientWidth, y: el.scrollHeight - el.clientHeight }, align: (cs.textAlign === 'start' || cs.textAlign === 'justify') ? 'left' : cs.textAlign === 'end' ? 'right' : cs.textAlign,
      content: { x: er.left + pl - S.left, w: er.width - pl - pr }, runs, lineHeight: lh, ...meta(el) };
  }
  // Nearest painted ancestor (card, panel, chip): text should stay inside it.
  function container(el) {
    for (let e = el.parentElement; e && e !== slide; e = e.parentElement) {
      const cs = getComputedStyle(e);
      const bordered = ['Top', 'Right', 'Bottom', 'Left'].some(s => cs['border' + s + 'Style'] !== 'none' && parseFloat(cs['border' + s + 'Width']) > 0);
      if (visible(cs.backgroundColor) || bordered) return R(e.getBoundingClientRect());
    }
    return null;
  }
  function checkStyle(el, cs) {
    if (cs.backgroundImage && cs.backgroundImage !== 'none') warn('CSS_BACKGROUND_IMAGE_UNSUPPORTED', el);
    if (cs.boxShadow && cs.boxShadow !== 'none') warn('CSS_SHADOW_IGNORED', el);
    if (cs.transform && cs.transform !== 'none') warn('CSS_TRANSFORM_UNSUPPORTED', el);
    if (parseFloat(cs.opacity) < 0.999) warn('CSS_OPACITY_IGNORED_USE_RGBA', el);
    if (cs.overflow === 'hidden' && el !== slide && el.scrollHeight > el.clientHeight + 1) warn('CONTENT_CLIPPED_BY_OVERFLOW', el);
  }
  function boxItem(el) {
    const cs = getComputedStyle(el);
    checkStyle(el, cs);
    const sides = ['Top', 'Right', 'Bottom', 'Left'].map(s => ({ w: parseFloat(cs['border' + s + 'Width']), c: cs['border' + s + 'Color'], st: cs['border' + s + 'Style'] }));
    const borders = sides.map(b => (b.st !== 'none' && b.w > 0 && visible(b.c)) ? { w: b.w, c: b.c } : null);
    if (!visible(cs.backgroundColor) && !borders.some(Boolean)) return null;
    const radius = ['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map(k => parseFloat(cs['border' + k + 'Radius']) || 0);
    return { kind: 'box', ...R(el.getBoundingClientRect()), fill: visible(cs.backgroundColor) ? cs.backgroundColor : null, borders, radius };
  }
  function tableItem(t) {
    const rows = [...t.rows].map(tr => {
      const trBg = getComputedStyle(tr).backgroundColor;
      return { h: tr.getBoundingClientRect().height, cells: [...tr.cells].map(td => {
        const cs = getComputedStyle(td);
        if (td.colSpan > 1 || td.rowSpan > 1) warn('TABLE_SPAN_UNSUPPORTED', td);
        const bb = parseFloat(cs.borderBottomWidth);
        return { w: td.getBoundingClientRect().width, runs: trimRuns(runsOf(td)), font: font(cs),
          align: (cs.textAlign === 'start' || cs.textAlign === 'justify') ? 'left' : cs.textAlign === 'end' ? 'right' : cs.textAlign,
          valign: cs.verticalAlign === 'top' ? 'top' : cs.verticalAlign === 'bottom' ? 'bottom' : 'middle',
          fill: visible(cs.backgroundColor) ? cs.backgroundColor : (visible(trBg) ? trBg : null),
          pad: [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft].map(parseFloat),
          borderBottom: (cs.borderBottomStyle !== 'none' && bb > 0 && visible(cs.borderBottomColor)) ? { w: bb, c: cs.borderBottomColor } : null };
      }) };
    });
    return { kind: 'table', ...R(t.getBoundingClientRect()), rows, ...meta(t) };
  }
  function svgItems(svg) {
    const r = R(svg.getBoundingClientRect());
    const vb = svg.viewBox && svg.viewBox.baseVal;
    const sx = vb && vb.width ? r.w / vb.width : 1, sy = vb && vb.height ? r.h / vb.height : 1;
    for (const el of svg.querySelectorAll('*')) if (el.tagName.toLowerCase() !== 'path') warn('SVG_ELEMENT_IGNORED_USE_PATH', el);
    return [...svg.querySelectorAll('path')].map(p => {
      const cs = getComputedStyle(p);
      return { kind: 'path', ox: r.x, oy: r.y, sx, sy, d: p.getAttribute('d'),
        fill: p.getAttribute('fill') === 'none' || cs.fill === 'none' ? null : cs.fill, fillOpacity: parseFloat(cs.fillOpacity),
        stroke: cs.stroke === 'none' ? null : cs.stroke, strokeWidth: parseFloat(cs.strokeWidth), strokeOpacity: parseFloat(cs.strokeOpacity) };
    });
  }
  function walk(el) {
    const tag = el.tagName.toLowerCase();
    if (tag === 'script' || tag === 'style') return;
    if (getComputedStyle(el).display === 'none' || getComputedStyle(el).visibility === 'hidden') return;
    if (el.hasAttribute('data-asset')) {
      const cs = getComputedStyle(el);
      out.items.push({ kind: 'image', ...R(el.getBoundingClientRect()), asset: el.getAttribute('data-asset'),
        fit: el.getAttribute('data-fit') || 'contain', radius: parseFloat(cs.borderTopLeftRadius) || 0, ...meta(el) });
      return;
    }
    if (el.hasAttribute('data-chart')) {
      let spec = null;
      try { spec = JSON.parse(el.getAttribute('data-chart')); } catch (e) { warn('CHART_SPEC_INVALID_JSON', el); return; }
      out.items.push({ kind: 'chart', ...R(el.getBoundingClientRect()), spec, ...meta(el) }); return;
    }
    if (tag === 'table') { const b = boxItem(el); if (b) out.items.push(b); out.items.push(tableItem(el)); return; }
    if (tag === 'svg') { if (el.hasAttribute('data-native-svg')) out.items.push(...svgItems(el)); else warn('SVG_WITHOUT_NATIVE_MARKER_IGNORED', el); return; }
    if (el !== slide) { const b = boxItem(el); if (b) out.items.push(b); }
    const own = hasOwnText(el);
    if (own) { const t = textItem(el); if (t) out.items.push(t); }
    for (const c of el.children) { if (own && isInline(c)) continue; walk(c); }
  }
  function finish() {
    const pre = document.createElement('pre'); pre.id = '__pptsmith_layout'; pre.style.display = 'none';
    pre.textContent = JSON.stringify(out); document.body.appendChild(pre);
  }
  // Tool-owned preview of native charts: authors only write the data-chart spec.
  function drawChartPreviews() {
    for (const el of slide.querySelectorAll('[data-chart]')) {
      if (el.children.length) continue;
      let spec; try { spec = JSON.parse(el.getAttribute('data-chart')); } catch (e) { continue; }
      const W = el.clientWidth, H = el.clientHeight, cats = spec.categories || [], ser = spec.series || [];
      if (!W || !H || !cats.length || !ser.length) continue;
      const all = ser.flatMap(s => s.values || []);
      const lo = spec.min !== undefined ? spec.min : Math.min(0, ...all), hi = spec.max !== undefined ? spec.max : Math.max(...all) * 1.15 || 1;
      const step = spec.major || (hi - lo) / 4, horiz = spec.type === 'bar';
      const pl = horiz ? 64 : 34, pr = 12, pt = 16, pb = 24, iw = W - pl - pr, ih = H - pt - pb;
      const font = "font-family:" + getComputedStyle(slide).fontFamily.replace(/"/g, "'");
      const col = (s) => '#' + String(s.color || '4B4FD6').replace('#', '');
      const V = (v) => (v - lo) / (hi - lo);
      let g = '';
      for (let t = lo; t <= hi + 1e-9; t += step) {
        if (horiz) { const x = pl + V(t) * iw; g += `<line x1="${x}" x2="${x}" y1="${pt}" y2="${pt + ih}" stroke="#EDEFF5"/><text x="${x}" y="${H - 6}" text-anchor="middle" font-size="9" fill="#A0A4B8" style="${font}">${+t.toFixed(4)}</text>`; }
        else { const y = pt + (1 - V(t)) * ih; g += `<line x1="${pl}" x2="${W - pr}" y1="${y}" y2="${y}" stroke="#EDEFF5"/><text x="${pl - 6}" y="${y + 3}" text-anchor="end" font-size="9" fill="#A0A4B8" style="${font}">${+t.toFixed(4)}</text>`; }
      }
      const n = cats.length, slot = (horiz ? ih : iw) / n, k = ser.length;
      cats.forEach((c, i) => {
        const m = (horiz ? pt : pl) + slot * (i + 0.5);
        g += horiz ? `<text x="${pl - 6}" y="${m + 3}" text-anchor="end" font-size="9" fill="#6B7084" style="${font}">${c}</text>`
                   : `<text x="${m}" y="${H - 6}" text-anchor="middle" font-size="9" fill="#6B7084" style="${font}">${c}</text>`;
      });
      ser.forEach((s, si) => {
        const pts = s.values.map((v, i) => [pl + slot * (i + 0.5), pt + (1 - V(v)) * ih, v]);
        if (spec.type === 'line') {
          if (s.area) g += `<path d="M${pts.map(p => p[0] + ',' + p[1]).join(' L')} L${pts[n - 1][0]},${pt + ih} L${pts[0][0]},${pt + ih} Z" fill="${col(s)}" fill-opacity="0.12"/>`;
          g += `<path d="M${pts.map(p => p[0] + ',' + p[1]).join(' L')}" fill="none" stroke="${col(s)}" stroke-width="2"/>`;
          pts.forEach(p => { g += `<circle cx="${p[0]}" cy="${p[1]}" r="2.6" fill="#fff" stroke="${col(s)}" stroke-width="1.6"/>`;
            if (spec.labels !== false) g += `<text x="${p[0]}" y="${p[1] - 6}" text-anchor="middle" font-size="9" font-weight="700" fill="${col(s)}" style="${font}">${p[2]}</text>`; });
        } else {
          const bw = slot * 0.6 / k;
          s.values.forEach((v, i) => {
            const off = slot * 0.2 + bw * si, len = V(v) * (horiz ? iw : ih);
            if (horiz) { const y = pt + slot * i + off; g += `<rect x="${pl}" y="${y}" width="${len}" height="${bw}" fill="${col(s)}"/>`;
              if (spec.labels !== false) g += `<text x="${pl + len + 4}" y="${y + bw / 2 + 3}" font-size="9" font-weight="700" fill="${col(s)}" style="${font}">${v}</text>`; }
            else { const x = pl + slot * i + off, y = pt + ih - len; g += `<rect x="${x}" y="${y}" width="${bw}" height="${len}" fill="${col(s)}"/>`;
              if (spec.labels !== false) g += `<text x="${x + bw / 2}" y="${y - 4}" text-anchor="middle" font-size="9" font-weight="700" fill="${col(s)}" style="${font}">${v}</text>`; }
          });
        }
      });
      el.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}">${g}</svg>`;
    }
  }
  try { drawChartPreviews(); } catch (e) { out.warnings.push({ code: 'CHART_PREVIEW_FAILED', at: String(e) }); }
  document.fonts.ready.then(() => { try { walk(slide); } catch (e) { out.error = 'EXTRACT_FAILED: ' + e; } finish(); });
})();
