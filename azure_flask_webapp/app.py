from flask import Flask, render_template, request,redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import text
from io import StringIO
import pandas as pd
from sklearn.linear_model import LinearRegression, LogisticRegression
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
    __tablename__ = "users"
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

def upload_csv_to_table(file_storage, table_name, columns):
    if file_storage and file_storage.filename != '':
        stream = StringIO(file_storage.stream.read().decode("UTF8"), newline=None)
        cur = db.session.connection().connection.cursor()
        copy_sql = f"""
            COPY {table_name} ({columns})
            FROM STDIN
            WITH CSV
        """
        cur.copy_expert(copy_sql, stream)
        db.session.commit()
        print(f"✅ {table_name} updated")

@app.route('/')
def home():
    # Renders the registration form on the homepage
    return render_template('home.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None  # Track error messages

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(username=username).first()

        if user and user.password == password:
            return render_template('search.html')
        else:
            error = "Invalid credentials. Please try again."

    return render_template('login.html', error=error)


@app.route('/logout')
def logout():
    return render_template('home.html')
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    else:
        username = request.form['username']
        firstname = request.form['firstname']
        lastname = request.form['lastname']
        email = request.form['email']
        password = request.form['password']


    # Create a new user instance
        new_user = User(
            username=username,
            first_name=firstname,
            last_name=lastname,
            email=email,
            password=password
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
        
    
@app.route('/search', methods=['GET', 'POST'])
def search_and_pull():
    data = None
    hshd_num = None
    if request.method == 'POST':
        hshd_num = request.form.get('hshd_num')
        query = """
            SELECT h.hshd_num, t.basket_num, t.purchase_date, t.product_num,
                   p.department, p.commodity, t.spend, t.units
            FROM households h
            JOIN transactions t ON h.hshd_num = t.hshd_num
            JOIN products p ON t.product_num = p.product_num
            WHERE h.hshd_num = :hshd_num
            ORDER BY h.hshd_num, t.basket_num, t.purchase_date, p.product_num, p.department, p.commodity
        """
        result = db.session.execute(text(query), {'hshd_num': hshd_num})
        data = result.fetchall()
    return render_template('search.html', data=data, hshd_num=hshd_num)
@app.route('/upload', methods=['GET', 'POST'])
def upload_page():
    uploaded_tables = []
    if request.method == 'POST':
        # --- Handle Households if uploaded ---
        households_file = request.files.get('households')
        if households_file and households_file.filename != '':
            upload_csv_to_table(
                households_file,
                "households",
                "hshd_num, loyalty_flag, age_range, marital_status, income_range, homeowner_desc, hh_comp_desc, household_size, kid_category"
            )
            uploaded_tables.append('Households')
        # --- Handle Products if uploaded ---
        products_file = request.files.get('products')
        if products_file and products_file.filename != '':
            upload_csv_to_table(
                products_file,
                "products",
                "product_num, department, commodity, brand_type, natural_organic_flag"
            )
            uploaded_tables.append('Households')
        # --- Handle Transactions if uploaded ---
        transactions_file = request.files.get('transactions')
        if transactions_file and transactions_file.filename != '':
            upload_csv_to_table(
                transactions_file,
                "transactions",
                "basket_num, hshd_num, purchase_date, product_num, spend, units, store_region, week_num, year"
            )
        
            uploaded_tables.append('Transactions')

        if uploaded_tables:
            flash(f"✅ Successfully uploaded: {', '.join(uploaded_tables)}")
        else:
            flash("⚠️ No files were uploaded!")

        return redirect(url_for('upload_page'))  # Refresh after upload

    return render_template('upload.html')
@app.route('/dashboard')
def dashboard():
    # Demographic Analysis
    demographic_query = """
        SELECT hh.household_size, hh.kid_category, AVG(t.spend) AS avg_spend
        FROM households hh
        JOIN transactions t ON hh.hshd_num = t.hshd_num
        GROUP BY hh.household_size, hh.kid_category
        ORDER BY avg_spend DESC
        LIMIT 5;
    """
    demographic_data = db.session.execute(text(demographic_query)).fetchall()

    # Engagement Over Time
    engagement_query = """
        SELECT year, SUM(spend) AS total_spend
        FROM transactions
        GROUP BY year
        ORDER BY year;
    """
    engagement_data = db.session.execute(text(engagement_query)).fetchall()

    # Brand Preferences
    brand_query = """
        SELECT p.brand_type, SUM(t.spend) AS total_spend
        FROM transactions t
        JOIN products p ON t.product_num = p.product_num
        GROUP BY p.brand_type
        ORDER BY total_spend DESC;
    """
    brand_data = db.session.execute(text(brand_query)).fetchall()

    # ✅ Now ADD: Seasonal Trends
    seasonal_query = """
        SELECT WEEK_NUM, YEAR, SPEND
        FROM transactions
        WHERE SPEND IS NOT NULL;
    """
    seasonal_result = db.session.execute(text(seasonal_query)).fetchall()

    import pandas as pd
    seasonal_df = pd.DataFrame(seasonal_result, columns=["WEEK_NUM", "YEAR", "SPEND"])

    # Group and sum SPEND
    seasonal_grouped = seasonal_df.groupby(['YEAR', 'WEEK_NUM'])['SPEND'].sum().reset_index()
    seasonal_grouped = seasonal_grouped.sort_values(by=['YEAR', 'WEEK_NUM'])

    # Prepare seasonal trends dictionary for frontend
    years = sorted(seasonal_grouped['YEAR'].unique())
    seasonal_data = {}

    for year in years:
        year_data = seasonal_grouped[seasonal_grouped['YEAR'] == year]
        seasonal_data[year] = {
            "weeks": list(year_data['WEEK_NUM']),
            "spends": list(year_data['SPEND'])
        }

    return render_template('dashboard.html',
                           demographic_data=demographic_data,
                           engagement_data=engagement_data,
                           brand_data=brand_data,
                           seasonal_data=seasonal_data)

@app.route('/basket-ml')
def basket_ml():
    # Step 1: Load transactions
    transactions_query = """
        SELECT basket_num, product_num
        FROM transactions
        LIMIT 5000;
    """
    transactions_result = db.session.execute(text(transactions_query)).fetchall()
    transactions = pd.DataFrame(transactions_result, columns=["basket_num", "product_num"])

    # Step 2: Load products
    products_query = """
        SELECT product_num, department, commodity
        FROM products;
    """
    products_result = db.session.execute(text(products_query)).fetchall()
    products = pd.DataFrame(products_result, columns=["product_num", "department", "commodity"])

    # Step 3: Create basket-product matrix
    basket = transactions.groupby(['basket_num', 'product_num']).size().unstack(fill_value=0)
    basket = basket.applymap(lambda x: 1 if x > 0 else 0)

    if basket.shape[1] < 2:
        return "Not enough product combinations for ML analysis."

    # Step 4: Prepare X and y
    X = basket.copy()
    y = basket.columns.tolist()  # list of all products

    # Step 5: Fake target for each basket
    import random
    y_target = random.choices(y, k=len(X))

    # Step 6: Train Linear Regression
    from sklearn.linear_model import LinearRegression
    model = LinearRegression()
    model.fit(X, y_target)

    # Step 7: Predict "next likely product number"
    predictions = model.predict(X)
    predicted_products = [int(round(p)) for p in predictions]

    # Step 8: Map predicted product_num ➔ product details
    recommended_products = products[products['product_num'].isin(predicted_products)]

    # Step 9: For each basket, also list current products
    basket_product_map = {}

    for basket_id in basket.index:
        current_products = transactions[transactions['basket_num'] == basket_id]['product_num'].tolist()
        product_names = products[products['product_num'].isin(current_products)][['department', 'commodity']]
        readable_names = product_names.apply(lambda row: f"{row['department']} - {row['commodity']}", axis=1)
        basket_product_map[basket_id] = ", ".join(readable_names.tolist())

    # Step 10: Final results
    results = pd.DataFrame({
        'Basket Num': basket.index,
        'Products Already in Basket': basket.index.map(basket_product_map),
        'Recommended Product Num': predicted_products
    })

    results = results.merge(products, left_on='Recommended Product Num', right_on='product_num', how='left')

    results = results[['Basket Num', 'Products Already in Basket', 'department', 'commodity']].head(10)

    return render_template('basket_ml.html', results=results)



# Churn Prediction Page
@app.route('/churn')
def churn():
    # Load data
    churn_query = """
        SELECT hshd_num, SUM(spend) AS total_spend, MAX(year) AS last_year
        FROM transactions
        GROUP BY hshd_num
        LIMIT 1000;  -- to keep it light
    """
    churn_result = db.session.execute(text(churn_query)).fetchall()
    churn_data = pd.DataFrame(churn_result, columns=["hshd_num", "total_spend", "last_year"])

    # Label churn: if last purchase year < 2020, assume churn
    churn_data['churn'] = churn_data['last_year'].apply(lambda x: 1 if x < 2020 else 0)

    # Prepare features
    X = churn_data[['total_spend', 'last_year']]
    y = churn_data['churn']

    # Train Logistic Regression model
    model = LogisticRegression()
    model.fit(X, y)

    # Predict churn probability
    churn_data['churn_probability'] = model.predict_proba(X)[:, 1]

    # Show top 10 customers at risk
    churn_data = churn_data.sort_values(by="churn_probability", ascending=False).head(10)

    return render_template('churn.html', churn_data=churn_data)


if __name__ == '__main__':
    app.run(debug=True)
