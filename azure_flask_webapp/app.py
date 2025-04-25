from flask import Flask, render_template, request,redirect, url_for
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

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # Ensure the password is hashed

@app.route('/')
def home():
    # Renders the registration form on the homepage
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Get the credentials from the form
        username = request.form['username']
        password = request.form['password']

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Compare passwords (ensure hashing in production)
            return redirect(url_for('dashboard'))
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    return "Welcome to the dashboard!"

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
