/* =========================================
   INTERNFLOW
   Frontend application logic
========================================= */


/* =========================================
   DEMO INTERNSHIP DATA
========================================= */

const demoInternships = [
    {
        id: 1,
        company: "Vertex Labs",
        title: "Software Engineering Intern",
        location: "Bengaluru, India",
        mode: "Hybrid",
        stipend: "₹25,000 / month",
        deadline: "2026-10-08",
        source: "Company careers",
        skills: ["Python", "JavaScript", "Git"],
        description:
            "Work with the engineering team to build and improve internal products, APIs and developer tools. This role is suitable for students with strong programming fundamentals."
    },

    {
        id: 2,
        company: "Nexa Analytics",
        title: "Data Science Intern",
        location: "Remote",
        mode: "Remote",
        stipend: "₹20,000 / month",
        deadline: "2026-10-12",
        source: "Internship portal",
        skills: ["Python", "SQL", "Pandas"],
        description:
            "Assist the analytics team with data preparation, exploratory analysis and building data-driven reports for business teams."
    },

    {
        id: 3,
        company: "Orbit AI",
        title: "Machine Learning Intern",
        location: "Pune, India",
        mode: "Hybrid",
        stipend: "₹30,000 / month",
        deadline: "2026-10-06",
        source: "Company careers",
        skills: ["Python", "Machine Learning", "TensorFlow"],
        description:
            "Support machine learning experiments, prepare datasets and help evaluate models used in real-world AI applications."
    },

    {
        id: 4,
        company: "Northstar Digital",
        title: "Frontend Development Intern",
        location: "Mumbai, India",
        mode: "On-site",
        stipend: "₹18,000 / month",
        deadline: "2026-10-18",
        source: "Internship portal",
        skills: ["HTML", "CSS", "JavaScript", "React"],
        description:
            "Work with designers and developers to create responsive interfaces and improve the user experience of digital products."
    },

    {
        id: 5,
        company: "CloudHarbor",
        title: "DevOps Intern",
        location: "Remote",
        mode: "Remote",
        stipend: "₹22,000 / month",
        deadline: "2026-10-22",
        source: "Company careers",
        skills: ["Linux", "Docker", "Git"],
        description:
            "Learn and contribute to cloud infrastructure, deployment pipelines, monitoring and developer productivity systems."
    },

    {
        id: 6,
        company: "Pixel & Form",
        title: "Product Design Intern",
        location: "Mumbai, India",
        mode: "Hybrid",
        stipend: "₹17,000 / month",
        deadline: "2026-10-14",
        source: "Design jobs",
        skills: ["Figma", "UI Design", "UX Research"],
        description:
            "Collaborate with product managers and engineers to research user needs and design clean, useful digital experiences."
    },

    {
        id: 7,
        company: "SecureGrid",
        title: "Cybersecurity Intern",
        location: "Bengaluru, India",
        mode: "On-site",
        stipend: "₹23,000 / month",
        deadline: "2026-10-25",
        source: "Company careers",
        skills: ["Linux", "Networking", "Python"],
        description:
            "Assist the security team with monitoring, vulnerability research and security testing while learning practical cybersecurity workflows."
    },

    {
        id: 8,
        company: "BrightScale",
        title: "Backend Developer Intern",
        location: "Remote",
        mode: "Remote",
        stipend: "₹24,000 / month",
        deadline: "2026-10-10",
        source: "Internship portal",
        skills: ["Node.js", "Python", "SQL"],
        description:
            "Build APIs and backend services, work with databases and collaborate with frontend developers to deliver reliable web applications."
    }
];


/* =========================================
   APPLICATION STATE
========================================= */

let profile = JSON.parse(localStorage.getItem("internflowProfile")) || null;

let savedInternships =
    JSON.parse(localStorage.getItem("internflowSaved")) || [];

let applications =
    JSON.parse(localStorage.getItem("internflowApplications")) || [];


/* =========================================
   DOM REFERENCES
========================================= */

const profileScreen = document.getElementById("profileScreen");
const app = document.getElementById("app");

const profileForm = document.getElementById("profileForm");
const editProfileForm = document.getElementById("editProfileForm");

const internshipModal = document.getElementById("internshipModal");
const modalContent = document.getElementById("modalContent");
const closeModal = document.getElementById("closeModal");

const toast = document.getElementById("toast");
const toastMessage = document.getElementById("toastMessage");


/* =========================================
   INITIALIZATION
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    if (profile) {
        showApplication();
        updateAllUI();
    } else {
        showProfileScreen();
    }

    setupNavigation();
    setupProfileForm();
    setupEditProfile();
    setupSearch();
    setupFilters();
    setupModal();
    setupRefreshButton();
});


/* =========================================
   SCREEN MANAGEMENT
========================================= */

function showProfileScreen() {
    profileScreen.classList.remove("hidden");
    app.classList.add("hidden");
}


function showApplication() {
    profileScreen.classList.add("hidden");
    app.classList.remove("hidden");
}


/* =========================================
   PROFILE FORM
========================================= */

function setupProfileForm() {

    profileForm.addEventListener("submit", (event) => {

        event.preventDefault();

        profile = {
            name: document.getElementById("fullName").value.trim(),
            degree: document.getElementById("degree").value.trim(),
            graduation: document.getElementById("graduation").value,
            role: document.getElementById("preferredRole").value,
            mode: document.getElementById("workMode").value,
            skills: document
                .getElementById("skills")
                .value
                .split(",")
                .map(skill => skill.trim())
                .filter(Boolean)
        };

        saveProfile();

        showApplication();

        updateAllUI();

        showToast("Your internship feed is ready.");
    });
}


/* =========================================
   EDIT PROFILE
========================================= */

function setupEditProfile() {

    editProfileForm.addEventListener("submit", (event) => {

        event.preventDefault();

        profile.name =
            document.getElementById("editName").value.trim();

        profile.degree =
            document.getElementById("editDegree").value.trim();

        profile.graduation =
            document.getElementById("editGraduation").value;

        profile.role =
            document.getElementById("editRole").value;

        profile.mode =
            document.getElementById("editMode").value;

        profile.skills =
            document
                .getElementById("editSkills")
                .value
                .split(",")
                .map(skill => skill.trim())
                .filter(Boolean);

        saveProfile();

        updateAllUI();

        showToast("Profile updated.");
    });
}


function saveProfile() {
    localStorage.setItem(
        "internflowProfile",
        JSON.stringify(profile)
    );
}


/* =========================================
   NAVIGATION
========================================= */

function setupNavigation() {

    const navItems =
        document.querySelectorAll(".nav-item");

    navItems.forEach(item => {

        item.addEventListener("click", () => {

            const page = item.dataset.page;

            switchPage(page);

            navItems.forEach(nav =>
                nav.classList.remove("active")
            );

            item.classList.add("active");
        });
    });


    document.querySelectorAll("[data-page-link]")
        .forEach(button => {

            button.addEventListener("click", () => {

                const page = button.dataset.pageLink;

                switchPage(page);

                navItems.forEach(nav =>
                    nav.classList.remove("active")
                );

                const matchingNav =
                    document.querySelector(
                        `.nav-item[data-page="${page}"]`
                    );

                if (matchingNav) {
                    matchingNav.classList.add("active");
                }
            });
        });
}


function switchPage(pageName) {

    document.querySelectorAll(".page")
        .forEach(page => {
            page.classList.remove("active-page");
        });

    const targetPage =
        document.getElementById(`${pageName}Page`);

    if (targetPage) {
        targetPage.classList.add("active-page");
    }

    if (pageName === "discover") {
        renderDiscover();
    }

    if (pageName === "saved") {
        renderSaved();
    }

    if (pageName === "applications") {
        renderApplications();
    }

    if (pageName === "profile") {
        populateProfileForm();
    }
}


/* =========================================
   SEARCH
========================================= */

function setupSearch() {

    const globalSearch =
        document.getElementById("globalSearch");

    globalSearch.addEventListener("input", () => {

        const searchValue =
            globalSearch.value.trim();

        if (!searchValue) {
            return;
        }

        switchPage("discover");

        document
            .getElementById("internshipSearch")
            .value = searchValue;

        renderDiscover();
    });
}


function setupFilters() {

    document
        .getElementById("internshipSearch")
        .addEventListener("input", renderDiscover);

    document
        .getElementById("modeFilter")
        .addEventListener("change", renderDiscover);

    document
        .getElementById("sortFilter")
        .addEventListener("change", renderDiscover);
}


/* =========================================
   MATCHING ENGINE
========================================= */

function calculateMatch(internship) {

    if (!profile) {
        return 50;
    }

    let score = 40;

    const preferredRole =
        profile.role.toLowerCase();

    const internshipTitle =
        internship.title.toLowerCase();

    if (
        internshipTitle.includes(
            preferredRole.split(" ")[0]
        )
    ) {
        score += 25;
    }

    const userSkills =
        profile.skills.map(skill =>
            skill.toLowerCase()
        );

    const internshipSkills =
        internship.skills.map(skill =>
            skill.toLowerCase()
        );

    const matchingSkills =
        internshipSkills.filter(skill =>
            userSkills.some(userSkill =>
                userSkill.includes(skill) ||
                skill.includes(userSkill)
            )
        );

    score +=
        Math.min(
            matchingSkills.length * 8,
            30
        );

    if (
        profile.mode === "Any" ||
        profile.mode === internship.mode
    ) {
        score += 5;
    }

    return Math.min(score, 99);
}


/* =========================================
   DATE FUNCTIONS
========================================= */

function getDaysUntil(dateString) {

    const today = new Date();

    today.setHours(0, 0, 0, 0);

    const deadline =
        new Date(`${dateString}T00:00:00`);

    const difference =
        deadline.getTime() - today.getTime();

    return Math.ceil(
        difference / (1000 * 60 * 60 * 24)
    );
}


function formatDeadline(dateString) {

    const date =
        new Date(`${dateString}T00:00:00`);

    return date.toLocaleDateString("en-IN", {
        day: "numeric",
        month: "short"
    });
}


function getDeadlineText(dateString) {

    const days =
        getDaysUntil(dateString);

    if (days < 0) {
        return "Closed";
    }

    if (days === 0) {
        return "Closes today";
    }

    if (days === 1) {
        return "1 day left";
    }

    return `${days} days left`;
}


/* =========================================
   INTERNSHIP CARD
========================================= */

function createInternshipCard(internship) {

    const isSaved =
        savedInternships.includes(internship.id);

    const match =
        calculateMatch(internship);

    const days =
        getDaysUntil(internship.deadline);

    const urgent =
        days <= 7 && days >= 0;

    const logo =
        internship.company
            .split(" ")
            .map(word => word[0])
            .join("")
            .substring(0, 2)
            .toUpperCase();

    return `
        <article class="internship-card">

            <div class="internship-main">

                <div class="company-logo">
                    ${logo}
                </div>

                <div class="internship-info">

                    <div class="company-name">
                        ${internship.company}
                    </div>

                    <div class="internship-title">
                        ${internship.title}
                    </div>

                    <div class="internship-meta">
                        <span>⌖ ${internship.location}</span>
                        <span>◷ ${internship.mode}</span>
                        <span>₹ ${internship.stipend.replace("₹ ", "")}</span>
                    </div>

                </div>

                <div class="internship-actions">

                    <span class="match-badge">
                        ${match}% match
                    </span>

                    <button
                        class="save-button ${isSaved ? "saved" : ""}"
                        onclick="toggleSave(${internship.id})"
                        title="Save internship"
                    >
                        ${isSaved ? "♥" : "♡"}
                    </button>

                </div>

            </div>

            <div class="internship-bottom">

                <div class="skill-tags">
                    ${internship.skills
                        .map(skill =>
                            `<span class="skill-tag">${skill}</span>`
                        )
                        .join("")
                    }
                </div>

                <div class="deadline-label ${urgent ? "urgent" : ""}">
                    ${getDeadlineText(internship.deadline)}
                    · ${formatDeadline(internship.deadline)}
                </div>

                <button
                    class="view-button"
                    onclick="openInternship(${internship.id})"
                >
                    View details →
                </button>

            </div>

        </article>
    `;
}


/* =========================================
   OVERVIEW
========================================= */

function renderOverview() {

    const sorted =
        [...demoInternships]
            .sort(
                (a, b) =>
                    calculateMatch(b) -
                    calculateMatch(a)
            );

    const featured =
        sorted.slice(0, 5);

    document.getElementById("featuredInternships")
        .innerHTML =
            featured
                .map(createInternshipCard)
                .join("");

    renderDeadlines();

    updateStats();
}


function renderDeadlines() {

    const upcoming =
        [...demoInternships]
            .filter(item =>
                getDaysUntil(item.deadline) >= 0
            )
            .sort(
                (a, b) =>
                    new Date(a.deadline) -
                    new Date(b.deadline)
            )
            .slice(0, 4);

    const container =
        document.getElementById("deadlineList");

    if (!upcoming.length) {

        container.innerHTML = `
            <div class="empty-state">
                <div class="empty-state-icon">✓</div>
                <h3>All clear</h3>
                <p>No upcoming deadlines.</p>
            </div>
        `;

        return;
    }

    container.innerHTML =
        upcoming
            .map(item => {

                const date =
                    new Date(
                        `${item.deadline}T00:00:00`
                    );

                return `
                    <div class="deadline-item">

                        <div class="deadline-date">
                            <strong>${date.getDate()}</strong>
                            <span>
                                ${date
                                    .toLocaleDateString(
                                        "en-IN",
                                        { month: "short" }
                                    )
                                    .toUpperCase()
                                }
                            </span>
                        </div>

                        <div class="deadline-info">
                            <strong>${item.title}</strong>
                            <span>
                                ${item.company}
                                · ${getDeadlineText(item.deadline)}
                            </span>
                        </div>

                    </div>
                `;
            })
            .join("");
}


/* =========================================
   DISCOVER
========================================= */

function renderDiscover() {

    const search =
        document
            .getElementById("internshipSearch")
            .value
            .toLowerCase()
            .trim();

    const mode =
        document
            .getElementById("modeFilter")
            .value;

    const sort =
        document
            .getElementById("sortFilter")
            .value;

    let results =
        demoInternships.filter(item => {

            const searchable =
                [
                    item.company,
                    item.title,
                    item.location,
                    item.mode,
                    ...item.skills
                ]
                    .join(" ")
                    .toLowerCase();

            const matchesSearch =
                !search ||
                searchable.includes(search);

            const matchesMode =
                mode === "All" ||
                item.mode === mode;

            return matchesSearch && matchesMode;
        });


    if (sort === "match") {

        results.sort(
            (a, b) =>
                calculateMatch(b) -
                calculateMatch(a)
        );

    } else if (sort === "deadline") {

        results.sort(
            (a, b) =>
                new Date(a.deadline) -
                new Date(b.deadline)
        );

    } else if (sort === "stipend") {

        results.sort(
            (a, b) =>
                extractStipend(b.stipend) -
                extractStipend(a.stipend)
        );
    }


    const container =
        document.getElementById("discoverList");

    if (!results.length) {

        container.innerHTML = `
            <div class="empty-state">

                <div class="empty-state-icon">
                    ⌕
                </div>

                <h3>No internships found</h3>

                <p>
                    Try changing your search or filters.
                </p>

            </div>
        `;

        return;
    }

    container.innerHTML =
        results
            .map(createInternshipCard)
            .join("");
}


function extractStipend(value) {

    return parseInt(
        value
            .replace(/[^\d]/g, ""),
        10
    ) || 0;
}


/* =========================================
   SAVE / UNSAVE
========================================= */

function toggleSave(id) {

    if (savedInternships.includes(id)) {

        savedInternships =
            savedInternships.filter(
                savedId => savedId !== id
            );

        showToast("Removed from saved.");

    } else {

        savedInternships.push(id);

        showToast("Internship saved.");
    }

    localStorage.setItem(
        "internflowSaved",
        JSON.stringify(savedInternships)
    );

    updateAllUI();
}


/* =========================================
   SAVED PAGE
========================================= */

function renderSaved() {

    const saved =
        demoInternships.filter(
            item =>
                savedInternships.includes(item.id)
        );

    const container =
        document.getElementById("savedList");

    if (!saved.length) {

        container.innerHTML = `
            <div class="empty-state">

                <div class="empty-state-icon">
                    ♡
                </div>

                <h3>Your shortlist is empty</h3>

                <p>
                    Save internships from Discover and they'll appear here.
                </p>

            </div>
        `;

        return;
    }

    container.innerHTML =
        saved
            .map(createInternshipCard)
            .join("");
}


/* =========================================
   INTERNSHIP MODAL
========================================= */

function openInternship(id) {

    const internship =
        demoInternships.find(
            item => item.id === id
        );

    if (!internship) {
        return;
    }

    const isSaved =
        savedInternships.includes(id);

    const hasApplied =
        applications.some(
            item => item.id === id
        );

    const match =
        calculateMatch(internship);

    modalContent.innerHTML = `

        <div class="modal-company">
            ${internship.company}
        </div>

        <h2 class="modal-title">
            ${internship.title}
        </h2>

        <div class="modal-meta">
            <span>⌖ ${internship.location}</span>
            <span>◷ ${internship.mode}</span>
            <span>${internship.stipend}</span>
            <span>${match}% profile match</span>
        </div>

        <div class="modal-section">

            <h4>ABOUT THE ROLE</h4>

            <p>
                ${internship.description}
            </p>

        </div>

        <div class="modal-section">

            <h4>KEY SKILLS</h4>

            <div class="skill-tags">
                ${internship.skills
                    .map(skill =>
                        `<span class="skill-tag">${skill}</span>`
                    )
                    .join("")
                }
            </div>

        </div>

        <div class="modal-section">

            <h4>APPLICATION DEADLINE</h4>

            <p>
                ${formatDeadline(internship.deadline)}
                · ${getDeadlineText(internship.deadline)}
            </p>

        </div>

        <div class="modal-actions">

            <button
                class="secondary-button"
                onclick="toggleSave(${internship.id})"
            >
                ${isSaved ? "♥ Saved" : "♡ Save internship"}
            </button>

            <button
                class="primary-button"
                onclick="applyInternship(${internship.id})"
            >
                ${hasApplied ? "Application tracked" : "Mark as applied"}
            </button>

        </div>
    `;

    internshipModal.classList.remove("hidden");
}


function setupModal() {

    closeModal.addEventListener(
        "click",
        closeInternshipModal
    );

    document
        .querySelector(".modal-overlay")
        .addEventListener(
            "click",
            closeInternshipModal
        );
}


function closeInternshipModal() {

    internshipModal.classList.add("hidden");
}


/* =========================================
   APPLICATIONS
========================================= */

function applyInternship(id) {

    const internship =
        demoInternships.find(
            item => item.id === id
        );

    if (!internship) {
        return;
    }

    const alreadyApplied =
        applications.some(
            item => item.id === id
        );

    if (alreadyApplied) {

        showToast("Application already tracked.");

        closeInternshipModal();

        return;
    }

    applications.push({
        id: internship.id,
        company: internship.company,
        title: internship.title,
        appliedDate: new Date().toISOString(),
        status: "In progress"
    });

    localStorage.setItem(
        "internflowApplications",
        JSON.stringify(applications)
    );

    closeInternshipModal();

    updateAllUI();

    showToast("Application added to your tracker.");
}


function renderApplications() {

    const container =
        document.getElementById("applicationsList");

    if (!applications.length) {

        container.innerHTML = `
            <div class="empty-state">

                <div class="empty-state-icon">
                    ✓
                </div>

                <h3>No applications yet</h3>

                <p>
                    When you apply to an internship, track it here.
                </p>

            </div>
        `;

        return;
    }

    container.innerHTML =
        applications
            .map(application => {

                return `
                    <div class="application-item">

                        <div class="company-logo">
                            ${application.company
                                .split(" ")
                                .map(word => word[0])
                                .join("")
                                .substring(0, 2)
                                .toUpperCase()
                            }
                        </div>

                        <div class="application-info">

                            <strong>
                                ${application.title}
                            </strong>

                            <span>
                                ${application.company}
                                · Applied ${formatApplicationDate(application.appliedDate)}
                            </span>

                        </div>

                        <span class="application-status">
                            ${application.status}
                        </span>

                    </div>
                `;
            })
            .join("");
}


function formatApplicationDate(date) {

    return new Date(date)
        .toLocaleDateString(
            "en-IN",
            {
                day: "numeric",
                month: "short"
            }
        );
}


/* =========================================
   PROFILE UI
========================================= */

function populateProfileForm() {

    if (!profile) {
        return;
    }

    document.getElementById("editName").value =
        profile.name;

    document.getElementById("editDegree").value =
        profile.degree;

    document.getElementById("editGraduation").value =
        profile.graduation;

    document.getElementById("editRole").value =
        profile.role;

    document.getElementById("editMode").value =
        profile.mode;

    document.getElementById("editSkills").value =
        profile.skills.join(", ");
}


/* =========================================
   STATS
========================================= */

function updateStats() {

    const relevantMatches =
        demoInternships.filter(
            item => calculateMatch(item) >= 60
        ).length;

    const closingSoon =
        demoInternships.filter(
            item => {
                const days =
                    getDaysUntil(item.deadline);

                return days >= 0 && days <= 7;
            }
        ).length;

    document.getElementById("matchStat")
        .textContent = relevantMatches;

    document.getElementById("savedStat")
        .textContent = savedInternships.length;

    document.getElementById("applicationStat")
        .textContent = applications.length;

    document.getElementById("deadlineStat")
        .textContent = closingSoon;

    document.getElementById("savedCount")
        .textContent = savedInternships.length;


    const applied =
        applications.length;

    const progress =
        applications.filter(
            item => item.status === "In progress"
        ).length;

    const completed =
        applications.filter(
            item => item.status === "Completed"
        ).length;

    document.getElementById("appliedCount")
        .textContent = applied;

    document.getElementById("progressCount")
        .textContent = progress;

    document.getElementById("completedCount")
        .textContent = completed;
}


/* =========================================
   USER DETAILS
========================================= */

function updateUserDetails() {

    if (!profile) {
        return;
    }

    const firstName =
        profile.name
            .split(" ")[0];

    const initials =
        profile.name
            .split(" ")
            .map(word => word[0])
            .join("")
            .substring(0, 2)
            .toUpperCase();


    document.getElementById("sidebarUserName")
        .textContent = profile.name;

    document.getElementById("sidebarUserRole")
        .textContent = profile.role;

    document.getElementById("sidebarAvatar")
        .textContent = initials;

    document.getElementById("topbarAvatar")
        .textContent = initials;

    document.getElementById("profileAvatar")
        .textContent = initials;

    document.getElementById("profileName")
        .textContent = profile.name;

    document.getElementById("profileDegree")
        .textContent =
            `${profile.degree} · ${profile.graduation}`;

    document.getElementById("welcomeHeading")
        .textContent =
            `Good morning, ${firstName}.`;
}


/* =========================================
   REFRESH
========================================= */

function setupRefreshButton() {

    document
        .getElementById("refreshButton")
        .addEventListener("click", () => {

            const button =
                document.getElementById("refreshButton");

            button.textContent =
                "↻ Scanning...";

            setTimeout(() => {

                renderOverview();

                button.textContent =
                    "↻ Refresh opportunities";

                showToast(
                    "Opportunity feed refreshed."
                );

            }, 900);
        });
}


/* =========================================
   GLOBAL UI UPDATE
========================================= */

function updateAllUI() {

    if (!profile) {
        return;
    }

    updateUserDetails();

    renderOverview();

    renderDiscover();

    renderSaved();

    renderApplications();

    populateProfileForm();
}


/* =========================================
   TOAST
========================================= */

let toastTimeout;

function showToast(message) {

    toastMessage.textContent =
        message;

    toast.classList.add("show");

    clearTimeout(toastTimeout);

    toastTimeout =
        setTimeout(() => {

            toast.classList.remove("show");

        }, 2500);
}


/* =========================================
   NOTIFICATION BUTTON
========================================= */

document
    .getElementById("notificationButton")
    .addEventListener("click", () => {

        showToast(
            "No new internship alerts."
        );
    });


/* =========================================
   EXPOSE FUNCTIONS FOR HTML BUTTONS
========================================= */

window.toggleSave = toggleSave;
window.openInternship = openInternship;
window.applyInternship = applyInternship;