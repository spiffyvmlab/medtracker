document.addEventListener("DOMContentLoaded", function() {
    // Theme CSS blocks
    const darkCSS = `
        body { background: #181818; color: #eee; }
        th, td { border: 1px solid #444; }
        th { background: #222; }
        a, input[type="submit"] { color: #8cf; }
        .server-time { color: #aaa; }
        .toggle-btn { background: #333; color: #eee; }
        tr { border-bottom: 2px solid #222; }
    `;
    const lightCSS = `
        body { background: #fff; color: #222; }
        th, td { border: 1px solid #ccc; }
        th { background: #f0f0f0; }
        a, input[type="submit"] { color: #06c; }
        .server-time { color: #555; }
        .toggle-btn { background: #eee; color: #222; }
        tr { border-bottom: 2px solid #eee; }
    `;
    // Add theme-style tag if not present
    let styleTag = document.getElementById('theme-style');
    if (!styleTag) {
        styleTag = document.createElement('style');
        styleTag.id = 'theme-style';
        document.head.appendChild(styleTag);
    }
    const toggleBtn = document.getElementById('theme-toggle');
    let darkMode = true;
    function setTheme(dark) {
        styleTag.innerHTML = dark ? darkCSS : lightCSS;
        if (toggleBtn) {
            toggleBtn.textContent = dark ? "Switch to Light Mode" : "Switch to Dark Mode";
        }
        darkMode = dark;
        localStorage.setItem('medtracker-theme', dark ? 'dark' : 'light');
    }
    // Load theme from localStorage
    const savedTheme = localStorage.getItem('medtracker-theme');
    if (savedTheme === 'light') {
        setTheme(false);
    } else {
        setTheme(true);
    }
    if (toggleBtn) {
        toggleBtn.addEventListener('click', function() {
            setTheme(!darkMode);
        });
    }

    // Convert all UTC datetimes to local time
    document.querySelectorAll('.utc-datetime').forEach(function(el) {
        let utcString = el.dataset.utc;
        if (utcString) {
            let date = new Date(utcString);
            if (!isNaN(date)) {
                el.textContent = date.toLocaleString();
            }
        }
    });
    // Convert server time
    let st = document.querySelector('.server-time');
    if (st && st.dataset.utc) {
        let date = new Date(st.dataset.utc);
        if (!isNaN(date)) {
            st.textContent = "Your time: " + date.toLocaleString();
        }
    }
});