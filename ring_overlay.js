/* Ring overlay: circle area ~ population, arc length ~ lighting %. */
(function () {
  const POP_MAX = window.llmapsData?.meta?.pop_max ?? 1;
  const R_MIN = 6;
  const R_MAX = 58;
  const AREA_SCALE = 5; // площадь круга / 5 => радиус / sqrt(5)
  const R_SCALE = 1 / Math.sqrt(AREA_SCALE);
  const RING_COLOR = "#FFCC08";
  const RING_GLOW = "rgba(255, 204, 8, 0.85)";

  function popRadius(pop) {
    const p = Math.max(0, Number(pop) || 0);
    if (p <= 0) return R_MIN * R_SCALE;
    const t = Math.sqrt(p / POP_MAX);
    return (R_MIN + t * (R_MAX - R_MIN)) * R_SCALE;
  }

  function drawRing(ctx, x, y, radius, pct) {
    const track = "rgba(255, 204, 8, 0.12)";
    const lineW = Math.max(1.2, radius * 0.085);
    const start = -Math.PI / 2;
    const sweep = (Math.max(0, Math.min(100, pct)) / 100) * Math.PI * 2;

    ctx.save();
    ctx.lineCap = "round";

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(255, 204, 8, 0.05)";
    ctx.fill();

    ctx.beginPath();
    ctx.arc(x, y, radius, 0, Math.PI * 2);
    ctx.strokeStyle = track;
    ctx.lineWidth = lineW;
    ctx.stroke();

    if (sweep > 0.001) {
      ctx.shadowColor = RING_GLOW;
      ctx.shadowBlur = Math.max(10, radius * 0.45);
      ctx.beginPath();
      ctx.arc(x, y, radius, start, start + sweep);
      ctx.strokeStyle = RING_COLOR;
      ctx.lineWidth = lineW;
      ctx.stroke();

      ctx.shadowBlur = Math.max(16, radius * 0.65);
      ctx.globalAlpha = 0.55;
      ctx.beginPath();
      ctx.arc(x, y, radius, start, start + sweep);
      ctx.strokeStyle = RING_COLOR;
      ctx.lineWidth = lineW * 2;
      ctx.stroke();
    }

    ctx.restore();
  }

  function mountCanvas(map) {
    const host =
      document.getElementById("krasnodar-ring-host") ||
      document.getElementById("map-root");
    if (!host || host.querySelector(".krasnodar-ring-canvas")) return;

    const canvas = document.createElement("canvas");
    canvas.className = "krasnodar-ring-canvas";
    canvas.setAttribute("aria-hidden", "true");
    host.appendChild(canvas);

    const ctx = canvas.getContext("2d");
    let raf = 0;

    function sizeTarget() {
      const root = document.getElementById("map-root");
      return root || host;
    }

    function resize() {
      const box = sizeTarget();
      const w = box.clientWidth;
      const h = box.clientHeight;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.floor(w * dpr);
      canvas.height = Math.floor(h * dpr);
      canvas.style.width = w + "px";
      canvas.style.height = h + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    function render() {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const box = sizeTarget();
        const w = box.clientWidth;
        const h = box.clientHeight;
        ctx.clearRect(0, 0, w, h);
        const feats = window.llmapsData?.points?.features;
        if (!feats) return;
        for (let i = 0; i < feats.length; i++) {
          const f = feats[i];
          const c = f.geometry.coordinates;
          const p = map.project([c[0], c[1]]);
          if (p.x < -100 || p.y < -100 || p.x > w + 100 || p.y > h + 100) continue;
          const props = f.properties || {};
          const r = popRadius(props.pop);
          drawRing(ctx, p.x, p.y, r, props.light_pct ?? 0);
        }
      });
    }

    resize();
    render();
    map.on("move", render);
    map.on("zoom", render);
    map.on("resize", () => {
      resize();
      render();
    });
    map.on("load", render);
    map.on("idle", render);
    window.addEventListener("resize", () => {
      resize();
      render();
    });
  }

  function boot(map) {
    if (!map) return;
    mountCanvas(map);
  }

  function tryBoot() {
    const map = window.llmaps_map || window._llmapsReadyMap;
    if (map) {
      boot(map);
      return true;
    }
    return false;
  }

  if (typeof window.llmapsOnLayersReady === "function") {
    window.llmapsOnLayersReady(boot);
  }

  if (!tryBoot()) {
    const poll = window.setInterval(() => {
      if (tryBoot()) window.clearInterval(poll);
    }, 150);
    window.setTimeout(() => window.clearInterval(poll), 20000);
  }
})();
