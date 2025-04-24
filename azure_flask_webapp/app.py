from flask import Flask, render_template, request, redirect, url_for
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash
from sqlalchemy import text
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Flask app
app = Flask(__name__)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@"
    f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize SQLAlchemy
db = SQLAlchemy(app)

# Define User model
class User(db.Model):
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

# Home route to test DB connection
@app.route('/')
def index():
    return render_template('register.html')

# Route to show the registration form
@app.route('/register', methods=['GET'])
def show_register_form():
    return render_template('register.html')

# Route to handle form submission and save user to DB
@app.route('/register', methods=['POST'])
def register():
    username = request.form['username']
    firstname = request.form['firstname']
    lastname = request.form['lastname']
    email = request.form['email']
    password = request.form['password']

    # Hash the password before saving
    # hashed_password = generate_password_hash(password)

    # Create a new user instance
    new_user = User(
        username=username,
        first_name=firstname,
        last_name=lastname,
        email=email,
        password=password
        #password=hashed_password
    )

    # Add and commit the user to the database
    try:
        db.session.add(new_user)
        db.session.commit()
        return render_template('success.html')
        #return f"User {username} registered successfully!"
        # Optionally redirect to login: return redirect(url_for('login'))
    except Exception as e:
        db.session.rollback()
        return f"Registration failed: {e}"

# Success route after registration
@app.route('/success')
def success():
    return render_template('success.html')

@app.route('/login')
def signin():
    return render_template('login.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
