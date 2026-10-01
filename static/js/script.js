/* =========================================
   QUEUEFLOW
   DIGITAL QUEUE AUTOMATION

   Frontend-only version.
   Mock data will later be replaced
   by backend API calls.
========================================= */


/* =========================================
   INITIAL QUEUE DATA
========================================= */

const queueData = [
    {
        id: 1,
        ticket: "A-104",
        name: "Aarav Mehta",
        service: "Account Support",
        priority: "priority",
        joinedAt: Date.now() - (18 * 60 * 1000),
        status: "waiting"
    },
    {
        id: 2,
        ticket: "A-105",
        name: "Riya Shah",
        service: "Document Service",
        priority: "normal",
        joinedAt: Date.now() - (13 * 60 * 1000),
        status: "waiting"
    },
    {
        id: 3,
        ticket: "A-106",
        name: "Kabir Joshi",
        service: "Payment Desk",
        priority: "normal",
        joinedAt: Date.now() - (9 * 60 * 1000),
        status: "waiting"
    },
    {
        id: 4,
        ticket: "A-107",
        name: "Nisha Patel",
        service: "General Enquiry",
        priority: "priority",
        joinedAt: Date.now() - (6 * 60 * 1000),
        status: "waiting"
    },
    {
        id: 5,
        ticket: "A-108",
        name: "Arjun Rao",
        service: "Account Support",
        priority: "normal",
        joinedAt: Date.now() - (3 * 60 * 1000),
        status: "waiting"
    }
];


/* =========================================
   APPLICATION STATE
========================================= */

let queue = [...queueData];

let servedToday = 27;

let ticketNumber = 109;

let activityData = [
    {
        icon: "✓",
        title: "Ticket A-103 was served",
        detail: "Counter 02 completed the request",
        time: "4 min ago"
    },
    {
        icon: "+",
        title: "A new customer joined",
        detail: "Ticket A-108 entered the queue",
        time: "3 min ago"
    },
    {
        icon: "→",
        title: "Ticket A-104 marked priority",
        detail: "Queue position updated automatically",
        time: "2 min ago"
    },
    {
        icon: "●",
        title: "Counter 03 became available",
        detail: "Ready for the next customer",
        time: "1 min ago"
    }
];


const counters = [
    {
        id: "01",
        name: "Counter 01",
        status: "busy",
        ticket: "A-101"
    },
    {
        id: "02",
        name: "Counter 02",
        status: "busy",
        ticket: "A-102"
    },
    {
        id: "03",
        name: "Counter 03",
        status: "available",
        ticket: "Ready"
    },
    {
        id: "04",
        name: "Counter 04",
        status: "available",
        ticket: "Ready"
    }
];


/* =========================================
   DOM ELEMENTS
========================================= */

const queueTableBody = document.getElementById("queueTableBody");

const emptyQueue = document.getElementById("emptyQueue");

const queueSearch = document.getElementById("queueSearch");

const queueFilter = document.getElementById("queueFilter");

const queueForm = document.getElementById("queueForm");

const customerName = document.getElementById("customerName");

const serviceType = document.getElementById("serviceType");

const waitingCount = document.getElementById("waitingCount");

const averageWait = document.getElementById("averageWait");

const servedCount = document.getElementById("servedCount");

const activeCounters = document.getElementById("activeCounters");

const sidebarQueueCount = document.getElementById("sidebarQueueCount");

const currentDate = document.getElementById("currentDate");

const counterList = document.getElementById("counterList");

const activityList = document.getElementById("activityList");

const refreshQueue = document.getElementById("refreshQueue");

const notificationButton = document.getElementById("notificationButton");

const viewCounters = document.getElementById("viewCounters");

const toast = document.getElementById("toast");

const toastTitle = document.getElementById("toastTitle");

const toastMessage = document.getElementById("toastMessage");


/* =========================================
   INITIALISE APPLICATION
========================================= */

document.addEventListener("DOMContentLoaded", () => {

    updateDate();

    renderQueue();

    updateStats();

    renderCounters();

    renderActivity();

    setupNavigation();

    updateWaitTimes();

});


/* =========================================
   DATE
========================================= */

function updateDate() {

    const now = new Date();

    const formattedDate = now.toLocaleDateString("en-IN", {
        weekday: "long",
        day: "numeric",
        month: "short",
        year: "numeric"
    });

    currentDate.textContent = formattedDate;
}


/* =========================================
   CALCULATE WAIT TIME
========================================= */

function getWaitMinutes(joinedAt) {

    const difference = Date.now() - joinedAt;

    return Math.max(
        1,
        Math.floor(difference / (1000 * 60))
    );
}


/* =========================================
   GET INITIALS
========================================= */

function getInitials(name) {

    const words = name.trim().split(" ");

    if (words.length === 1) {
        return words[0].slice(0, 2).toUpperCase();
    }

    return (
        words[0][0] +
        words[words.length - 1][0]
    ).toUpperCase();
}


/* =========================================
   RENDER QUEUE
========================================= */

function renderQueue() {

    const searchValue = queueSearch.value
        .trim()
        .toLowerCase();

    const filterValue = queueFilter.value;


    let filteredQueue = queue.filter(person => {

        const matchesSearch =
            person.name.toLowerCase().includes(searchValue) ||
            person.ticket.toLowerCase().includes(searchValue) ||
            person.service.toLowerCase().includes(searchValue);


        let matchesFilter = true;

        if (filterValue === "waiting") {
            matchesFilter = person.status === "waiting";
        }

        if (filterValue === "priority") {
            matchesFilter = person.priority === "priority";
        }


        return matchesSearch && matchesFilter;
    });


    /* Priority customers appear first */

    filteredQueue.sort((a, b) => {

        if (
            a.priority === "priority" &&
            b.priority !== "priority"
        ) {
            return -1;
        }

        if (
            a.priority !== "priority" &&
            b.priority === "priority"
        ) {
            return 1;
        }

        return a.joinedAt - b.joinedAt;
    });


    queueTableBody.innerHTML = "";


    if (filteredQueue.length === 0) {

        emptyQueue.classList.remove("hidden");

        return;
    }


    emptyQueue.classList.add("hidden");


    filteredQueue.forEach(person => {

        const row = document.createElement("tr");

        const wait = getWaitMinutes(person.joinedAt);

        const priorityLabel =
            person.priority === "priority"
                ? "Priority"
                : "Normal";

        const statusLabel =
            person.status === "serving"
                ? "Serving"
                : "Waiting";


        row.innerHTML = `
            <td>
                <span class="ticket-number">
                    ${person.ticket}
                </span>
            </td>

            <td>
                <div class="customer-cell">

                    <div class="customer-avatar">
                        ${getInitials(person.name)}
                    </div>

                    <span class="customer-name">
                        ${person.name}
                    </span>

                </div>
            </td>

            <td>
                <span class="service-name">
                    ${person.service}
                </span>
            </td>

            <td>
                <span class="wait-time">
                    ${wait} min
                </span>
            </td>

            <td>
                <span class="priority-badge ${person.priority}">
                    ${priorityLabel}
                </span>
            </td>

            <td>
                <span class="status-badge ${person.status}">
                    ${statusLabel}
                </span>
            </td>

            <td>
                <button
                    class="row-action"
                    data-ticket="${person.ticket}"
                >
                    ${person.status === "serving"
                        ? "Complete"
                        : "Call next"}
                </button>
            </td>
        `;


        queueTableBody.appendChild(row);
    });


    attachQueueActions();
}


/* =========================================
   QUEUE ACTION BUTTONS
========================================= */

function attachQueueActions() {

    const actionButtons =
        document.querySelectorAll(".row-action");


    actionButtons.forEach(button => {

        button.addEventListener("click", () => {

            const ticket =
                button.dataset.ticket;

            handleQueueAction(ticket);
        });

    });
}


/* =========================================
   HANDLE QUEUE ACTION
========================================= */

function handleQueueAction(ticket) {

    const person =
        queue.find(item => item.ticket === ticket);


    if (!person) {
        return;
    }


    if (person.status === "waiting") {

        person.status = "serving";

        addActivity(
            "→",
            `${person.ticket} called to counter`,
            `${person.name} is now being served`,
            "Just now"
        );

        showToast(
            "Customer called",
            `${person.ticket} is now being served.`
        );

    } else {

        queue = queue.filter(
            item => item.id !== person.id
        );

        servedToday++;

        addActivity(
            "✓",
            `${person.ticket} was completed`,
            `${person.name}'s request was completed`,
            "Just now"
        );

        showToast(
            "Service completed",
            `${person.ticket} has been removed from the queue.`
        );
    }


    renderQueue();

    updateStats();

    renderActivity();
}


/* =========================================
   ADD CUSTOMER TO QUEUE
========================================= */

queueForm.addEventListener("submit", event => {

    event.preventDefault();


    const name =
        customerName.value.trim();

    const service =
        serviceType.value;

    const priority =
        document.querySelector(
            'input[name="priority"]:checked'
        ).value;


    if (!name || !service) {

        showToast(
            "Missing information",
            "Please complete the required fields."
        );

        return;
    }


    const newTicket = {

        id: Date.now(),

        ticket: `A-${ticketNumber}`,

        name: name,

        service: service,

        priority: priority,

        joinedAt: Date.now(),

        status: "waiting"
    };


    ticketNumber++;


    queue.push(newTicket);


    addActivity(
        "+",
        `${newTicket.ticket} added to queue`,
        `${newTicket.name} joined ${newTicket.service}`,
        "Just now"
    );


    queueForm.reset();


    renderQueue();

    updateStats();

    renderActivity();


    showToast(
        "Customer added",
        `${newTicket.ticket} has been added to the queue.`
    );
});


/* =========================================
   SEARCH
========================================= */

queueSearch.addEventListener(
    "input",
    renderQueue
);


/* =========================================
   FILTER
========================================= */

queueFilter.addEventListener(
    "change",
    renderQueue
);


/* =========================================
   UPDATE STATISTICS
========================================= */

function updateStats() {

    const waitingPeople =
        queue.filter(
            person => person.status === "waiting"
        );


    waitingCount.textContent =
        waitingPeople.length;


    sidebarQueueCount.textContent =
        waitingPeople.length;


    servedCount.textContent =
        servedToday;


    const busyCounters =
        counters.filter(
            counter => counter.status === "busy"
        );


    activeCounters.textContent =
        busyCounters.length;


    if (waitingPeople.length === 0) {

        averageWait.textContent = "0";

        return;
    }


    const totalWait =
        waitingPeople.reduce(
            (total, person) =>
                total + getWaitMinutes(person.joinedAt),
            0
        );


    const average =
        Math.round(
            totalWait / waitingPeople.length
        );


    averageWait.textContent =
        average;
}


/* =========================================
   LIVE WAIT TIME UPDATE
========================================= */

function updateWaitTimes() {

    renderQueue();

    updateStats();
}


/* Update every minute */

setInterval(
    updateWaitTimes,
    60000
);


/* =========================================
   RENDER COUNTERS
========================================= */

function renderCounters() {

    counterList.innerHTML = "";


    counters.forEach(counter => {

        const card =
            document.createElement("div");


        card.className =
            "counter-card";


        const statusText =
            counter.status === "busy"
                ? "Busy"
                : "Available";


        card.innerHTML = `

            <div class="counter-top">

                <div class="counter-name">

                    <div class="counter-number">
                        ${counter.id}
                    </div>

                    ${counter.name}

                </div>

                <div class="counter-status ${counter.status}">

                    <span></span>

                    ${statusText}

                </div>

            </div>

            <div class="counter-ticket">

                Current ticket:

                <strong>
                    ${counter.ticket}
                </strong>

            </div>
        `;


        counterList.appendChild(card);
    });
}


/* =========================================
   RENDER ACTIVITY
========================================= */

function renderActivity() {

    activityList.innerHTML = "";


    activityData
        .slice(0, 5)
        .forEach(activity => {

            const item =
                document.createElement("div");


            item.className =
                "activity-item";


            item.innerHTML = `

                <div class="activity-icon">
                    ${activity.icon}
                </div>

                <div class="activity-text">

                    <strong>
                        ${activity.title}
                    </strong>

                    <span>
                        ${activity.detail}
                    </span>

                </div>

                <span class="activity-time">
                    ${activity.time}
                </span>
            `;


            activityList.appendChild(item);
        });
}


/* =========================================
   ADD ACTIVITY
========================================= */

function addActivity(
    icon,
    title,
    detail,
    time
) {

    activityData.unshift({

        icon: icon,

        title: title,

        detail: detail,

        time: time
    });


    if (activityData.length > 8) {

        activityData =
            activityData.slice(0, 8);
    }
}


/* =========================================
   TOAST MESSAGE
========================================= */

let toastTimer;


function showToast(
    title,
    message
) {

    toastTitle.textContent =
        title;

    toastMessage.textContent =
        message;


    toast.classList.add("show");


    clearTimeout(toastTimer);


    toastTimer =
        setTimeout(() => {

            toast.classList.remove("show");

        }, 3500);
}


/* =========================================
   REFRESH BUTTON
========================================= */

refreshQueue.addEventListener(
    "click",
    () => {

        renderQueue();

        updateStats();

        showToast(
            "Queue refreshed",
            "The live queue has been updated."
        );
    }
);


/* =========================================
   NOTIFICATION BUTTON
========================================= */

notificationButton.addEventListener(
    "click",
    () => {

        showToast(
            "No new alerts",
            "Everything is running normally."
        );
    }
);


/* =========================================
   VIEW COUNTERS
========================================= */

viewCounters.addEventListener(
    "click",
    () => {

        document
            .querySelector(".counters-panel")
            .scrollIntoView({
                behavior: "smooth",
                block: "center"
            });

    }
);


/* =========================================
   SIDEBAR NAVIGATION
========================================= */

function setupNavigation() {

    const navItems =
        document.querySelectorAll(".nav-item");


    navItems.forEach(item => {

        item.addEventListener("click", () => {

            navItems.forEach(nav => {
                nav.classList.remove("active");
            });


            item.classList.add("active");


            const section =
                item.dataset.section;


            if (section === "dashboard") {

                window.scrollTo({
                    top: 0,
                    behavior: "smooth"
                });

                return;
            }


            if (section === "queue") {

                document
                    .querySelector(".queue-panel")
                    .scrollIntoView({
                        behavior: "smooth",
                        block: "start"
                    });

                return;
            }


            if (section === "counters") {

                document
                    .querySelector(".counters-panel")
                    .scrollIntoView({
                        behavior: "smooth",
                        block: "center"
                    });

                return;
            }


            if (section === "activity") {

                document
                    .querySelector(".activity-panel")
                    .scrollIntoView({
                        behavior: "smooth",
                        block: "center"
                    });

                return;
            }


            if (section === "settings") {

                showToast(
                    "Settings",
                    "System settings will be connected later."
                );
            }

        });

    });
}
