from flask import Flask, render_template, request

app = Flask(__name__)

@app.route('/')
def home():
    # Renders the registration form on the homepage
    return render_template('register.html')

@app.route('/register', methods=['POST'])
def register():
    # Retrieves the form data
    username = request.form['username']
    email = request.form['email']
    password = request.form['password']
    
    # In a real-world application, you should hash the password and save user details to a database
    
    # Return a response confirming the registration (or ideally redirect to a confirmation page)
    return f"User {username} with email {email} successfully registered!!"

if __name__ == '__main__':
    app.run(debug=True)
