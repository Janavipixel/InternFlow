# InternFlow

InternFlow is an internship discovery and management system that helps students find, track, and manage internship opportunities.

## Backend & Automation

The backend provides APIs for storing internship information, tracking application status, and checking upcoming deadlines.

### Features

- Add internship opportunities
- View available internships
- Track application status
- Detect internships with upcoming deadlines
- Send automated email reminders for approaching deadlines
- Store internship data using SQLite
- Use environment variables for secure email credentials
- GitHub Actions workflow prepared for scheduled automation

## Backend Technologies

- Python
- Flask
- SQLite
- Python-dotenv
- SMTP / Gmail

## API Endpoints

### Add an Internship

```text
POST /internships