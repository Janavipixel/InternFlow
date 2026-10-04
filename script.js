/* =========================================
   INTERNFLOW
========================================= */

const loginPage = document.getElementById("loginPage");
const preferencesPage = document.getElementById("preferencesPage");
const dashboardPage = document.getElementById("dashboardPage");

const loginForm = document.getElementById("loginForm");
const preferencesForm = document.getElementById("preferencesForm");

const logoutBtn = document.getElementById("logoutBtn");
const dashboardLogout = document.getElementById("dashboardLogout");
const editPreferences = document.getElementById("editPreferences");

const STORAGE_KEY = "internflow_user";

/*
   Frontend and backend are hosted
   on the same Render service.
*/
const API_URL = "";


/* =========================================
   STORAGE
========================================= */

function getUser() {

    const saved = localStorage.getItem(STORAGE_KEY);

    if (!saved) {
        return null;
    }

    try {
        return JSON.parse(saved);
    } catch {
        return null;
    }

}


function saveUser(user) {

    localStorage.setItem(
        STORAGE_KEY,
        JSON.stringify(user)
    );

}


function clearUser() {

    localStorage.removeItem(STORAGE_KEY);

}


/* =========================================
   PAGE SWITCH
========================================= */

function showPage(page) {

    loginPage.classList.remove("active");
    preferencesPage.classList.remove("active");
    dashboardPage.classList.remove("active");

    page.classList.add("active");

}


/* =========================================
   LOGIN
========================================= */

loginForm.addEventListener("submit", function(event) {

    event.preventDefault();

    const name =
        document.getElementById("loginName").value.trim();

    const email =
        document.getElementById("loginEmail").value.trim();

    const password =
        document.getElementById("loginPassword").value.trim();

    if (!name || !email || !password) {
        return;
    }

    const oldUser = getUser();

    if (
        oldUser &&
        oldUser.email === email &&
        oldUser.preferences
    ) {

        oldUser.name = name;

        saveUser(oldUser);

        loadDashboard(oldUser);

        showPage(dashboardPage);

        return;
    }

    const user = {

        name: name,

        email: email,

        preferences: null

    };

    saveUser(user);

    document.getElementById("preferenceEmail").textContent =
        email;

    showPage(preferencesPage);

});


/* =========================================
   LOCATION
========================================= */

function getSelectedLocations() {

    const checked =
        document.querySelectorAll(
            '.location-grid input[type="checkbox"]:checked'
        );

    const locations = [];

    checked.forEach(function(item) {

        locations.push(item.value);

    });

    const custom =
        document.getElementById("customLocation")
            .value
            .trim();

    if (custom) {

        locations.push(custom);

    }

    return locations;

}


/* =========================================
   SEARCH INTERNSHIPS
========================================= */

async function searchInternships(user) {

    const resultsContainer =
        document.getElementById("internshipResults");

    const resultsCount =
        document.getElementById("resultsCount");

    if (!resultsContainer || !resultsCount) {
        return;
    }

    resultsCount.textContent = "Searching...";

    resultsContainer.innerHTML = `
        <p class="results-message">
            Searching for internships based on your preferences...
        </p>
    `;

    const preferences = user.preferences;

    try {

        const response = await fetch(
            `${API_URL}/search-internships`,
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({

                    student_skills:
                        preferences.student_skills,

                    preferred_domain:
                        preferences.preferred_domain,

                    locations:
                        preferences.locations,

                    minimum_stipend:
                        preferences.minimum_stipend

                })
            }
        );

        if (!response.ok) {

            throw new Error(
                `Server returned ${response.status}`
            );

        }

        const data = await response.json();

        displayInternships(data.internships || []);

    } catch (error) {

        console.error(
            "Internship search failed:",
            error
        );

        resultsCount.textContent = "Search failed";

        resultsContainer.innerHTML = `
            <p class="results-message">
                We couldn't fetch internships right now.
                Please make sure the InternFlow backend is running.
            </p>
        `;

    }

}


/* =========================================
   DISPLAY INTERNSHIPS
========================================= */

function displayInternships(internships) {

    const resultsContainer =
        document.getElementById("internshipResults");

    const resultsCount =
        document.getElementById("resultsCount");

    if (!resultsContainer || !resultsCount) {
        return;
    }

    resultsCount.textContent =
        `${internships.length} found`;

    if (internships.length === 0) {

        resultsContainer.innerHTML = `
            <p class="results-message">
                No matching internships were found
                for your current preferences.
            </p>
        `;

        return;

    }

    resultsContainer.innerHTML = "";

    internships.forEach(function(internship) {

        const card =
            document.createElement("article");

        card.className = "internship-card";

        const company =
            internship.company || "Company not available";

        const role =
            internship.role || "Internship opportunity";

        const location =
            internship.location || "Location not specified";

        const stipend =
            internship.stipend || "Stipend not specified";

        const match =
            internship.match_percentage;

        const applicationUrl =
            internship.application_url ||
            internship.source_url ||
            "#";

        const skills =
            Array.isArray(internship.skills)
                ? internship.skills.join(", ")
                : internship.skills || "Not specified";

        const matchedSkills =
            Array.isArray(internship.matched_skills)
                ? internship.matched_skills.join(", ")
                : "None";

        const missingSkills =
            Array.isArray(internship.missing_skills)
                ? internship.missing_skills.join(", ")
                : "None";

        card.innerHTML = `

            <div class="internship-card-top">

                <div>

                    <span class="internship-company">
                        ${escapeHTML(company)}
                    </span>

                    <h3>
                        ${escapeHTML(role)}
                    </h3>

                </div>

                <div class="match-badge">

                    ${match !== undefined && match !== null
                        ? `${match}% match`
                        : "Match unavailable"}

                </div>

            </div>

            <div class="internship-meta">

                <span>
                    📍 ${escapeHTML(location)}
                </span>

                <span>
                    💰 ${escapeHTML(stipend)}
                </span>

            </div>

            <div class="internship-skills">

                <strong>
                    Required skills
                </strong>

                <p>
                    ${escapeHTML(skills)}
                </p>

            </div>

            <div class="internship-match-details">

                <div>

                    <strong>
                        Matched
                    </strong>

                    <p>
                        ${escapeHTML(matchedSkills)}
                    </p>

                </div>

                <div>

                    <strong>
                        Missing
                    </strong>

                    <p>
                        ${escapeHTML(missingSkills)}
                    </p>

                </div>

            </div>

            <div class="internship-card-bottom">

                ${
                    applicationUrl !== "#"
                        ? `
                            <a
                                href="${escapeAttribute(applicationUrl)}"
                                target="_blank"
                                rel="noopener noreferrer"
                                class="apply-btn"
                            >
                                View & Apply →
                            </a>
                          `
                        : `
                            <span class="no-link">
                                Application link unavailable
                            </span>
                          `
                }

            </div>

        `;

        resultsContainer.appendChild(card);

    });

}


/* =========================================
   HTML SAFETY
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
   PREFERENCES
========================================= */

preferencesForm.addEventListener(
    "submit",
    async function(event) {

        event.preventDefault();

        const user = getUser();

        if (!user) {

            showPage(loginPage);

            return;

        }

        const stipend =
            Number(
                document.getElementById("stipend").value
            );

        /*
           Never allow an unrealistic
           minimum stipend below ₹5,000.
        */

        if (stipend < 5000) {

            alert(
                "Minimum stipend must be at least ₹5,000 per month."
            );

            document.getElementById("stipend").value = 5000;

            return;

        }

        const locations =
            getSelectedLocations();

        if (locations.length === 0) {

            alert(
                "Please select at least one preferred location."
            );

            return;

        }

        const skills =
            document.getElementById("skills")
                .value
                .split(",")
                .map(skill => skill.trim())
                .filter(skill => skill.length > 0);

        user.preferences = {

            student_skills: skills,

            preferred_domain:
                document.getElementById("domain").value,

            internship_type:
                document.getElementById("internshipType").value,

            locations: locations,

            minimum_stipend: stipend,

            maximum_duration:
                document.getElementById("duration").value,

            payment_type:
                document.getElementById("paymentType").value,

            work_mode:
                document.getElementById("workMode").value,

            study_year:
                document.getElementById("studyYear").value,

            availability:
                document.getElementById("availability").value,

            deadline:
                document.getElementById("deadline").value,

            company_preference:
                document.getElementById("companyType").value,

            email_frequency:
                document.getElementById("frequency").value

        };

        saveUser(user);

        // Save preferences to backend database
        try {

            const response = await fetch(
                `${API_URL}/save-preferences`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type": "application/json"
                    },

                    body: JSON.stringify({
                        name: user.name,
                        email: user.email,

                        student_skills:
                            user.preferences.student_skills,

                        preferred_domain:
                            user.preferences.preferred_domain,

                        internship_type:
                            user.preferences.internship_type,

                        locations:
                            user.preferences.locations,

                        minimum_stipend:
                            user.preferences.minimum_stipend,

                        maximum_duration:
                            user.preferences.maximum_duration,

                        payment_type:
                            user.preferences.payment_type,

                        work_mode:
                            user.preferences.work_mode,

                        study_year:
                            user.preferences.study_year,

                        availability:
                            user.preferences.availability,

                        deadline_preference:
                            user.preferences.deadline,

                        company_preference:
                            user.preferences.company_preference,

                        email_frequency:
                            user.preferences.email_frequency
                    })
                }
            );

            const result = await response.json();

            console.log(result);

        } catch (error) {

            console.error(
                "Could not save preferences:",
                error
            );

        }

        /*
           Show dashboard first so the user
           can see the search progress.
        */

        loadDashboard(user);

        showPage(dashboardPage);

        /*
           Now call the Flask AI pipeline.
        */

        await searchInternships(user);

    }
);


/* =========================================
   DASHBOARD
========================================= */

function loadDashboard(user) {

    if (!user) {
        return;
    }

    document.getElementById("userEmail").textContent =
        user.email;

    const preferences =
        user.preferences;

    if (!preferences) {
        return;
    }

    document.getElementById("welcomeText").textContent =
        `Your internship search is active, ${user.name}.`;

    document.getElementById("summarySkills").textContent =
        preferences.student_skills.join(", ");

    document.getElementById("summaryDomain").textContent =
        preferences.preferred_domain;

    document.getElementById("summaryLocation").textContent =
        preferences.locations.join(", ");

    document.getElementById("summaryStipend").textContent =
        "₹" +
        preferences.minimum_stipend.toLocaleString("en-IN");

    document.getElementById("summaryWorkMode").textContent =
        preferences.work_mode;

    document.getElementById("summaryType").textContent =
        preferences.internship_type;

    document.getElementById("frequencyStatus").textContent =
        preferences.email_frequency;

    document.getElementById("preferenceEmail").textContent =
        user.email;

}


/* =========================================
   EDIT PREFERENCES
========================================= */

editPreferences.addEventListener("click", function() {

    const user = getUser();

    if (!user || !user.preferences) {

        showPage(preferencesPage);

        return;

    }

    const p = user.preferences;

    document.getElementById("skills").value =
        p.student_skills.join(", ");

    document.getElementById("domain").value =
        p.preferred_domain;

    document.getElementById("internshipType").value =
        p.internship_type;

    document.getElementById("stipend").value =
        p.minimum_stipend;

    document.getElementById("duration").value =
        p.maximum_duration;

    document.getElementById("paymentType").value =
        p.payment_type;

    document.getElementById("workMode").value =
        p.work_mode;

    document.getElementById("studyYear").value =
        p.study_year;

    document.getElementById("availability").value =
        p.availability;

    document.getElementById("deadline").value =
        p.deadline;

    document.getElementById("companyType").value =
        p.company_preference;

    document.getElementById("frequency").value =
        p.email_frequency;

    /*
       Clear all location checkboxes first.
    */

    document
        .querySelectorAll(
            '.location-grid input[type="checkbox"]'
        )
        .forEach(function(box) {

            box.checked =
                p.locations.includes(box.value);

        });

    /*
       Anything that isn't one of the
       predefined locations goes into
       the custom location field.
    */

    const predefinedLocations = [

        "Mumbai",
        "Pune",
        "Bengaluru",
        "Hyderabad",
        "Delhi NCR",
        "Chennai",
        "Kolkata",
        "Ahmedabad",
        "Noida",
        "Gurugram",
        "Remote",
        "Anywhere in India"

    ];

    const customLocations =
        p.locations.filter(
            location =>
                !predefinedLocations.includes(location)
        );

    document.getElementById("customLocation").value =
        customLocations.join(", ");

    document.getElementById("preferenceEmail").textContent =
        user.email;

    showPage(preferencesPage);

});


/* =========================================
   LOGOUT
========================================= */

function logout() {

    clearUser();

    loginForm.reset();

    preferencesForm.reset();

    showPage(loginPage);

}


logoutBtn.addEventListener("click", logout);

dashboardLogout.addEventListener("click", logout);


/* =========================================
   INITIAL LOAD
========================================= */

const existingUser = getUser();

if (existingUser) {

    if (existingUser.preferences) {

        loadDashboard(existingUser);

        showPage(dashboardPage);

    } else {

        document.getElementById("preferenceEmail").textContent =
            existingUser.email;

        showPage(preferencesPage);

    }

} else {

    showPage(loginPage);

}
