/* ==========================================================================
   INTERNFLOW — CORE ENGINE CONTROLLER & UI WORKSPACE
   SaaS Architecture: Zero Emojis, Crisp SVGs, Real-Time Filtering,
   Deterministic Match Scoring & SMTP Automation.
   ========================================================================== */

/* =========================================
   ELEMENT SELECTORS
   ========================================= */

const loginPage = document.getElementById("loginPage");
const preferencesPage = document.getElementById("preferencesPage");
const dashboardPage = document.getElementById("dashboardPage");

const loginForm = document.getElementById("loginForm");
const preferencesForm = document.getElementById("preferencesForm");

const logoutBtn = document.getElementById("logoutBtn");
const dashboardLogout = document.getElementById("dashboardLogout");
const editPreferences = document.getElementById("editPreferences");


/* =========================================
   SVG ICON LIBRARY (CRISP, NON-EMOJI)
   ========================================= */

const ICONS = {
    check: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"></polyline></svg>`,
    dash: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="5" y1="12" x2="19" y2="12"></line></svg>`,
    location: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"></path><circle cx="12" cy="10" r="3"></circle></svg>`,
    stipend: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="6" y1="3" x2="18" y2="3"></line><line x1="6" y1="8" x2="18" y2="8"></line><path d="M6 3h5a4 4 0 0 1 0 8H6"></path><path d="M10 11l6 10"></path></svg>`,
    calendar: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>`,
    clock: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg>`,
    graduation: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 10v6M2 10l10-5 10 5-10 5z"></path><path d="M6 12v5c3 3 9 3 12 0v-5"></path></svg>`,
    bookmarkOutline: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
    bookmarkFilled: `<svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21l-7-5-7 5V5a2 2 0 0 1 2-2h10a2 2 0 0 1 2 2z"></path></svg>`,
    copy: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`,
    externalLink: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path><polyline points="15 3 21 3 21 9"></polyline><line x1="10" y1="14" x2="21" y2="3"></line></svg>`,
    moon: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`,
    sun: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`,
    eye: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"></path><circle cx="12" cy="12" r="3"></circle></svg>`,
    eyeOff: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"></path><line x1="1" y1="1" x2="23" y2="23"></line></svg>`,
    refresh: `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"></path></svg>`,
    info: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="16" x2="12" y2="12"></line><line x1="12" y1="8" x2="12.01" y2="8"></line></svg>`,
    alert: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"></path><line x1="12" y1="9" x2="12" y2="13"></line><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>`
};


/* =========================================
   API RESOLUTION
   ========================================= */

const LOCAL_API_URL = "http://127.0.0.1:5000";
const CLOUD_API_URL = "https://intern-flow-ckh9.onrender.com";

let resolvedApiUrl = null;

async function getApiUrl() {
    if (resolvedApiUrl) {
        return resolvedApiUrl;
    }

    // 1. If currently served via HTTP/HTTPS in browser, always use current origin directly
    if (typeof window !== "undefined" && window.location && window.location.origin && window.location.origin !== "null" && window.location.protocol.startsWith("http")) {
        resolvedApiUrl = window.location.origin;
        return resolvedApiUrl;
    }

    // 2. Fallback when opened as static file://
    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 2000);

        const res = await fetch(`${LOCAL_API_URL}/health`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (res.ok) {
            resolvedApiUrl = LOCAL_API_URL;
            return resolvedApiUrl;
        }
    } catch {
        // Fall back to cloud on error
    }

    resolvedApiUrl = CLOUD_API_URL;
    return resolvedApiUrl;
}


/* =========================================
   USER STORAGE
   ========================================= */

const STORAGE_KEY = "internflow_current_user";

function getUser() {
    try {
        const data = localStorage.getItem(STORAGE_KEY);
        return data ? JSON.parse(data) : null;
    } catch {
        return null;
    }
}

function saveUser(user) {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(user));
}

function clearUser() {
    localStorage.removeItem(STORAGE_KEY);
}


/* =========================================
   PAGE ROUTING
   ========================================= */

function showPage(page) {
    document.querySelectorAll(".page").forEach(function(item) {
        item.classList.remove("active");
    });
    if (page) {
        page.classList.add("active");
        window.scrollTo({ top: 0, behavior: "smooth" });
    }
}


/* =========================================
   AUTH & LOGIN HANDLER
   ========================================= */

loginForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const name = document.getElementById("loginName").value.trim();
    const email = document.getElementById("loginEmail").value.trim();

    if (!email) {
        showToast("Please enter a valid email", "warning");
        return;
    }

    try {
        const apiUrl = await getApiUrl();
        const response = await fetch(`${apiUrl}/preferences?email=${encodeURIComponent(email)}`);

        if (response.ok) {
            const data = await response.json();
            if ((data.found || data.exists) && data.preferences) {
                // Signing is already done: directly show dashboard and internships!
                const user = {
                    name: name || data.preferences.name || "Candidate",
                    email: email,
                    preferences: data.preferences
                };
                saveUser(user);
                loadDashboard(user);
                showPage(dashboardPage);
                searchInternships(user);
                showToast(`Welcome back, ${user.name}!`, "success");
                return;
            }
        }
    } catch (err) {
        console.warn("Could not check backend preferences:", err);
    }

    // First time signing in: preferences must be asked first!
    const user = {
        name: name,
        email: email,
        preferences: null
    };

    saveUser(user);
    document.getElementById("preferenceEmail").textContent = email;
    preferencesForm.reset();
    showPage(preferencesPage);
    showToast("Welcome! Please configure your internship preferences first.", "info");
});


/* =========================================
   LOCATION PARSER
   ========================================= */

function getSelectedLocations() {
    const checked = document.querySelectorAll('.location-grid input[type="checkbox"]:checked');
    const locations = [];
    checked.forEach(item => locations.push(item.value));

    const custom = document.getElementById("customLocation").value.trim();
    if (custom) {
        locations.push(custom);
    }

    return locations;
}


/* =========================================
   SEARCH INTERNSHIPS (AI PIPELINE)
   ========================================= */

async function searchInternships(user) {
    const currentUser = user || getUser();
    const resultsContainer = document.getElementById("internshipResults");
    const resultsCount = document.getElementById("resultsCount");

    if (!resultsContainer || !resultsCount) return;

    if (!currentUser || !currentUser.preferences) {
        resultsCount.textContent = "Preferences missing";
        resultsContainer.innerHTML = `
            <div class="results-message">
                <p>Please configure your internship preferences to begin search.</p>
            </div>
        `;
        return;
    }

    currentUser.isFirstTime = false;
    currentUser.hasSearched = true;
    saveUser(currentUser);

    resultsCount.textContent = "Searching...";

    resultsContainer.innerHTML = `
        <div class="skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line btn"></div>
        </div>
        <div class="skeleton-card">
            <div class="skeleton-line short"></div>
            <div class="skeleton-line medium"></div>
            <div class="skeleton-line long"></div>
            <div class="skeleton-line btn"></div>
        </div>
    `;

    const preferences = currentUser.preferences;

    try {
        const apiUrl = await getApiUrl();
        const response = await fetch(`${apiUrl}/search-internships`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: currentUser.email,
                student_skills: preferences.student_skills,
                preferred_domain: preferences.preferred_domain,
                locations: preferences.locations,
                minimum_stipend: preferences.minimum_stipend
            })
        });

        if (!response.ok) {
            throw new Error(`Server returned status ${response.status}`);
        }

        const data = await response.json();
        displayInternships(data.internships || [], currentUser);

    } catch (error) {
        console.error("Internship search failed:", error);
        resultsCount.textContent = "Search failed";
        const isNetworkError = error instanceof TypeError || (error.message && error.message.includes("Failed to fetch"));

        resultsContainer.innerHTML = `
            <div class="results-message search-error-banner">
                <div class="search-error-title-row">
                    <span class="search-error-icon">${ICONS.alert}</span>
                    <strong class="search-error-title">${isNetworkError ? "Backend Connection Notice" : "Search Pipeline Notice"}</strong>
                </div>
                <p class="search-error-desc">
                    ${isNetworkError ? "Unable to communicate with the local search service on port 5000:" : escapeHTML(error.message || "An unexpected error occurred during search.")}
                </p>
                ${isNetworkError ? `
                    <pre class="search-error-code">python backend.py</pre>
                    <p class="search-error-desc">
                        Ensure the daemon is running, then access <a href="http://localhost:5000" target="_blank" class="search-error-link">http://localhost:5000</a>.
                    </p>
                ` : ""}
                <button type="button" id="retrySearchBtn" class="secondary-btn btn-sm" style="margin-top: 14px;">
                    ${ICONS.refresh}
                    <span>Retry Search</span>
                </button>
            </div>
        `;

        const retryBtn = document.getElementById("retrySearchBtn");
        if (retryBtn) {
            retryBtn.onclick = () => searchInternships(currentUser);
        }
    }
}


/* =========================================
   SAVED BOOKMARKS & TOAST NOTIFICATION SYSTEM
   ========================================= */

const SAVED_URLS_KEY = "internflow_saved_urls";

function getSavedUrls() {
    try {
        return new Set(JSON.parse(localStorage.getItem(SAVED_URLS_KEY) || "[]"));
    } catch {
        return new Set();
    }
}

function toggleSaveUrl(url) {
    const saved = getSavedUrls();
    let isNowSaved = false;
    if (saved.has(url)) {
        saved.delete(url);
        isNowSaved = false;
    } else {
        saved.add(url);
        isNowSaved = true;
    }
    localStorage.setItem(SAVED_URLS_KEY, JSON.stringify(Array.from(saved)));
    updateSavedCountBadge();
    return isNowSaved;
}

function updateSavedCountBadge() {
    const badge = document.getElementById("savedCountBadge");
    if (badge) {
        badge.textContent = getSavedUrls().size;
    }
}

function showToast(message, type = "info", duration = 3000) {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const icon = type === "success" ? ICONS.check : (type === "warning" || type === "error" ? ICONS.alert : ICONS.info);

    toast.innerHTML = `
        <span class="toast-icon">${icon}</span>
        <span class="toast-msg">${escapeHTML(message)}</span>
    `;
    container.appendChild(toast);

    setTimeout(() => {
        toast.classList.add("toast-leave");
        setTimeout(() => toast.remove(), 240);
    }, duration);
}


/* =========================================
   FILTER, SORT & INTERNSHIP CARD RENDERER
   ========================================= */

let currentInternshipsData = [];
let currentActiveFilter = "all";

function displayInternships(internships, user = null) {
    currentInternshipsData = Array.isArray(internships) ? internships : [];
    renderFilteredInternships(user);
}

function renderFilteredInternships(user = null) {
    const currentUser = user || getUser();
    const resultsContainer = document.getElementById("internshipResults");
    const resultsCount = document.getElementById("resultsCount");

    if (!resultsContainer || !resultsCount) return;

    const searchKeyword = (document.getElementById("internshipSearchInput")?.value || "").toLowerCase().trim();
    const sortOption = document.getElementById("sortSelector")?.value || "match-desc";
    const savedUrls = getSavedUrls();

    let filtered = [...currentInternshipsData];

    // 1. Text Search Filter
    if (searchKeyword) {
        filtered = filtered.filter(item => {
            const comp = (item.company || "").toLowerCase();
            const role = (item.role || "").toLowerCase();
            const loc = (item.location || "").toLowerCase();
            const skills = Array.isArray(item.skills) ? item.skills.join(" ").toLowerCase() : (item.skills || "").toLowerCase();
            return comp.includes(searchKeyword) || role.includes(searchKeyword) || loc.includes(searchKeyword) || skills.includes(searchKeyword);
        });
    }

    // 2. Pill Filter
    if (currentActiveFilter === "high-match") {
        filtered = filtered.filter(item => (item.match_percentage || 0) >= 80);
    } else if (currentActiveFilter === "remote") {
        filtered = filtered.filter(item => (item.location || "").toLowerCase().includes("remote"));
    } else if (currentActiveFilter === "paid") {
        filtered = filtered.filter(item => {
            const st = (item.stipend || "").toLowerCase();
            return st && !st.includes("unpaid") && !st.includes("0") && st !== "not specified";
        });
    } else if (currentActiveFilter === "saved") {
        filtered = filtered.filter(item => {
            const url = item.application_url || item.source_url || "";
            return savedUrls.has(url);
        });
    }

    // 3. Sorting
    if (sortOption === "match-desc") {
        filtered.sort((a, b) => (b.match_percentage || 0) - (a.match_percentage || 0));
    } else if (sortOption === "company-asc") {
        filtered.sort((a, b) => (a.company || "").localeCompare(b.company || ""));
    } else if (sortOption === "deadline") {
        filtered.sort((a, b) => {
            const d1 = a.deadline ? new Date(a.deadline).getTime() : Infinity;
            const d2 = b.deadline ? new Date(b.deadline).getTime() : Infinity;
            return d1 - d2;
        });
    }

    resultsCount.textContent = `${filtered.length} Discovered`;

    if (filtered.length === 0) {
        resultsContainer.innerHTML = `
            <div class="results-empty-state">
                <h4>No opportunities match this criteria</h4>
                <p>Adjust your filter pills or search terms to broaden the feed.</p>
                <button type="button" class="secondary-btn btn-sm" id="resetFiltersActionBtn">
                    Reset Filter
                </button>
            </div>
        `;
        document.getElementById("resetFiltersActionBtn")?.addEventListener("click", () => {
            const input = document.getElementById("internshipSearchInput");
            if (input) input.value = "";
            const clearBtn = document.getElementById("clearSearchBtn");
            if (clearBtn) clearBtn.style.display = "none";
            document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            document.querySelector('.filter-pill[data-filter="all"]')?.classList.add("active");
            currentActiveFilter = "all";
            renderFilteredInternships(currentUser);
        });
        return;
    }

    resultsContainer.innerHTML = "";

    filtered.forEach(internship => {
        const card = createInternshipCardElement(internship, currentUser);
        resultsContainer.appendChild(card);
    });
}

function createInternshipCardElement(internship, currentUser) {
    const card = document.createElement("article");
    card.className = "internship-card";

    const company = internship.company || "Company not specified";
    const role = internship.role || "Internship Opportunity";
    const location = internship.location || "Location not specified";
    const stipend = internship.stipend || "Stipend not specified";
    const match = internship.match_percentage;
    const applicationUrl = internship.application_url || internship.source_url || "#";
    const companyInitial = company.trim().charAt(0).toUpperCase() || "I";

    const savedUrls = getSavedUrls();
    const isSaved = applicationUrl !== "#" && savedUrls.has(applicationUrl);

    const skills = Array.isArray(internship.skills)
        ? internship.skills.join(", ")
        : internship.skills || "Not specified";

    const matchedList = Array.isArray(internship.matched_skills)
        ? internship.matched_skills
        : (internship.matched_skills ? [internship.matched_skills] : []);

    const missingList = Array.isArray(internship.missing_skills)
        ? internship.missing_skills
        : (internship.missing_skills ? [internship.missing_skills] : []);

    const matchedSkills = matchedList.length > 0
        ? matchedList.join(", ")
        : (currentUser?.preferences?.preferred_domain ? `Aligned with ${currentUser.preferences.preferred_domain}` : "Domain aligned");

    const missingSkills = missingList.length > 0
        ? missingList.join(", ")
        : "None (All criteria met)";

    const isHighMatch = (match !== undefined && match !== null && match >= 80);

    card.innerHTML = `
        <div class="card-head">
            <div class="card-company-group">
                <div class="company-monogram">${escapeHTML(companyInitial)}</div>
                <div class="card-title-group">
                    <div class="company-name-row">
                        <span class="company-title">${escapeHTML(company)}</span>
                        <span class="verified-indicator" title="Verified opening">${ICONS.check} Verified</span>
                    </div>
                    <h3 class="role-title">${escapeHTML(role)}</h3>
                </div>
            </div>

            <div class="match-badge ${isHighMatch ? 'high-match' : 'standard-match'}">
                ${match !== undefined && match !== null ? `${match}% Match` : "Aligned"}
            </div>
        </div>

        <div class="card-meta-chips">
            <span class="meta-chip">${ICONS.location} ${escapeHTML(location)}</span>
            <span class="meta-chip">${ICONS.stipend} ${escapeHTML(stipend)}</span>
            ${internship.deadline ? `<span class="meta-chip deadline-chip">${ICONS.calendar} ${escapeHTML(internship.deadline)}</span>` : `<span class="meta-chip">${ICONS.calendar} Rolling</span>`}
            ${internship.duration ? `<span class="meta-chip">${ICONS.clock} ${escapeHTML(internship.duration)}</span>` : ""}
        </div>

        ${internship.eligibility ? `
            <div class="card-eligibility-chip">
                ${ICONS.graduation} <span>Eligibility: ${escapeHTML(internship.eligibility)}</span>
            </div>
        ` : ""}

        ${internship.description ? `
            <p class="card-excerpt">
                "${escapeHTML(internship.description)}"
            </p>
        ` : ""}

        <div class="card-skills-block">
            <span class="skills-block-label">Required Skills</span>
            <p class="skills-block-text">${escapeHTML(skills)}</p>
        </div>

        <div class="card-match-breakdown">
            <div class="breakdown-column matched">
                <span class="breakdown-label">${ICONS.check} Matched</span>
                <p class="breakdown-text">${escapeHTML(matchedSkills)}</p>
            </div>
            <div class="breakdown-column missing">
                <span class="breakdown-label">${ICONS.dash} Missing</span>
                <p class="breakdown-text">${escapeHTML(missingSkills)}</p>
            </div>
        </div>

        <div class="card-footer-row">
            <div class="footer-left-actions">
                <button
                    type="button"
                    class="card-action-icon-btn bookmark-btn ${isSaved ? 'active' : ''}"
                    title="${isSaved ? 'Remove from saved' : 'Save opportunity'}"
                    aria-label="Bookmark"
                >
                    ${isSaved ? ICONS.bookmarkFilled : ICONS.bookmarkOutline}
                </button>
                ${applicationUrl !== "#" ? `
                    <button
                        type="button"
                        class="card-action-icon-btn copy-url-btn"
                        title="Copy direct application link"
                        aria-label="Copy URL"
                    >
                        ${ICONS.copy}
                    </button>
                ` : ""}
            </div>

            ${applicationUrl !== "#" ? `
                <a
                    href="${escapeAttribute(applicationUrl)}"
                    target="_blank"
                    rel="noopener noreferrer"
                    class="primary-btn btn-sm"
                >
                    <span>Apply Direct</span>
                    ${ICONS.externalLink}
                </a>
            ` : `
                <span class="unavail-note">Portal link unavailable</span>
            `}
        </div>
    `;

    // Bookmark binding
    const bookmarkBtn = card.querySelector(".bookmark-btn");
    if (bookmarkBtn && applicationUrl !== "#") {
        bookmarkBtn.addEventListener("click", () => {
            const nowSaved = toggleSaveUrl(applicationUrl);
            bookmarkBtn.classList.toggle("active", nowSaved);
            bookmarkBtn.innerHTML = nowSaved ? ICONS.bookmarkFilled : ICONS.bookmarkOutline;
            bookmarkBtn.setAttribute("title", nowSaved ? "Remove from saved" : "Save opportunity");
            showToast(nowSaved ? `Saved ${company} to bookmarks` : `Removed ${company} from bookmarks`, "info");
            if (currentActiveFilter === "saved") {
                renderFilteredInternships(currentUser);
            }
        });
    }

    // Copy URL binding
    const copyBtn = card.querySelector(".copy-url-btn");
    if (copyBtn && applicationUrl !== "#") {
        copyBtn.addEventListener("click", async () => {
            try {
                await navigator.clipboard.writeText(applicationUrl);
                showToast("Application link copied to clipboard", "success");
            } catch {
                showToast(applicationUrl, "info");
            }
        });
    }

    return card;
}


/* =========================================
   HTML SAFETY UTILS
   ========================================= */

function escapeHTML(value) {
    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function escapeAttribute(value) {
    return escapeHTML(value);
}


/* =========================================
   PREFERENCES SAVE & UPDATE
   ========================================= */

preferencesForm.addEventListener("submit", async function(event) {
    event.preventDefault();

    const user = getUser();
    if (!user) {
        showPage(loginPage);
        return;
    }

    const stipend = Number(document.getElementById("stipend").value);
    const locations = getSelectedLocations();

    if (locations.length === 0) {
        showToast("Please select at least one preferred location.", "warning");
        return;
    }

    const skills = document.getElementById("skills")
        .value
        .split(",")
        .map(s => s.trim())
        .filter(s => s.length > 0);

    user.preferences = {
        student_skills: skills,
        preferred_domain: document.getElementById("domain").value,
        internship_type: document.getElementById("internshipType").value,
        locations: locations,
        minimum_stipend: stipend,
        maximum_duration: document.getElementById("duration").value,
        payment_type: document.getElementById("paymentType").value,
        work_mode: document.getElementById("workMode").value,
        study_year: document.getElementById("studyYear").value,
        availability: document.getElementById("availability").value,
        deadline: document.getElementById("deadline").value,
        company_preference: document.getElementById("companyType").value,
        email_frequency: document.getElementById("frequency").value
    };

    saveUser(user);

    try {
        const apiUrl = await getApiUrl();
        await fetch(`${apiUrl}/save-preferences`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: user.name,
                email: user.email,
                student_skills: user.preferences.student_skills,
                preferred_domain: user.preferences.preferred_domain,
                internship_type: user.preferences.internship_type,
                locations: user.preferences.locations,
                minimum_stipend: user.preferences.minimum_stipend,
                maximum_duration: user.preferences.maximum_duration,
                payment_type: user.preferences.payment_type,
                work_mode: user.preferences.work_mode,
                study_year: user.preferences.study_year,
                availability: user.preferences.availability,
                deadline_preference: user.preferences.deadline,
                company_preference: user.preferences.company_preference,
                email_frequency: user.preferences.email_frequency
            })
        });
    } catch (error) {
        console.error("Could not save preferences to backend:", error);
    }

    loadDashboard(user);
    showPage(dashboardPage);
    showToast("Preferences saved successfully! Discovering matching opportunities...", "success");
    await searchInternships(user);
});


/* =========================================
   DASHBOARD DATA LOADER
   ========================================= */

function loadDashboard(user) {
    if (!user) return;

    const emailEl = document.getElementById("userEmail");
    if (emailEl) emailEl.textContent = user.email;

    const initial = (user.name || user.email || "C").trim().charAt(0).toUpperCase();
    const avatarEl = document.querySelector(".user-avatar-initial");
    if (avatarEl) avatarEl.textContent = initial;

    const preferences = user.preferences;
    if (!preferences) return;

    const welcomeEl = document.getElementById("welcomeText");
    if (welcomeEl) {
        welcomeEl.textContent = `Opportunities for ${user.name || "Candidate"}`;
    }

    const summarySkillsEl = document.getElementById("summarySkills");
    if (summarySkillsEl) {
        summarySkillsEl.textContent = (preferences.student_skills && preferences.student_skills.length)
            ? preferences.student_skills.join(" • ")
            : "All Domain Skills";
    }

    const summaryDomainEl = document.getElementById("summaryDomain");
    if (summaryDomainEl) {
        summaryDomainEl.textContent = preferences.preferred_domain || "Software Development";
    }

    const summaryLocationEl = document.getElementById("summaryLocation");
    if (summaryLocationEl) {
        summaryLocationEl.textContent = (preferences.locations && preferences.locations.length)
            ? preferences.locations.join(", ")
            : "Pan-India / Remote";
    }

    const summaryStipendEl = document.getElementById("summaryStipend");
    if (summaryStipendEl) {
        summaryStipendEl.textContent = "₹" + (preferences.minimum_stipend || 0).toLocaleString("en-IN") + "/mo";
    }

    const summaryWorkModeEl = document.getElementById("summaryWorkMode");
    if (summaryWorkModeEl) {
        summaryWorkModeEl.textContent = preferences.work_mode || "Any Arrangement";
    }

    const summaryTypeEl = document.getElementById("summaryType");
    if (summaryTypeEl) {
        summaryTypeEl.textContent = preferences.internship_type || "Any Classification";
    }

    const freqEl = document.getElementById("frequencyStatus");
    if (freqEl) {
        freqEl.textContent = preferences.email_frequency || "Daily";
    }

    const prefEmailEl = document.getElementById("preferenceEmail");
    if (prefEmailEl) {
        prefEmailEl.textContent = user.email;
    }

    updateSavedCountBadge();
}


/* =========================================
   EDIT PREFERENCES ROUTER
   ========================================= */

editPreferences.addEventListener("click", function() {
    const user = getUser();
    if (!user || !user.preferences) {
        showPage(preferencesPage);
        return;
    }

    const p = user.preferences;
    document.getElementById("skills").value = p.student_skills.join(", ");
    document.getElementById("domain").value = p.preferred_domain;
    document.getElementById("internshipType").value = p.internship_type;
    document.getElementById("stipend").value = p.minimum_stipend;
    document.getElementById("duration").value = p.maximum_duration;
    document.getElementById("paymentType").value = p.payment_type;
    document.getElementById("workMode").value = p.work_mode;
    document.getElementById("studyYear").value = p.study_year;
    document.getElementById("availability").value = p.availability;
    document.getElementById("deadline").value = p.deadline;
    document.getElementById("companyType").value = p.company_preference;
    document.getElementById("frequency").value = p.email_frequency;

    document.querySelectorAll('.location-grid input[type="checkbox"]').forEach(box => {
        box.checked = p.locations.includes(box.value);
    });

    const predefinedLocations = [
        "Mumbai", "Pune", "Bengaluru", "Hyderabad", "Delhi NCR",
        "Chennai", "Kolkata", "Ahmedabad", "Noida", "Gurugram",
        "Remote", "Anywhere in India"
    ];

    const customLocations = p.locations.filter(loc => !predefinedLocations.includes(loc));
    document.getElementById("customLocation").value = customLocations.join(", ");
    document.getElementById("preferenceEmail").textContent = user.email;

    showPage(preferencesPage);
});


/* =========================================
   LOGOUT CONTROLLER
   ========================================= */

function logout() {
    clearUser();
    loginForm.reset();
    preferencesForm.reset();
    showPage(loginPage);
    showToast("Signed out", "info");
}

logoutBtn.addEventListener("click", logout);
dashboardLogout.addEventListener("click", logout);


/* =========================================
   AUTOMATION TEST DISPATCH
   ========================================= */

const triggerTestEmailBtn = document.getElementById("triggerTestEmailBtn");
if (triggerTestEmailBtn) {
    triggerTestEmailBtn.addEventListener("click", async function() {
        const user = getUser();
        if (!user || !user.email) return;

        const feedbackEl = document.getElementById("emailActionFeedback");
        triggerTestEmailBtn.disabled = true;
        triggerTestEmailBtn.innerHTML = `<span>Dispatching Brief...</span>`;

        if (feedbackEl) {
            feedbackEl.className = "action-feedback-box feedback-pending";
            feedbackEl.style.display = "block";
            feedbackEl.innerHTML = `<span>Executing matching runner and dispatching personalized brief via Gmail SMTP...</span>`;
        }

        try {
            const apiUrl = await getApiUrl();
            const response = await fetch(`${apiUrl}/automation/trigger-test`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email: user.email })
            });

            const data = await response.json();

            if (response.ok && data.success) {
                if (feedbackEl) {
                    feedbackEl.className = "action-feedback-box feedback-success";
                    feedbackEl.innerHTML = `<strong>Dispatch Complete:</strong> ${escapeHTML(data.message)}`;
                }
                showToast("Brief delivered to inbox", "success");
            } else if (data.status === "cloud_smtp_blocked") {
                if (feedbackEl) {
                    feedbackEl.className = "action-feedback-box feedback-warning";
                    feedbackEl.innerHTML = `<strong>Cloud Hosting Notice:</strong> ${escapeHTML(data.message)}`;
                }
                showToast("Render Free Tier blocks raw SMTP ports", "info");
            } else {
                if (feedbackEl) {
                    feedbackEl.className = "action-feedback-box feedback-warning";
                    feedbackEl.innerHTML = `<strong>Notice:</strong> ${escapeHTML(data.message || data.error || "Could not dispatch test brief.")}`;
                }
            }
        } catch (err) {
            if (feedbackEl) {
                feedbackEl.className = "action-feedback-box feedback-error";
                feedbackEl.innerHTML = `<strong>Network Error:</strong> ${escapeHTML(err.message)}`;
            }
        } finally {
            triggerTestEmailBtn.disabled = false;
            triggerTestEmailBtn.innerHTML = `
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"></path><polyline points="22,6 12,13 2,6"></polyline></svg>
                <span>Send Test Digest</span>
            `;
        }
    });
}


/* =========================================
   THEME CONTROLLER (PERMANENT PURE LIGHT MODE)
   Strict Rules: Pure Titanium Light Mode only.
   ZERO Blue, ZERO Cream, ZERO Teal.
   ========================================= */

const THEME_STORAGE_KEY = "internflow_theme";

function applyTheme() {
    document.body.classList.add("light-theme");
    document.body.classList.remove("dark-theme");
    localStorage.setItem(THEME_STORAGE_KEY, "light");

    const toggleButtons = document.querySelectorAll(".theme-toggle-btn");
    toggleButtons.forEach(btn => {
        btn.style.display = "none";
    });
}

function initTheme() {
    applyTheme();
}


/* =========================================
   INTERACTIVE CONTROLS & LISTENERS
   ========================================= */

function initInteractiveFeatures() {
    // 1. Quick Demo Fill
    const quickDemoBtn = document.getElementById("quickDemoBtn");
    if (quickDemoBtn) {
        quickDemoBtn.addEventListener("click", () => {
            const nameInput = document.getElementById("loginName");
            const emailInput = document.getElementById("loginEmail");
            const passInput = document.getElementById("loginPassword");
            if (nameInput) nameInput.value = "Janavi Punmiya";
            if (emailInput) emailInput.value = "janavi@example.com";
            if (passInput) passInput.value = "DemoPass123!";
            showToast("Demo credentials populated", "info");
        });
    }

    // 2. Password Visibility Toggle
    const togglePassBtn = document.getElementById("togglePasswordBtn");
    const passInput = document.getElementById("loginPassword");
    if (togglePassBtn && passInput) {
        togglePassBtn.addEventListener("click", () => {
            const isPassword = passInput.type === "password";
            passInput.type = isPassword ? "text" : "password";
            togglePassBtn.innerHTML = isPassword ? ICONS.eyeOff : ICONS.eye;
            togglePassBtn.setAttribute("title", isPassword ? "Hide password" : "Show password");
        });
    }

    // 3. Quick Skill Suggestion Chips
    const skillInput = document.getElementById("skills");
    document.querySelectorAll(".skill-suggestion-chip").forEach(chip => {
        chip.addEventListener("click", () => {
            if (!skillInput) return;
            const skillToAdd = chip.getAttribute("data-skill") || chip.textContent.replace("+", "").trim();
            const currentVal = skillInput.value.trim();
            const currentSkills = currentVal ? currentVal.split(",").map(s => s.trim().toLowerCase()) : [];

            if (!currentSkills.includes(skillToAdd.toLowerCase())) {
                skillInput.value = currentVal ? `${currentVal}, ${skillToAdd}` : skillToAdd;
                chip.classList.add("added");
                showToast(`Added ${skillToAdd}`, "info", 1600);
            } else {
                showToast(`${skillToAdd} already added`, "warning", 1600);
            }
        });
    });

    // 4. Real-time Search Toolbar
    const searchInput = document.getElementById("internshipSearchInput");
    const clearSearchBtn = document.getElementById("clearSearchBtn");

    if (searchInput) {
        searchInput.addEventListener("input", () => {
            if (clearSearchBtn) {
                clearSearchBtn.style.display = searchInput.value.trim().length > 0 ? "block" : "none";
            }
            renderFilteredInternships();
        });
    }

    if (clearSearchBtn) {
        clearSearchBtn.addEventListener("click", () => {
            if (searchInput) searchInput.value = "";
            clearSearchBtn.style.display = "none";
            renderFilteredInternships();
        });
    }

    // 5. Toolbar Filter Pills
    document.querySelectorAll(".filter-pill").forEach(pill => {
        pill.addEventListener("click", () => {
            document.querySelectorAll(".filter-pill").forEach(p => p.classList.remove("active"));
            pill.classList.add("active");
            currentActiveFilter = pill.getAttribute("data-filter") || "all";
            renderFilteredInternships();
        });
    });

    // 6. Toolbar Sort Select
    const sortSelector = document.getElementById("sortSelector");
    if (sortSelector) {
        sortSelector.addEventListener("change", () => {
            renderFilteredInternships();
        });
    }

    // 7. Refresh Button
    const refreshBtn = document.getElementById("refreshSearchBtn");
    if (refreshBtn) {
        refreshBtn.addEventListener("click", function() {
            const user = getUser();
            if (user && user.preferences) {
                searchInternships(user);
            }
        });
    }

    updateSavedCountBadge();
}


/* =========================================
   INITIALIZATION
   ========================================= */

const existingUser = getUser();

if (existingUser) {
    if (existingUser.preferences) {
        // Signing is already done: directly show dashboard and internships!
        loadDashboard(existingUser);
        showPage(dashboardPage);
        searchInternships(existingUser);
    } else {
        // Preferences not yet saved: ask preferences first!
        document.getElementById("preferenceEmail").textContent = existingUser.email;
        showPage(preferencesPage);
    }
} else {
    showPage(loginPage);
}

initTheme();
initInteractiveFeatures();
