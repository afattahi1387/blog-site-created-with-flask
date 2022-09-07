import os
import config
import MySQLdb
from flask import Flask, flash, render_template, request, redirect, url_for, Response, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

app = Flask(__name__)

app.config.update(
    SECRET_KEY = config.SECRET_KEY
)

db_connection = MySQLdb.connect(host = config.DB_HOST, user = config.DB_USERNAME, passwd = config.DB_PASSWORD, db = config.DB_NAME)

cursor = db_connection.cursor()

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def create_tables_in_database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `users` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `email` VARCHAR(255) NOT NULL,
            `password` VARCHAR(255) NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `categories` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `category_name` VARCHAR(255) NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `articles` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `image` VARCHAR(255) NOT NULL,
            `category_id` VARCHAR(255) NOT NULL,
            `writer_id` INT(255) NOT NULL,
            `short_description` TEXT NOT NULL,
            `long_description` TEXT NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

def close_database():
    db_connection.commit()
    cursor.close()

def get_all_users():
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()

class User(UserMixin):
    
    def __init__(self, id):
        self.id = id
        cursor.execute(f"SELECT * FROM users WHERE id = '{self.id}'")
        user = cursor.fetchone()
        self.name = user[1]
        self.username = user[2]
        self.password = user[3]

    def __repr__(self):
        return "%d/%s/%s/%s" % (self.id, self.name, self.username, self.password)

users = [User(user[0]) for user in get_all_users()]

@login_manager.user_loader
def load_user(userID):
    return User(userID)

def get_all_categories(orderby):
    query = 'SELECT * FROM categories'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_all_articles(orderby):
    query = 'SELECT * FROM articles'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_single_article(articleID):
    cursor.execute(f"SELECT * FROM articles WHERE id = '{articleID}'")
    article = cursor.fetchone()
    if not article:
        return False
    
    return article

def get_single_writer(writerID):
    cursor.execute(f"SELECT * FROM users WHERE id = '{writerID}'")
    writer = cursor.fetchone()
    if not writer:
        return False

    return writer

def get_single_category(categoryID):
    cursor.execute(f"SELECT * FROM categories WHERE id = '{categoryID}'")
    category = cursor.fetchone()
    if not category:
        return False

    return category

def check_user_exists(email, password):
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
    if cursor.fetchone():
        return True
    
    return False

def get_single_user(email, password):
    if check_user_exists(email, password):
        cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        return cursor.fetchone()

    return False

create_tables_in_database()

@app.route('/')
def home():
    categories = get_all_categories(False)
    articles = get_all_articles(True)
    return render_template('home.html', icon = config.APP_ICON, title = config.APP_NAME, categories = categories, articles = articles)

@app.route('/single-article/<int:id>')
def single_article(id):
    categories = get_all_categories(False)
    article = get_single_article(id)
    category = get_single_category(article[3])
    writer = get_single_writer(article[4])
    return render_template('single_article.html', icon = config.APP_ICON, title = config.APP_NAME, categories = categories, article = article, category = category, writer = writer)

@app.route('/login', methods = ['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/') #Todo: change
    
    if request.method == 'POST':
        if not request.form['email']:
            flash('فیلد ایمیل الزامی است.')
            return redirect(url_for('login'))
        elif not request.form['password']:
            flash('فیلد رمز عبور الزامی است.')
            old_email = request.form['email']
            return redirect(url_for('login') + f'?email={old_email}')

        email = request.form['email']
        password = request.form['password']
        if check_user_exists(email, password):
            user = get_single_user(email, password)
            login_user(User(user[0]))
            return redirect('/') #Todo: change
        else:
            flash('اطلاعات وارد شده صحیح نمی باشند. لطفا مجددا تلاش فرمایید.')
            old_email = request.form['email']
            return redirect(url_for('login') + f'?email={old_email}')

    if request.args.get('email'):
        email = request.args.get('email');
    else:
        email = ''

    return render_template('login.html', title = config.APP_NAME, email = email)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')

@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title = config.APP_NAME)

if __name__ == '__main__':
    app.run(debug=True)
