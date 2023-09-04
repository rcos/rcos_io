# RCOS IO

RCOS IO is the latest iteration of an admin and member portal for the Rensselaer Center for Open Source. It was created by Coordinators in 2022 and will be maintained by alumnus Frank Matranga until at least 2028, solving the issue of loss of experience as student leadership comes and goes.

## Motivation

RCOS has to handle the data of typically 150+ students each semester (even 100+ students during summer semesters). Data includes enrolled students, external organizations and their users, projects, semester enrollments, meetings, mentors, small groups, etc. Most of the operations are straightforward CRUD operations (Create Read Update Destroy) and the data does not often change. As a result, a traditional web application using a relational database is a good choice. Django was chosen because it is batteries-included and opinionated, and Python is a very well-known and accessible language to develop and deploy.

## Stack

- Python [Django](https://www.djangoproject.com/) backend
- Plain old HTML frontend using
    - [Bulma CSS library](https://bulma.io/documentation/)
- HTMX (coming soon)
- [PostgreSQL](https://www.postgresql.org/) database
- [Redis](https://redis.io/) cache

## Local Development

### Requirements

- Python 3.11+
- [Poetry](https://python-poetry.org/docs/#installation)

### Setup

1. Clone repository
2. Install dependencies `poetry install`
3. Create a `.env` file (not the placement of the `.`) and add environment values
    - see `.env.example` for the expected variables
4. Activate Poetry shell `poetry shell`
5. Setup database `./manage.py migrate` OR ask maintainers for test data DB file
6. Setup cache table in database `./manage.py createcachetable`
7. Create a superuser for testing `./manage.py createsuperuser`


### Running

1. `poetry shell`
2. `./manage.py runserver`
3. Navigate to http://127.0.0.1:8000/auth/login/ and enter the email of your superuser and choose "Login (admin)"

## Deploying to Production

1. `git push origin main:production`

## Updating Dependencies

We use [MEND Renovate](https://www.mend.io/renovate/) to automatically open dependency update PRs.

To manually update dependencies, run `poetry update`.