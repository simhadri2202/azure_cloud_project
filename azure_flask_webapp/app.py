from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import text 
# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# @app.route('/')
# def home():
#     # Renders the registration form on the homepage
#     return render_template('index.html')
@app.route('/')
def index():
    try:
        # Test the connection by querying the database
        result = db.session.execute(text("SELECT 1"))
        return "Database connection successful!"
    except Exception as e:
        return f"Database connection failed: {e}"
    
@app.route('/register', methods=['POST'])
def register():
    # Retrieves the form data
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']

    result = db.session.execute(text("SELECT 1"))
    return "Database connection successful!"

    
    # In a real-world application, you should hash the password and save user details to a database
    
    # Return a response confirming the registration (or ideally redirect to a confirmation page)
    # return f"User {username} with email {email} successfully registered!!"

if __name__ == '__main__':
    app.run(debug=True)
