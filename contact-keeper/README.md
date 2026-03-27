# Contact Keeper — Microservice Web Application for Contact Management

## Stack
- **Backend:** Python (FastAPI)
- **Database:** PostgreSQL
- **Containerization:** Docker, Docker Compose
- **Reverse-proxy:** Nginx
- **Frontend:** Jinja2, JavaScript (AJAX)
- **Additional:** PGAdmin (database management)

## Description
A web application for contact management with a microservice architecture. Allows creating, editing, deleting, and searching contacts, organizing them into groups, and adding to favorites.

### Architecture
The application consists of 4 containers:
- **FastAPI** — backend server with business logic and REST API
- **PostgreSQL** — database
- **Nginx** — reverse-proxy, hides internal service ports
- **PGAdmin** — web interface for database management (optional)

### Key Features
- CRUD operations with contacts
- Search and filter by name, phone, group
- Groups and favorites system
- Phone number validation at database level (CHECK constraints)
- AJAX requests for dynamic interface updates

### Security
- Parameterized SQL queries (protection against SQL injection)
- Jinja2 escaping (protection against XSS)
- Running application as non-root user
- Nginx reverse-proxy hides internal service ports

### Future improvments
- Add unit tests
- Implement user authentication
- Rewrite frontend in React/Vue
- Add contact export to CSV

## How to Run

```bash
docker-compose up --build
```
## Stop the application
```bash
docker-compose down
```