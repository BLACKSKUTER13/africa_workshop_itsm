(function() {
    const canvas = document.getElementById('bg-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    let width, height, dpr;

    function resize() {
        dpr = window.devicePixelRatio || 1;
        width = window.innerWidth;
        height = window.innerHeight;
        canvas.width = width * dpr;
        canvas.height = height * dpr;
        canvas.style.width = width + 'px';
        canvas.style.height = height + 'px';
        ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    const orbs = [];
    const ORB_COUNT = 14;

    function initOrbs() {
        orbs.length = 0;
        for (let i = 0; i < ORB_COUNT; i++) {
            orbs.push({
                x: Math.random() * width,
                y: Math.random() * height,
                r: 120 + Math.random() * 200,
                dx: (Math.random() - 0.5) * 0.12,
                dy: (Math.random() - 0.5) * 0.12,
                hue: 190 + Math.random() * 140,
                alpha: 0.1 + Math.random() * 0.2
            });
        }
    }

    function step() {
        ctx.clearRect(0, 0, width, height);

        ctx.fillStyle = '#020617';
        ctx.fillRect(0, 0, width, height);

        for (const orb of orbs) {
            orb.x += orb.dx;
            orb.y += orb.dy;

            if (orb.x - orb.r > width) orb.x = -orb.r;
            if (orb.x + orb.r < 0) orb.x = width + orb.r;
            if (orb.y - orb.r > height) orb.y = -orb.r;
            if (orb.y + orb.r < 0) orb.y = height + orb.r;

            const gradient = ctx.createRadialGradient(
                orb.x, orb.y, 0,
                orb.x, orb.y, orb.r
            );
            gradient.addColorStop(0, `hsla(${orb.hue}, 95%, 70%, ${orb.alpha})`);
            gradient.addColorStop(0.3, `hsla(${orb.hue}, 85%, 60%, ${orb.alpha * 0.7})`);
            gradient.addColorStop(1, 'rgba(15, 23, 42, 0)');

            ctx.fillStyle = gradient;
            ctx.beginPath();
            ctx.arc(orb.x, orb.y, orb.r, 0, Math.PI * 2);
            ctx.fill();
        }

        requestAnimationFrame(step);
    }

    resize();
    initOrbs();
    step();

    window.addEventListener('resize', () => {
        resize();
        initOrbs();
    });
})();
