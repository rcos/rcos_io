# RCOS IO

## Local Development

### Requirements

- Python 3.10+
- a Postgres database

### Setup

1. Clone repository
2. Create the virtual environment in the project folder `python3.11 -m venv ./venv`
3. Activate virtual environment `source ./venv/bin/activate`
4. Install requirements `pip install -r requirements.txt`
5. Create a `.env` file (not the placement of the `.`) and add environment values
    - see `.env.example` for the expected variables
6. Setup database `./manage.py migrate`
7. ~~Load test data (optional) `./manage.py loaddata full`~~ coming soon


### Running

1. `./manage.py runserver`