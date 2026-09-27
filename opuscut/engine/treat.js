const TREAT = (() => {
  const scratch = document.createElement('canvas');
  const sctx = scratch.getContext('2d', { willReadFrequently: true });
  const BAYER = [0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5].map(v => (v + 0.5) / 16);

  function pixels(src, w, h) {
    scratch.width = w; scratch.height = h;
    sctx.clearRect(0, 0, w, h);
    sctx.drawImage(src, 0, 0, w, h);
    return sctx.getImageData(0, 0, w, h);
  }

  function hex(c) { return [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16)); }
  function lum(d, i) { return (d[i] * 0.299 + d[i + 1] * 0.587 + d[i + 2] * 0.114) / 255; }

  function dither(g, src, x, y, w, h, { cell = 3, ink = '#111111', paper = null, contrast = 1.2 } = {}) {
    const cw = Math.max(1, Math.round(w / cell)), ch = Math.max(1, Math.round(h / cell));
    const img = pixels(src, cw, ch), d = img.data, a = hex(ink), p = paper ? hex(paper) : null;
    for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
      const k = (j * cw + i) * 4;
      if (d[k + 3] < 8) continue;
      const v = Math.min(1, Math.max(0, (lum(d, k) - 0.5) * contrast + 0.5));
      const on = v < BAYER[(j & 3) * 4 + (i & 3)];
      const c = on ? a : p;
      if (c) { d[k] = c[0]; d[k + 1] = c[1]; d[k + 2] = c[2]; d[k + 3] = 255; } else d[k + 3] = 0;
    }
    sctx.putImageData(img, 0, 0);
    g.save(); g.imageSmoothingEnabled = false; g.drawImage(scratch, 0, 0, cw, ch, x, y, w, h); g.restore();
  }

  function halftone(g, src, x, y, w, h, { cell = 10, ink = '#111111', angle = 0.26, scale = 0.72 } = {}) {
    const cw = Math.max(1, Math.round(w / cell)), ch = Math.max(1, Math.round(h / cell));
    const d = pixels(src, cw, ch).data;
    g.save(); g.fillStyle = ink; g.translate(x + w / 2, y + h / 2); g.rotate(angle); g.translate(-w / 2, -h / 2);
    for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
      const k = (j * cw + i) * 4;
      if (d[k + 3] < 8) continue;
      const r = Math.sqrt(1 - lum(d, k)) * cell * scale;
      if (r < 0.3) continue;
      g.beginPath(); g.arc((i + 0.5) * cell, (j + 0.5) * cell, r, 0, 6.2832); g.fill();
    }
    g.restore();
  }

  function duotone(g, src, x, y, w, h, { dark = '#101014', light = '#f4f1ea' } = {}) {
    const img = pixels(src, Math.round(w), Math.round(h)), d = img.data, a = hex(dark), b = hex(light);
    for (let k = 0; k < d.length; k += 4) {
      const t = lum(d, k);
      d[k] = a[0] + (b[0] - a[0]) * t; d[k + 1] = a[1] + (b[1] - a[1]) * t; d[k + 2] = a[2] + (b[2] - a[2]) * t;
    }
    sctx.putImageData(img, 0, 0);
    g.drawImage(scratch, 0, 0, Math.round(w), Math.round(h), x, y, w, h);
  }

  function sketch(g, src, x, y, w, h, { ink = '#1a1a1a', threshold = 0.12, detail = 2 } = {}) {
    const cw = Math.max(2, Math.round(w / detail)), ch = Math.max(2, Math.round(h / detail));
    const img = pixels(src, cw, ch), d = img.data, L = new Float32Array(cw * ch), a = hex(ink);
    for (let k = 0, n = 0; k < d.length; k += 4, n++) L[n] = lum(d, k);
    for (let j = 0; j < ch; j++) for (let i = 0; i < cw; i++) {
      const n = j * cw + i, k = n * 4;
      const gx = (L[n + (i < cw - 1 ? 1 : 0)] - L[n - (i > 0 ? 1 : 0)]);
      const gy = (L[n + (j < ch - 1 ? cw : 0)] - L[n - (j > 0 ? cw : 0)]);
      const e = Math.hypot(gx, gy);
      if (e > threshold) { d[k] = a[0]; d[k + 1] = a[1]; d[k + 2] = a[2]; d[k + 3] = Math.min(255, e * 900); } else d[k + 3] = 0;
    }
    sctx.putImageData(img, 0, 0);
    g.drawImage(scratch, 0, 0, cw, ch, x, y, w, h);
  }

  return { dither, halftone, duotone, sketch };
})();
