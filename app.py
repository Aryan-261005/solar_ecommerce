from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb.cursors
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# ------------------------------
# MySQL Configuration
# ------------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''  # Set your MySQL password
app.config['MYSQL_DB'] = 'solar_shop'

mysql = MySQL(app)

# ------------------------------
# Home / Visitor Routes
# ------------------------------
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')


# ------------------------------
# Admin Authentication
# ------------------------------
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT password FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        cursor.close()

        if admin and check_password_hash(admin[0], password):
            session['admin'] = username
            flash("Admin logged in successfully!", "success")
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid credentials", "danger")

    return render_template('admin/login.html')

@app.route('/admin/register', methods=['GET', 'POST'])
def admin_register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'])

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
        existing_admin = cursor.fetchone()
        if existing_admin:
            flash("Username already exists!", "danger")
            cursor.close()
            return redirect(url_for('admin_register'))

        cursor.execute("INSERT INTO admin (username,password) VALUES (%s,%s)", (username, password))
        mysql.connection.commit()
        cursor.close()
        flash("Admin registered successfully!", "success")
        return redirect(url_for('admin_login'))

    return render_template('admin/register.html')

@app.route('/admin/reset-password', methods=['GET', 'POST'])
def admin_reset_password():
    if request.method == 'POST':
        username = request.form['username']
        new_password = generate_password_hash(request.form['new_password'])

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM admin WHERE username=%s", (username,))
        admin = cursor.fetchone()
        if admin:
            cursor.execute("UPDATE admin SET password=%s WHERE username=%s", (new_password, username))
            mysql.connection.commit()
            flash("Password updated successfully!", "success")
        else:
            flash("Username not found!", "danger")
        cursor.close()
        return redirect(url_for('admin_login'))

    return render_template('admin/reset_password.html')

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    flash("Logged out successfully!", "success")
    return redirect(url_for('admin_login'))


# ------------------------------
# Admin Dashboard / Products
# ------------------------------
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'admin' not in session:
        flash("Please login as admin first!", "danger")
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    return render_template('admin/dashboard.html', products=products)

@app.route('/admin/add-product', methods=['POST'])
def add_product():
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    name = request.form['name']
    description = request.form['description']
    price = request.form['price']
    image_file = request.files['image']

    filename = None
    if image_file:
        filename = image_file.filename
        save_path = os.path.join('static/uploads', filename)
        image_file.save(save_path)

    cursor = mysql.connection.cursor()
    cursor.execute("INSERT INTO products (name, description, price, image) VALUES (%s,%s,%s,%s)",
                   (name, description, price, filename))
    mysql.connection.commit()
    cursor.close()
    flash("Product added successfully!", "success")
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/delete-product/<int:id>')
def delete_product(id):
    if 'admin' not in session:
        return redirect(url_for('admin_login'))

    cursor = mysql.connection.cursor()
    cursor.execute("DELETE FROM products WHERE id=%s", (id,))
    mysql.connection.commit()
    cursor.close()
    flash("Product deleted!", "success")
    return redirect(url_for('admin_dashboard'))


# ------------------------------
# User Authentication
# ------------------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Email already registered!", "danger")
            cursor.close()
            return redirect(url_for('register'))

        cursor.execute("INSERT INTO users (name,email,password) VALUES (%s,%s,%s)", (name,email,password))
        mysql.connection.commit()
        cursor.close()
        flash("Registration successful. Please login.", "success")
        return redirect(url_for('login'))

    return render_template('auth/register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password_input = request.form['password']

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute("SELECT id, first_name, last_name, email, password FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user:
            if check_password_hash(user['password'], password_input):
                session['user_id'] = user['id']
                session['user_name'] = f"{user['first_name']} {user['last_name']}"
                session['user_email'] = user['email']
                flash("Logged in successfully!", "success")
                return redirect(url_for('user_dashboard'))
            else:
                flash("Incorrect password!", "danger")
        else:
            flash("Email not found!", "danger")

    return render_template('login.html')

@app.route('/reset-password', methods=['GET', 'POST'])
def user_reset_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = generate_password_hash(request.form['new_password'])

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cursor.fetchone()
        if user:
            cursor.execute("UPDATE users SET password=%s WHERE email=%s", (new_password,email))
            mysql.connection.commit()
            flash("Password updated successfully!", "success")
        else:
            flash("Email not found!", "danger")
        cursor.close()
        return redirect(url_for('login'))

    return render_template('auth/reset_password.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("Logged out successfully!", "success")
    return redirect(url_for('home'))


# ------------------------------
# User Dashboard & Products
# ------------------------------
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute("SELECT * FROM products")
    products = cursor.fetchall()
    cursor.close()
    return render_template('user/dashboard.html', products=products, user_name=session.get('user_email'))


# ------------------------------
# Cart & Checkout
# ------------------------------
@app.route('/add-to-cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    quantity = int(request.form.get('quantity', 1))
    cart = session.get('cart', {})
    if str(product_id) in cart:
        cart[str(product_id)] += quantity
    else:
        cart[str(product_id)] = quantity
    session['cart'] = cart
    flash("Product added to cart!", "success")
    return redirect(url_for('user_dashboard'))

@app.route('/cart')
def cart():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    products_in_cart = []
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    for product_id, qty in cart.items():
        cursor.execute("SELECT * FROM products WHERE id=%s", (product_id,))
        product = cursor.fetchone()
        if product:
            product['quantity'] = qty
            products_in_cart.append(product)
    cursor.close()
    return render_template('cart.html', products=products_in_cart)

@app.route('/checkout', methods=['GET','POST'])
def checkout_page():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        name = request.form['name']
        address = request.form['address']
        phone = request.form['phone']
        payment_method = request.form['payment_method']
        user_id = session['user_id']

        cursor = mysql.connection.cursor()
        cursor.execute(
            "INSERT INTO orders (user_id,name,address,phone,payment_method) VALUES (%s,%s,%s,%s,%s)",
            (user_id,name,address,phone,payment_method)
        )
        mysql.connection.commit()
        cursor.close()

        session.pop('cart', None)
        flash("Order placed successfully!", "success")
        return redirect(url_for('user_dashboard'))

    return render_template('checkout_page.html')


# ------------------------------
# Feedback
# ------------------------------
@app.route('/feedback', methods=['GET','POST'])
def feedback():
    if 'user_id' not in session:
        flash("Please login first!", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        message = request.form['message']
        user_id = session['user_id']
        cursor = mysql.connection.cursor()
        cursor.execute("INSERT INTO feedback (user_id,message) VALUES (%s,%s)", (user_id,message))
        mysql.connection.commit()
        cursor.close()
        flash("Feedback submitted successfully!", "success")
        return redirect(url_for('feedback'))

    return render_template('feedback.html')


# ------------------------------
# Run Flask
# ------------------------------
if __name__ == '__main__':
    app.run(debug=True)
