(() => {
  let now = 0;
  const epoch = 1767225600000;
  let queue = [];
  let nextId = 1;
  const timers = new Map();
  const realSetTimeout = window.setTimeout.bind(window);
  const realClearTimeout = window.clearTimeout.bind(window);

  performance.now = () => now;
  Date.now = () => epoch + now;
  const RealDate = Date;
  window.Date = class extends RealDate {
    constructor(...a) { a.length ? super(...a) : super(epoch + now); }
    static now() { return epoch + now; }
  };

  window.requestAnimationFrame = cb => { const id = nextId++; queue.push({ id, cb }); return id; };
  window.cancelAnimationFrame = id => { queue = queue.filter(q => q.id !== id); };

  window.setTimeout = (cb, ms = 0, ...args) => {
    if (!window.__clockRunning) return realSetTimeout(cb, ms, ...args);
    const id = nextId++;
    timers.set(id, { at: now + Math.max(0, ms), cb: () => cb(...args) });
    return id;
  };
  window.clearTimeout = id => { timers.has(id) ? timers.delete(id) : realClearTimeout(id); };
  window.setInterval = (cb, ms = 0, ...args) => {
    const id = nextId++;
    const tick = () => { cb(...args); if (timers.has(id)) timers.set(id, { at: now + Math.max(1, ms), cb: tick }); };
    timers.set(id, { at: now + Math.max(1, ms), cb: tick });
    return id;
  };
  window.clearInterval = id => timers.delete(id);

  window.__clockRunning = false;
  window.__clock = {
    now: () => now,
    start() { window.__clockRunning = true; },
    async advance(ms) {
      const target = now + ms;
      for (;;) {
        let next = null;
        for (const [id, t] of timers) if (t.at <= target && (!next || t.at < next[1].at)) next = [id, t];
        if (!next) break;
        now = Math.max(now, next[1].at);
        timers.delete(next[0]);
        next[1].cb();
      }
      now = target;
      const due = queue;
      queue = [];
      for (const q of due) q.cb(now);
      document.getAnimations?.().forEach(a => { a.pause(); a.currentTime = (a.currentTime || 0) + ms; });
      for (const v of document.querySelectorAll('video')) { v.pause(); v.currentTime = now / 1000; }
      await new Promise(r => realSetTimeout(r, 0));
    },
  };
})();
