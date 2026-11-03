
# Teachers Pet

**FIU Study Location Finder | Software Engineering II**  
**Team:** Teacher Pets Dev's

## Overview

Teachers Pet is a web application designed to help Florida International University (FIU) students discover suitable study locations across campus.

Students can search for available study spaces, filter locations based on amenities, view recent crowd information, submit reviews, receive personalized recommendations, and access navigation information.

The application follows a **layered client-server architecture** with a modular Django backend, a React frontend, and PostgreSQL for persistent data storage.

## Features

| ID | Feature | Description |
|---|---|---|
| FR-01 | Study Location Search | Search, browse, and filter available campus study locations. |
| FR-02 | Location Details | View study location information, amenities, and crowd levels. |
| FR-03 | Crowd Reports | Submit crowd-level reports that remain current for 45 minutes. |
| FR-04 | Reviews | Submit and view reviews for study locations. |
| FR-05 | Recommendations | Receive recommendations based on location attributes and preferences. |
| FR-06 | Maps & Navigation | View study locations on a map and access navigation information. |
| FR-07 | Location Management | Allow authorized FIU staff to manage official study-location information. |

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, TypeScript, Vite, Tailwind CSS |
| State Management | TanStack Query |
| Backend | Python, Django, Django REST Framework |
| Database | PostgreSQL 17 |
| Caching | Redis |
| Infrastructure | Docker & Docker Compose |
| Dependency Management | uv |
| Version Control | Git |
| Backend Testing | pytest, pytest-django |
| Frontend Testing | Vitest, React Testing Library |

## System Architecture

Teachers Pet uses a **three-tier layered client-server architecture**.

### 1. Presentation Layer

The React frontend handles user interactions, rendering, navigation, forms, and displaying data retrieved from the backend.

### 2. Application Layer

The Django REST Framework backend handles business logic, authentication, API endpoints, input validation, and communication with the database.

### 3. Data Layer

PostgreSQL stores persistent application data, including users, locations, amenities, reviews, and crowd reports.

Redis supports caching and efficient retrieval of frequently accessed data.

```text
           React + TypeScript
          Presentation Layer
                  |
             REST API
                  |
         Django REST Framework
        Application/Business Layer
                  |
           Django ORM
                  |
              PostgreSQL
              Data Layer

         Redis (Caching Layer)
```

## Project Structure

```text
teachers_pet/
│
├── backend/
│   ├── apps/
│   │   ├── __init__.py
│   │   ├── accounts/
│   │   ├── locations/
│   │   ├── crowd_reports/
│   │   ├── reviews/
│   │   └── recommendations/
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   ├── asgi.py
│   │   └── wsgi.py
│   │
│   ├── manage.py
│   └── templates/
│
├── frontend/
├── docs/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pyproject.toml
├── uv.lock
└── README.md
```

### Backend Applications

| Application | Responsibility |
|---|---|
| accounts | User accounts, authentication, and permissions |
| locations | Study locations, amenities, search, and filtering |
| crowd_reports | Crowd-level submissions and report expiration |
| reviews | Student reviews and feedback |
| recommendations | Study-space recommendation logic |
| config | Central Django configuration and URL routing |

Each Django application is responsible for its own models, views, serializers, URLs, and business logic.

## Development Setup

### Prerequisites

Install the following:

- Python 3.12+
- Git
- uv
- Docker Desktop
- Node.js (LTS)
- PyCharm or Visual Studio Code

### 1. Clone the Repository

```bash
git clone <REPOSITORY_URL>
cd teachers_pet
```

Replace `<REPOSITORY_URL>` with the team's Git repository URL.

### 2. Install Backend Dependencies

Python dependencies are managed using **uv**.

From the project root, run:

```bash
uv sync --locked
```

This installs the dependency versions specified in `uv.lock`.

If dependencies need to be added, use:

```bash
uv add package-name
```

Do not manually modify the lockfile.

### 3. Configure Environment Variables

Create a `.env` file using the provided example:

```powershell
Copy-Item .env.example .env
```

Update the required environment variables for Django, PostgreSQL, and Redis.

Never commit `.env` or any credentials to version control.

### 4. Start Database Services

PostgreSQL and Redis will run using Docker Compose.

Once the services are configured, run:

```bash
docker compose up -d
```

To stop the containers:

```bash
docker compose down
```

### 5. Run Django

From the project root:

```bash
uv run python backend/manage.py check
```

Once PostgreSQL is configured and running, apply migrations:

```bash
uv run python backend/manage.py migrate
```

Start the development server:

```bash
uv run python backend/manage.py runserver
```

The backend will typically be available at:

http://127.0.0.1:8000/

### 6. Run the Frontend

Once the React application is initialized:

```bash
cd frontend
npm install
npm run dev
```

Use the frontend URL displayed by Vite.

## Development Guidelines

### Branching Strategy

All development should occur on feature branches.

Examples:

```text
feature/location-search
feature/user-authentication
feature/crowd-reports
feature/recommendations
fix/review-validation
```

### Commit Conventions

Use descriptive commit messages.

Examples:

```text
feat: implement location search endpoint
fix: correct crowd report expiration logic
refactor: separate location business logic
test: add location API tests
docs: update development instructions
chore: configure Django project structure
```

### Pull Request Guidelines

1. Create a feature branch.
2. Implement and test the assigned functionality.
3. Push the branch to the remote repository.
4. Open a pull request.
5. Obtain at least one teammate review for major changes.
6. Merge after approval.

Avoid pushing unfinished features directly to the stable branch.

### Backend Coding Standards

- Use `snake_case` for Python functions, variables, and files.
- Use `PascalCase` for Python classes.
- Keep Django applications modular.
- Place database models in `models.py`.
- Place DRF serializers in `serializers.py`.
- Define API endpoints in `views.py`.
- Define application routes in `urls.py`.
- Place substantial business logic in `services.py` when appropriate.
- Write tests for important functionality.
- Avoid storing credentials directly in source code.

### Frontend Coding Standards

- Use reusable React components.
- Use TypeScript for type safety.
- Keep API requests separate from presentation components.
- Follow consistent component naming conventions.
- Use Tailwind CSS for styling.
- Maintain responsive layouts.

## Testing

### Backend

Run backend tests using:

```bash
uv run pytest backend
```

Tests should cover:

- Study-location search and filtering
- API validation
- Authentication and authorization
- Crowd report submission
- 45-minute crowd report expiration
- Review submission
- Database consistency

### Frontend

Once configured, run:

```bash
cd frontend
npm run test
```

The frontend test command must be defined in `package.json`.

## Team Members

| Team Member | Role |
|---|---|
| Mark-Anthony Delva | Backend Developer |
| Jamar Morisseau | Frontend Developer |
| Mahadi Rahman | QA / Requirements Engineer |
| Bishal Ghosh | Full Stack / Integration Developer |

## Project Management

The team follows a lightweight Agile development approach.

Team members are responsible for their assigned components, while collaboration and code reviews help maintain consistency throughout development.

Weekly meetings will be used to discuss progress, identify blockers, review completed work, and coordinate integration.

### Development Workflow

1. Environment and database setup
2. Backend models and REST API development
3. Frontend components and pages
4. Frontend/backend integration
5. Map service integration
6. Unit testing and bug fixes
7. Final integration testing

## Project Documentation

The `docs/` directory contains the project's design and planning documentation.

- **Deliverable 2:** Software Specifications, Architecture & Model
- **Deliverable 3:** Project Planning
- **Deliverable 4:** Component-Level System Design

These documents define the system requirements, architecture, planned components, development responsibilities, and implementation approach.

## Implementation Checklist

- [x] Initialize Django project
- [x] Establish backend and frontend directories
- [x] Create Django application modules
- [ ] Verify Django application registration
- [ ] Finalize uv dependency management
- [ ] Configure PostgreSQL using Docker
- [ ] Configure Redis using Docker
- [ ] Configure environment variables
- [ ] Implement Django models
- [ ] Implement REST API endpoints
- [ ] Initialize React frontend
- [ ] Implement frontend components
- [ ] Integrate frontend and backend
- [ ] Integrate maps and navigation
- [ ] Add unit and integration tests
- [ ] Complete final system testing

## Security Considerations

The system is designed to include:

- Secure authentication and role-based access
- HTTPS communication
- Input validation
- Protection against common web vulnerabilities
- Audit logging for important system events
- Approval workflows for sensitive administrative changes
- Environment-based secret management

Security requirements will be implemented and verified throughout development.

---
