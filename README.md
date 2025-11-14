Project Description

SafeWallet is the backend component of a wallet-type application. It provides APIs (via Flask) to manage sessions, user accounts, database queries, and more. The project currently contains files such as main.py, main_flask.py, db_query.py, session.py, and a requirements.txt.
You can extend it further by adding authentication, wallet transactions, front-end UI, etc.

Features

Flask-based web server (main_flask.py)

Database query utilities (db_query.py)

Session management (session.py)

Basic “main” entrypoint script (main.py)

Easy to install with requirements.txt

Prerequisites

Before you begin, ensure you have the following installed:

Python 3.8+ (or latest compatible version)

pip (the Python package installer)

Git (for cloning the repo)

A relational database (e.g., PostgreSQL, MySQL, SQLite) — whichever the db_query.py uses or you choose to configure

(Optional) virtual environment tool (venv, virtualenv, pipenv)

Getting Started (Development Setup)
1. Clone the repository
git clone https://github.com/Abdulsalam9977/safewallet.git  
cd safewallet  

2. Create a virtual environment

It is recommended to use a virtual environment to isolate dependencies. For example:

python3 -m venv venv  
# On Windows:
# python -m venv venv


Then activate it:
On macOS/Linux:

source venv/bin/activate  


On Windows (PowerShell):

.\venv\Scripts\Activate  

3. Install dependencies

With your virtual environment activated:

pip install --upgrade pip  
pip install -r requirements.txt  

4. Configure environment variables / settings

You may need to configure specific settings for your environment. Common steps:

Create a .env file (or similar) in the project root.

Define variables such as:

FLASK_APP=main_flask.py
FLASK_ENV=development
DATABASE_URL=your_database_connection_string
SECRET_KEY=your_secret_key
HOST=redis_host
PORT=redis_port
DECODE_RESPONSES=response
REDIS_USERNAME=redis_username
PASSWORD=redis_password

If your db_query.py expects a particular DB URL or credentials, update accordingly.

If any other configuration (such as for sessions, logging, API keys) is required, define those variables.

5. Set up the database

Depending on how db_query.py is implemented:

If using SQLite, ensure you have the file path configured.

If using PostgreSQL/MySQL, ensure the database server is running and the credential details in DATABASE_URL are correct.

Create the necessary tables/schema if they are not auto-created. (You may have to run migrations or manually create tables.)

Optionally, seed initial data.

6. Run the application

With everything configured and dependencies installed, you can start the server:

# If using flask CLI:
flask run

# Or using python directly:
python main_flask.py


The server will run in development mode (if FLASK_ENV=development) and will listen on the default port (usually http://127.0.0.1:5000
).
You can test endpoints (e.g., using Postman, curl) accessing the APIs you define in the project.
