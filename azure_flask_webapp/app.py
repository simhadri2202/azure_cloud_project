from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home - redirects to register/login
@app.route('/')
def home():
    return render_template('welcome.html')

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']
        # TODO: Save user to DB
        return f"User {username} with email {email} successfully registered!"
    return render_template('register.html')

# Dashboard
@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

# Upload resumes or job description
@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        uploaded_file = request.files['file']
        # TODO: Process and store uploaded file
        return f"File {uploaded_file.filename} uploaded successfully!"
    return render_template('upload_form.html')

# Resume/Job Matching results
@app.route('/match')
def match():
    # TODO: Fetch and compute match results
    return render_template('search_display.html')

# Analytics
@app.route('/analytics')
def analytics():
    # TODO: Embed or connect to Power BI reports or internal data viz
    return render_template('data_display.html')

# Analytics
@app.route('/login')
def login():
    # TODO: welcome
    return render_template('login.html')

if __name__ == '__main__':
    app.run(debug=True)
