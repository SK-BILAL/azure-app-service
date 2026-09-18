from flask import Flask
import os
import psycopg2
from psycopg2 import OperationalError

app = Flask(__name__)


# ---------------------------------------------------------
# Application Configuration
# ---------------------------------------------------------

APP_ENV = os.environ.get("APP_ENV", "development")

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT", "5432")

FLASK_SECRET = os.environ.get("FLASK_SECRET", "local-development-secret")


# ---------------------------------------------------------
# Database Connection
# ---------------------------------------------------------

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT,
        sslmode="require"
    )


# ---------------------------------------------------------
# Initialize Database
# ---------------------------------------------------------

def initialize_database():

    if not all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD]):
        return False, "Database environment variables are not configured."

    try:
        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS application_info (
                id SERIAL PRIMARY KEY,
                application_name VARCHAR(100) NOT NULL,
                environment VARCHAR(50) NOT NULL
            )
        """)

        cursor.execute("""
            SELECT COUNT(*) FROM application_info
        """)

        count = cursor.fetchone()[0]

        if count == 0:
            cursor.execute("""
                INSERT INTO application_info
                (application_name, environment)
                VALUES (%s, %s)
            """, (
                "azure-python-demo",
                APP_ENV
            ))

        connection.commit()

        cursor.close()
        connection.close()

        return True, "Database connection successful."

    except OperationalError as error:
        return False, f"Database connection failed: {error}"

    except Exception as error:
        return False, f"Database error: {error}"


# ---------------------------------------------------------
# Home Page
# ---------------------------------------------------------

@app.route("/")
def home():

    db_status, db_message = initialize_database()

    if db_status:
        database_status = "Connected"
    else:
        database_status = "Connection Failed"

    return f"""
    <html>
        <head>
            <title>Azure Python App</title>
        </head>

        <body>

            <h1>Hello from Azure App Service!</h1>

            <p>
                This is a sample Python Flask application.
            </p>

            <p>
                Latest test sample application deployed
                using Azure App Service.
            </p>

            <hr>

            <h2>Application Information</h2>

            <p>
                Environment: {APP_ENV}
            </p>

            <p>
                Database Status: {database_status}
            </p>

            <p>
                Database Message: {db_message}
            </p>

            <p>
                Key Vault Secret: Configured through App Service environment variable
            </p>

        </body>
    </html>
    """


# ---------------------------------------------------------
# Health Check
# ---------------------------------------------------------

@app.route("/health")
def health():

    db_status, db_message = initialize_database()

    return {
        "status": "healthy",
        "application": "azure-python-demo",
        "environment": APP_ENV,
        "database": "connected" if db_status else "not_connected",
        "database_message": db_message
    }


# ---------------------------------------------------------
# Database Data
# ---------------------------------------------------------

@app.route("/data")
def data():

    try:

        connection = get_db_connection()
        cursor = connection.cursor()

        cursor.execute("""
            SELECT id, application_name, environment
            FROM application_info
            ORDER BY id
        """)

        rows = cursor.fetchall()

        cursor.close()
        connection.close()

        result = "<h1>Database Records</h1>"

        for row in rows:
            result += f"""
            <p>
                ID: {row[0]} |
                Application: {row[1]} |
                Environment: {row[2]}
            </p>
            """

        return result

    except Exception as error:

        return {
            "status": "error",
            "message": str(error)
        }, 500


# ---------------------------------------------------------
# Application Entry Point
# ---------------------------------------------------------

if __name__ == "__main__":

    port = int(os.environ.get("PORT", 8000))

    app.run(
        host="0.0.0.0",
        port=port
    )