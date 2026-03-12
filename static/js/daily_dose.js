(function () {
    const contentEl = document.getElementById('dailyDoseContent');
    const loadingEl = document.getElementById('dailyDoseLoading');
    const cardEl = document.getElementById('dailyDoseCard');
    const errorEl = document.getElementById('dailyDoseError');
    const errorMessageEl = document.getElementById('dailyDoseErrorMessage');
    const dayBadge = document.getElementById('dayBadge');
    const dateBadge = document.getElementById('dateBadge');
    const themeBadge = document.getElementById('themeBadge');
    const doseTitle = document.getElementById('doseTitle');
    const doseSource = document.getElementById('doseSource');
    const doseQuestion = document.getElementById('doseQuestion');
    const doseMessage = document.getElementById('doseMessage');
    const progressFill = document.getElementById('dailyDoseProgressFill');
    const progressText = document.getElementById('dailyDoseProgressText');
    const sidebarLabel = document.getElementById('dailyDoseSidebarLabel');
    const btnToday = document.getElementById('btnToday');
    const btnCopy = document.getElementById('btnCopy');
    const btnShare = document.getElementById('btnShare');
    const themeToggle = document.getElementById('themeToggle');
    const themeIcon = document.getElementById('themeIcon');

    const TOTAL_DAYS = 200;

    function getDayFromQuery() {
        const params = new URLSearchParams(window.location.search);
        const day = params.get('day');
        return day ? parseInt(day, 10) : null;
    }

    function setLoading(show) {
        loadingEl.classList.toggle('hidden', !show);
        cardEl.classList.toggle('hidden', show);
        errorEl.classList.add('hidden');
    }

    function setError(message) {
        loadingEl.classList.add('hidden');
        cardEl.classList.add('hidden');
        errorEl.classList.remove('hidden');
        errorMessageEl.textContent = message || 'Failed to load dose.';
    }

    function applyTheme() {
        const theme = document.documentElement.getAttribute('data-theme') || 'light';
        themeIcon.className = theme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
        themeToggle.querySelector('span').textContent = theme === 'dark' ? 'Light' : 'Dark';
    }

    function toggleTheme() {
        const current = document.documentElement.getAttribute('data-theme') || 'light';
        const next = current === 'dark' ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try {
            localStorage.setItem('theme', next);
        } catch (e) {}
        applyTheme();
    }

    function initTheme() {
        try {
            const saved = localStorage.getItem('theme');
            if (saved === 'dark' || saved === 'light') {
                document.documentElement.setAttribute('data-theme', saved);
            }
        } catch (e) {}
        applyTheme();
    }

    function updateProgress(day) {
        const pct = Math.min(100, (day / TOTAL_DAYS) * 100);
        progressFill.style.width = pct + '%';
        progressText.textContent = day + ' / ' + TOTAL_DAYS;
        sidebarLabel.textContent = 'Day ' + day + ' of ' + TOTAL_DAYS;
    }

    function renderDose(data) {
        const day = data.day;
        dayBadge.textContent = 'Day ' + day;
        dateBadge.textContent = data.date || '';
        themeBadge.textContent = data.theme || '';
        doseTitle.textContent = data.title || '';
        doseSource.textContent = data.source ? 'From: ' + data.source : '';
        doseQuestion.textContent = data.question ? 'Reflection: ' + data.question : '';
        doseMessage.textContent = data.message || '';
        updateProgress(day);
        cardEl.dataset.day = day;
    }

    function loadDose(dayParam) {
        setLoading(true);
        const url = dayParam != null
            ? '/api/daily-dose?day=' + encodeURIComponent(dayParam)
            : '/api/daily-dose';
        fetch(url)
            .then(function (res) { return res.json(); })
            .then(function (json) {
                if (json.success && json.data) {
                    renderDose(json.data);
                    setLoading(false);
                } else {
                    setError(json.error || json.message || 'Failed to load dose.');
                }
            })
            .catch(function (err) {
                setError(err.message || 'Network error.');
            });
    }

    function goToToday() {
        const params = new URLSearchParams(window.location.search);
        params.delete('day');
        const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
        window.location.href = newUrl;
    }

    function copyDose() {
        const msg = doseMessage.textContent;
        if (!msg) return;
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(msg).then(function () {
                btnCopy.querySelector('span').textContent = 'Copied!';
                setTimeout(function () { btnCopy.querySelector('span').textContent = 'Copy'; }, 2000);
            }).catch(function () { fallbackCopy(); });
        } else {
            fallbackCopy();
        }
    }

    function fallbackCopy() {
        const sel = window.getSelection();
        const range = document.createRange();
        range.selectNodeContents(doseMessage);
        sel.removeAllRanges();
        sel.addRange(range);
        try {
            document.execCommand('copy');
            btnCopy.querySelector('span').textContent = 'Copied!';
            setTimeout(function () { btnCopy.querySelector('span').textContent = 'Copy'; }, 2000);
        } catch (e) {}
        sel.removeAllRanges();
    }

    function shareDose() {
        const title = doseTitle.textContent;
        const text = doseMessage.textContent;
        if (navigator.share && title && text) {
            navigator.share({
                title: 'Daily Dose: ' + title,
                text: text,
                url: window.location.href
            }).catch(function () {});
        } else {
            copyDose();
        }
    }

    btnToday.addEventListener('click', goToToday);
    btnCopy.addEventListener('click', copyDose);
    btnShare.addEventListener('click', shareDose);
    themeToggle.addEventListener('click', toggleTheme);

    initTheme();
    var dayFromQuery = getDayFromQuery();
    loadDose(dayFromQuery);
})();
