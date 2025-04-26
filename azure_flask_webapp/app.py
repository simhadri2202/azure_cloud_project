from flask import Flask, render_template, request,redirect, url_for,flash
from flask_sqlalchemy import SQLAlchemy
import os
from dotenv import load_dotenv
from sqlalchemy import text
from io import StringIO
import pandas as pd
from mlxtend.preprocessing import TransactionEncoder
from mlxtend.frequent_patterns import apriori, association_rules
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
    if request.method == 'POST':
        # Get the credentials from the form
        username = request.form['username']
        password = request.form['password']

        # Query the database for the user
        user = User.query.filter_by(username=username).first()

        if user and user.password == password:  # Compare passwords (ensure hashing in production)
            return render_template('search.html')
        else:
            return "Invalid credentials, please try again."
    return render_template('login.html')

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

    return render_template('dashboard.html',
                           demographic_data=demographic_data,
                           engagement_data=engagement_data,
                           brand_data=brand_data)
@app.route('/basket-analysis')
def basket_analysis():
    import pandas as pd
    from collections import Counter
    from itertools import combinations
    from sqlalchemy import text

    # Step 1: Pull basket and product data
    basket_query = """
        SELECT basket_num, product_num
        FROM transactions
        ORDER BY basket_num;
    """
    data = db.session.execute(text(basket_query)).fetchall()

    df = pd.DataFrame(data, columns=["basket_num", "product_num"])

    # Step 2: Pull product information (PRODUCT_NUM, COMMODITY)
    product_query = """
        SELECT product_num, commodity
        FROM products;
    """
    products_data = db.session.execute(text(product_query)).fetchall()

    df_products = pd.DataFrame(products_data, columns=["product_num", "commodity"])

    # Step 3: Group products per basket
    basket_groups = df.groupby('basket_num')['product_num'].apply(list)

    # Step 4: Count co-occurring product pairs
    pair_counter = Counter()
    for products in basket_groups:
        if len(products) > 1:
            for pair in combinations(sorted(products), 2):
                pair_counter[pair] += 1

    # Step 5: Convert Counter to DataFrame
    pair_df = pd.DataFrame(pair_counter.items(), columns=['product_pair', 'count'])

    # Step 6: Map product_num to commodity (names)
    def get_commodity(product_num):
        row = df_products[df_products['product_num'] == product_num]
        if not row.empty:
            return row.iloc[0]['commodity']
        else:
            return str(product_num)  # fallback to number if not found

    # Step 7: Apply mapping to product pairs
    pair_df['product_1_name'] = pair_df['product_pair'].apply(lambda x: get_commodity(x[0]))
    pair_df['product_2_name'] = pair_df['product_pair'].apply(lambda x: get_commodity(x[1]))

    # Step 8: Take Top 10 most frequent
    top_pairs = pair_df.sort_values(by='count', ascending=False).head(10)

    return render_template('basket_analysis.html', pairs=top_pairs)


if __name__ == '__main__':
    app.run(debug=True)
