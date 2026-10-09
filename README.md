# InternFlow — Personalized Internship Discovery Platform
[🌐 View InternFlow Live](https://intern-flow-ckh9.onrender.com/)

**Discover relevant internships. Track opportunities. Stay updated.**

InternFlow is a web-based internship discovery platform designed to help students find internship opportunities that align with their skills, preferred domain, location, and stipend expectations. It uses web search and AI-powered information extraction to organize internship listings into structured, easier-to-explore results.

## Problem Statement

Students often spend significant time searching across multiple websites for internships that match their technical skills, preferred locations, and financial expectations. Relevant opportunities can be difficult to identify, and application deadlines can be easy to miss.

InternFlow aims to simplify this process by bringing internship discovery, skill-based matching, and personalized email updates into one platform.

## Objectives

* Simplify internship discovery for students.
* Identify opportunities relevant to a student's skills and career interests.
* Extract important internship details into a structured format.
* Help students discover opportunities matching their location and stipend preferences.
* Provide automated email updates about relevant opportunities.

## Key Features

* **Personalized Preferences:** Save skills, preferred internship domain, location, stipend requirements, and email preferences.
* **AI-Powered Information Extraction:** Extract internship details from web search results using an AI model.
* **Skill-Based Matching:** Compare student skills with internship requirements and calculate a match percentage.
* **Missing Skills Identification:** Show which required skills are not present in the student's skill list.
* **Internship Details:** Organize available information such as company, role, location, stipend, duration, eligibility, deadline, and application link.
* **Search Result Filtering:** Filter out unwanted pages and validate internship information using predefined checks.
* **Application Link Verification:** Check whether application URLs are reachable before including opportunities.
* **Automated Email Updates:** Send internship updates based on saved student preferences through an automated workflow.
* **Duplicate Handling:** Reduce duplicate internship listings in search results.

## How It Works

1. The student enters their skills and internship preferences.
2. InternFlow searches the web for relevant internship opportunities.
3. AI extracts structured information from the search results.
4. The system validates and filters the extracted information.
5. Student skills are compared with the internship's required skills.
6. Matching percentage, matched skills, and missing skills are calculated.
7. Relevant internship information is displayed to the student.
8. The automation workflow can send personalized internship updates by email.

## Technology Stack

| Component             | Technology                |
| --------------------- | ------------------------- |
| Frontend              | HTML, CSS, JavaScript     |
| Backend               | Python, Flask             |
| AI-powered extraction | Gemini API                |
| Web search            | Tavily API                |
| Database              | SQLite                    |
| Email automation      | Python and GitHub Actions |
| Deployment            | Render                    |
| Version control       | Git and GitHub            |

## System Architecture

```text
Student
   |
   v
Frontend
   |
   v
Flask Backend
   |
   v
Tavily Web Search
   |
   v
AI Information Extraction
   |
   v
Validation and Filtering
   |
   v
Skill Matching
   |
   v
Internship Results
```

**Email automation workflow:**

```text
Saved Student Preferences
          |
          v
Scheduled GitHub Actions Workflow
          |
          v
Internship Processing
          |
          v
Personalized Email Updates
```

## Project Structure

```text
InternFlow/
├── AI/
│   ├── pipeline.py
│   ├── matching.py
│   ├── gemini_client.py
│   ├── stipend.py
│   └── verify_application.py
├── backend.py
├── automation.py
├── internflow.db
├── requirements.txt
├── .gitignore
└── README.md
```

*The exact folder structure may vary depending on the current repository version.*

## Getting Started

### Prerequisites

* Python 3.10 or a compatible version supported by the dependencies
* Git
* Tavily API key
* Gemini API key, if using Gemini-powered extraction

### 1. Clone the Repository

```bash
git clone https://github.com/Janavipixel/InternFlow.git
cd InternFlow
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

Activate it on Windows:

```bash
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file in the project root and add the API keys required by your implementation.

```env
TAVILY_API_KEY=your_tavily_api_key
GEMINI_API_KEY=your_gemini_api_key
```

Check `AI/gemini_client.py` for the exact environment variable name expected by your current implementation.

**Security:** Never commit `.env`, API keys, email passwords, or other secrets to GitHub.

### 5. Run the Application

Start the Flask backend using:

```bash
python backend.py
```

If your frontend is served separately, configure it to use the backend's correct API URL.

### 6. Run the Email Automation Locally

If configured in your environment, run:

```bash
python automation.py
```

Make sure all required database settings, environment variables, and email credentials are configured before running the automation.

## Deployment

The backend is deployed on Render.

**Live application:** https://intern-flow-ckh9.onrender.com/

The application may depend on external API availability, configured environment variables, and deployment status.

## Security and Limitations

* API keys and email credentials should be stored as environment variables or repository secrets.
* AI-extracted information may be incomplete or inaccurate and should be verified before applying.
* A reachable application URL does not guarantee that the internship is genuine or that applications are still open.
* Search results depend on the availability and quality of indexed web content.
* Internship details and deadlines may change after extraction.

## Future Improvements

* More robust verification of internship authenticity and application status.
* Improved matching using skill synonyms and related technologies.
* Better filtering by eligibility, duration, and work mode.
* Internship bookmarking and application-status tracking.
* Expanded analytics on skill demand and internship trends.

## Contributors

Developed as a collaborative student software project.


