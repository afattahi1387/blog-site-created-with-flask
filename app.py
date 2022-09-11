import os
import config
import MySQLdb
import shutil
from werkzeug.utils import secure_filename
from flask import Flask, flash, render_template, request, redirect, url_for, Response, session
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user, current_user

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

app.config.update(
    SECRET_KEY = config.SECRET_KEY
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def connect_to_database():
    return MySQLdb.connect(host = config.DB_HOST, user = config.DB_USERNAME, passwd = config.DB_PASSWORD, db = config.DB_NAME)

def create_tables_in_database():
    db_connection = connect_to_database()

    cursor = db_connection.cursor()

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

    db_connection.commit()
    cursor.close()

def get_all_users():
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()

class User(UserMixin):

    def __init__(self, id):
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
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

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def get_all_categories(orderby):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = 'SELECT * FROM categories'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_all_articles(orderby):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = 'SELECT * FROM articles'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_single_article(articleID):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM articles WHERE id = '{articleID}'")
    article = cursor.fetchone()
    if not article:
        return False

    return article

def get_single_writer(writerID):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = '{writerID}'")
    writer = cursor.fetchone()
    if not writer:
        return False

    return writer

def get_single_category(categoryID):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM categories WHERE id = '{categoryID}'")
    category = cursor.fetchone()
    if not category:
        return False

    return category

def check_user_exists(email, password):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
    if cursor.fetchone():
        return True

    return False

def get_single_user(email, password):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    if check_user_exists(email, password):
        cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        return cursor.fetchone()

    return False

def articles_exists_for_category(categoryID):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM articles WHERE category_id = '{categoryID}'")
    articles = cursor.fetchall()
    if articles:
        return True

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
        return redirect(url_for('dashboard'))

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
            return redirect(url_for('dashboard'))
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

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    if request.method == 'POST':
        if not request.form['form_name']:
            flash('danger-----اطلاعات وارد شده صحیح نمی باشد.')
            return redirect(url_for('dashboard'))

        if request.form['form_name'] == 'add_category':
            category_name = request.form['category_name']
            cursor.execute(f"""
                INSERT INTO categories (id, category_name) VALUES (NULL, '{category_name}')
            """)
            flash('success-----دسته بندی شما با موفقیت اضافه شد.')
            db_connection.commit()
            cursor.close()
            return redirect(url_for('dashboard'))
        elif request.form['form_name'] == 'edit_category':
            category_id = request.args.get('edit-category')
            category_name = request.form['category_name']
            cursor.execute(f"""
                UPDATE categories SET category_name = '{category_name}' WHERE id = '{category_id}'
            """)
            flash('success-----دسته بندی انتخاب شده با موفقیت ویرایش شد.')
            db_connection.commit()
            cursor.close()
            return redirect(url_for('dashboard'))
        else:
            flash('اطلاعات وارد شده صحیح نمی باشد.')
            return redirect(url_for('dashboard'))

    all_categories = get_all_categories(True)
    categories = {}
    for i in range(0, len(all_categories)):
        category = list(all_categories[i])
        category_id = category[0]
        if not articles_exists_for_category(category_id):
            category.append(True)
        else:
            category.append(False)
        categories[i + 1] = category

    if request.args.get('edit-category'):
        show_form = 'edit_category'
        category = get_single_category(request.args.get('edit-category'))
        category_name = category[1]
    else:
        show_form = 'add_category'
        category_name = ''

    return render_template('dashboard.html', title = config.APP_NAME, categories = categories, show_form = show_form, category_name = category_name)

@app.route('/delete-category/<int:id>')
@login_required
def delete_category(id):
    if articles_exists_for_category(id):
        flash('danger-----این دسته بندی دارای مقاله است و نمی توانید آن را حذف کنید.')
        return redirect(url_for('dashboard'))

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"DELETE FROM categories WHERE id = '{id}'")
    flash('success-----دسته بندی شما با موفقیت حذف شد.')
    db_connection.commit()
    cursor.close()
    return redirect(url_for('dashboard'))

@app.route('/articles')
@login_required
def articles():
    all_articles = get_all_articles(True)
    articles = {}
    for i in range(0, len(all_articles)):
        articles[i + 1] = all_articles[i]
    return render_template('articles.html', title = config.APP_NAME, articles = articles)

@app.route('/delete-article/<int:id>')
@login_required
def delete_article(id):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    article_image = get_single_article(id)[2]
    image_path = os.path.join(config.CURRENT_WORKING_DIRECTORY + '/static/articles_images/', article_image)
    os.remove(image_path)
    cursor.execute(f"DELETE FROM articles WHERE id = '{id}'")
    flash('success-----مقاله شما با موفقیت حذف شد.')
    db_connection.commit()
    cursor.close()
    return redirect(url_for('articles'))

@app.route('/add-article', methods = ['GET', 'POST'])
@login_required
def add_article():
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    error = False
    if request.method == 'POST':
        if not request.form['name']:
            flash('name-----فیلد نام نمی تواند خالی باشد.')
            error = True
            session['add_article_name_error'] = True

        if request.form['category_id'] == 'empty':
            flash('category_id-----لطفا دسته بندی مورد نظر خود را انتخاب کنید.')
            error = True
            session['add_article_category_error'] = True

        if not request.form['short_description']:
            flash('short_description-----فیلد مقدمه نمی تواند خالی باشد.')
            error = True

        if not request.form['long_description']:
            flash('long_description-----فیلد بدنه نمی تواند خالی باشد.')
            error = True

        if error:
            if request.form['name'] and 'add_article_name_error' in session:
                session.pop('add_article_name_error', None)

            if request.form['category_id'] != 'empty' and 'add_article_category_error' in session:
                session.pop('add_article_category_error', None)

            session['add_article_name_value'] = request.form['name']
            if(request.form['category_id'] != 'empty'):
                session['add_article_category_value'] = int(request.form['category_id'])

            session['add_article_short_description_value'] = request.form['short_description']
            session['add_article_long_description_value'] = request.form['long_description']
            return redirect('/add-article')

        name = request.form['name']
        category_id = request.form['category_id']
        writer_id = current_user.get_id()
        short_description = request.form['short_description']
        long_description = request.form['long_description']
        cursor.execute(f"""
            INSERT INTO articles (id, name, image, category_id, writer_id, short_description, long_description)
            VALUES (NULL, '{name}', '', '{category_id}', '{writer_id}', '{short_description}', '{long_description}')
        """)

        last_insert_id = cursor.lastrowid
        db_connection.commit()
        cursor.close()
        session.pop('add_article_name_value', None)
        session.pop('add_article_category_value', None)
        session.pop('add_article_short_description_value', None)
        session.pop('add_article_long_description_value', None)
        session.pop('add_article_name_error', None)
        session.pop('add_article_category_error', None)
        return redirect(f'/upload-new-article-image/{last_insert_id}')

    categories = get_all_categories(True)
    return render_template('add_article.html', title = config.APP_NAME, categories = categories)

@app.route('/upload-new-article-image/<int:id>', methods = ['GET', 'POST'])
@login_required
def upload_new_article_image(id):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    if request.method == 'POST':
        if 'image' not in request.files:
            flash('فایل به درستی آپلود نشده است.')
            return redirect(f'/upload-new-article-image/{id}')

        image = request.files['image']
        if not image:
            flash('فایلی آپلود نشده است.')
            return redirect(f'/upload-new-article-image/{id}')

        if not allowed_file(image.filename):
            flash('پسوند فایل شما اجازه آپلود ندارد.')
            return redirect(f'/upload-new-article-image/{id}')

        image_name = secure_filename(image.filename)
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
        image.save(image_path)
        image_new_name = str(id) + '_' + image_name
        os.rename('static/uploads/' + image_name, 'static/uploads/' + image_new_name)
        shutil.copyfile(f'static/uploads/{image_new_name}', f'static/articles_images/{image_new_name}')
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_new_name)
        os.remove(image_path)
        cursor.execute(f"""
            UPDATE articles SET image = '{image_new_name}' WHERE id = '{id}'
        """)

        db_connection.commit()
        cursor.close()
        return redirect(f'/single-article/{id}')

    article = get_single_article(id)
    return render_template('upload_new_article_image.html', title = config.APP_NAME, article = article)

@app.route('/edit-article/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit_article(id):
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    error = False
    if request.method == 'POST':
        if not request.form['name']:
            flash('name-----فیلد نام نمی تواند خالی باشد.')
            error = True
            session['edit_article_name_error'] = True

        if not request.form['short_description']:
            flash('short_description-----فیلد مقدمه نمی تواند خالی باشد.')
            error = True

        if not request.form['long_description']:
            flash('long_description-----فیلد بدنه نمی تواند خالی باشد.')
            error = True

        if error:
            if request.form['name'] and 'edit_article_name_error' in session:
                session.pop('edit_article_name_error', None)

            if request.form['short_description'] != '':
                session['edit_article_name_value'] = request.form['name']

            if request.form['long_description'] != '':
                session['edit_article_name_value'] = request.form['name']

            session['edit_article_short_description_value'] = request.form['short_description']
            session['edit_article_long_description_value'] = request.form['long_description']
            return redirect(f'/edit-article/{id}')

        name = request.form['name']
        category_id = request.form['category_id']
        short_description = request.form['short_description']
        long_description = request.form['long_description']
        article = get_single_article(id)
        if not request.files['image']:
            image_new_name = article[2]
        else:
            image = request.files['image']
            if not allowed_file(image.filename):
                flash('image-----پسوند فایل شما اجازه آپلود ندارد.')
                return redirect(f'/edit-article/{id}')

            os.remove(os.path.join(config.CURRENT_WORKING_DIRECTORY + '/static/articles_images/' + article[2]))
            image_name = secure_filename(image.filename)
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_name)
            image.save(image_path)
            image_new_name = str(id) + '_' + image_name
            os.rename(f'static/uploads/{image_name}', f'static/uploads/{image_new_name}')
            shutil.copyfile(f'static/uploads/{image_new_name}', f'static/articles_images/{image_new_name}')
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], image_new_name))

        cursor.execute(f"""
            UPDATE articles SET name = '{name}',
            category_id = '{category_id}',
            short_description = '{short_description}',
            long_description = '{long_description}',
            image = '{image_new_name}' WHERE id = '{id}'
        """)

        db_connection.commit()
        cursor.close()
        session.pop('edit_article_name_value', None)
        session.pop('edit_article_short_description_value', None)
        session.pop('edit_article_long_description_value', None)
        session.pop('edit_article_name_error', None)
        return redirect(f'/single-article/{id}')

    categories = get_all_categories(True)
    article = get_single_article(id)
    return render_template('edit_article.html', title = config.APP_NAME, categories = categories, article = article)

if __name__ == '__main__':
    app.run(debug=True)
