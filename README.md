# RCOS IO

## Local Development

### Requirements

- Python 3.11+

### Setup

1. Clone repository
2. Create the virtual environment in the project folder `python3.11 -m venv ./venv`
3. Activate virtual environment `source ./venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Create a `.env` file (not the placement of the `.`) and add environment values
    - see `.env.example` for the expected variables
6. Setup database `./manage.py migrate`
7. Create a superuser for testing `./manage.py createsuperuser`
8. Ask existing maintainers for data JSON file


### Running

1. `./manage.py runserver`
2. Navigate to http://127.0.0.1:8000/auth/login/ and enter the email of your superuser and choose "Login (admin)"

## Deploying to RCOS IO

1. `git push origin main:production`
