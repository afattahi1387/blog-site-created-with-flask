"""This file for blog site created with flask."""
import os
import shutil
import MySQLdb
from flask import Flask, flash, render_template, \
                                 request, redirect, url_for, session, abort
from flask_login import LoginManager, UserMixin, \
                                 login_required, login_user, logout_user, current_user
from werkzeug.utils import secure_filename
import config

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = config.UPLOAD_FOLDER

app.config.update(
    SECRET_KEY = config.SECRET_KEY
)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

def connect_to_database():
    """
        This function is for connect to database.
    """

    return MySQLdb.connect(host = config.DB_HOST,
                           user = config.DB_USERNAME,
                           passwd = config.DB_PASSWORD,
                           db = config.DB_NAME)

def create_tables_in_database():
    """
        This function is for create tables in database.
    """

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

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `comments` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `user_name` VARCHAR(255) NOT NULL,
            `article_id` INT(255) NOT NULL,
            `comment` TEXT NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `votes` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `article_id` INT(255) NOT NULL,
            `vote` VARCHAR(255) NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

    db_connection.commit()
    cursor.close()

create_tables_in_database()

def get_all_users():
    """
        This function returns all users.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute('SELECT * FROM users')
    return cursor.fetchall()

class User(UserMixin):
    """
        This class is required for login page.
    """

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
def load_user(user_id):
    """
        This function is required for login page and returns an user with an id.
    """

    return User(user_id)

def allowed_file(filename):
    """
        This function is for check allowed file extension.
    """

    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in config.ALLOWED_EXTENSIONS

def get_all_categories(orderby):
    """
        This function returns all categories.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = 'SELECT * FROM categories'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_all_articles(orderby):
    """
        This function returns all articles.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = 'SELECT * FROM articles'
    if orderby:
        query += ' ORDER BY id DESC'
    cursor.execute(query)
    return cursor.fetchall()

def get_article_comments(article_id):
    """
        This function receives an article id,
        Then find and returns article comments.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"""
        SELECT * FROM comments WHERE article_id = '{article_id}'
    """)
    comments = cursor.fetchall()
    if not comments:
        return False
    return comments

def count_article_votes(article_id, vote):
    """
        This function receives an article id and vote,
        Then counts votes and returns number of votes.
    """
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    votes_counter = 0
    cursor.execute(f'''
        SELECT * FROM votes WHERE article_id = '{article_id}'
        AND vote = '{vote}'
    ''')
    votes = cursor.fetchall()
    if not votes:
        return 0
    for vote in votes:
        votes_counter += 1
    return votes_counter

def get_category_articles(category_id, orderby):
    """
        This function receives a category id and returns this category articles.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = f"SELECT * FROM articles WHERE category_id = '{category_id}'"
    if orderby:
        query += "ORDER BY id DESC"
    articles = cursor.fetchall()
    if not articles:
        return False

    return articles

def get_single_article(article_id):
    """
        This function receives an article id and returns article.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM articles WHERE id = '{article_id}'")
    article = cursor.fetchone()
    if not article:
        return False

    return article

def get_single_writer(writer_id):
    """
        This function receives an writer (user) id and returns writer (user).
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE id = '{writer_id}'")
    writer = cursor.fetchone()
    if not writer:
        return False

    return writer

def get_single_category(category_id):
    """
        This function receives a category id and returns category.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM categories WHERE id = '{category_id}'")
    category = cursor.fetchone()
    if not category:
        return False

    return category

def check_user_exists(email, password):
    """
        This function receives an email and a password,
        Then check user exists.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
    if cursor.fetchone():
        return True

    return False

def get_single_user(email, password):
    """
        This function receives an email and a password and returns an user.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    if check_user_exists(email, password):
        cursor.execute(f"SELECT * FROM users WHERE email = '{email}' AND password = '{password}'")
        return cursor.fetchone()

    return False

def articles_exists_for_category(category_id):
    """
        This function check for any article exists for a category.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT * FROM articles WHERE category_id = '{category_id}'")
    articles = cursor.fetchall()
    if articles:
        return True

    return False

def get_user_articles(user_id, orderby):
    """
        This function receives an user id and returns user articles.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    query = f"SELECT * FROM articles WHERE writer_id = '{user_id}'"
    if orderby:
        query += " ORDER BY id DESC"
    cursor.execute(query)
    articles = cursor.fetchall()
    if not articles:
        return False
    return articles

def search_in_articles(searched_word):
    """
        This function is for search articles page.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"""
        SELECT * FROM articles WHERE
        name LIKE '%{searched_word}%' OR
        short_description LIKE '%{searched_word}%' OR
        long_description LIKE '%{searched_word}%'
        ORDER BY id DESC
    """)

    articles = cursor.fetchall()
    if not articles:
        return False
    return articles

@app.route('/')
def home():
    """
        This function is for home page.
    """

    categories = get_all_categories(False)
    articles = get_all_articles(True)
    return render_template('home.html',
                           icon = config.APP_ICON,
                           title = config.APP_NAME,
                           categories = categories,
                           articles = articles)

@app.route('/category/<int:category_id>')
def category(category_id):
    """
        This function is for single category page.
        First receives a category id, Then
        Returns this category articles.
    """

    if not get_single_category(category_id):
        page_title = 'مقاله ای یافت نشد!'
    else:
        page_title = 'نمایش مقالات برای دسته بندی: ' + get_single_category(category_id)[1]
    articles = get_category_articles(category_id, True)
    categories = get_all_categories(False)
    return render_template('single_category.html',
                           icon = config.APP_ICON,
                           title = config.APP_NAME,
                           categories = categories,
                           page_title = page_title,
                           articles = articles)

@app.route('/search')
def search():
    """
        This function is for search page.
        First receives searched word,
        Then returns search results.
    """

    if request.args.get('searched_word'):
        searched_word = request.args.get('searched_word')
    else:
        searched_word = ''
    categories = get_all_categories(False)
    articles = search_in_articles(searched_word)
    return render_template('search.html',
                           icon = config.APP_ICON,
                           title = config.APP_NAME,
                           searched_word = searched_word,
                           categories = categories,
                           articles = articles)

@app.route('/single-article/<int:id>')
def single_article(id):
    """
        This function receives an article id and show this article
        in single article page.
    """

    categories = get_all_categories(False)
    article = get_single_article(id)
    category = get_single_category(article[3])
    writer = get_single_writer(article[4])
    comments = get_article_comments(id)
    great_votes = count_article_votes(id, 'great')
    not_bad_votes = count_article_votes(id, 'not_bad')
    bad_votes = count_article_votes(id, 'bad')
    return render_template('single_article.html',
                           icon = config.APP_ICON,
                           title = config.APP_NAME,
                           categories = categories,
                           article = article,
                           category = category,
                           writer = writer,
                           comments = comments,
                           great_votes = great_votes,
                           not_bad_votes = not_bad_votes,
                           bad_votes = bad_votes)

@app.route('/add-comment/<int:article_id>', methods = ['GET', 'POST'])
def add_comment(article_id):
    """
        This function is for add comment for an article.
    """
    error = False
    if request.method != 'POST':
        abort(404)

    if not request.form['user_name']:
        flash('user_name-----فیلد نام الزامی می باشد.')
        session['add_comment_user_name_error'] = True
        error = True

    if not request.form['comment']:
        flash('comment-----فیلد کامنت الزامی می باشد.')
        error = True

    if error:
        if request.form['user_name']:
            session['add_comment_user_name_value'] = request.form['user_name']
            session.pop('add_comment_user_name_error', None)

        if request.form['comment']:
            session['add_comment_comment_value'] = request.form['comment']

        return redirect(f'/single-article/{article_id}#send_c')

    user_name = request.form['user_name']
    comment = request.form['comment']
    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"""
        INSERT INTO comments (id, user_name, article_id, comment)
        VALUES (NULL, '{user_name}', '{article_id}', '{comment}')
    """)
    db_connection.commit()
    cursor.close()
    session.pop('add_comment_user_name_value', None)
    session.pop('add_comment_comment_value', None)
    session.pop('add_comment_user_name_error', None)
    return redirect(f'/single-article/{article_id}#comments')

@app.route('/add-vote/<int:article_id>/<string:vote>')
def add_vote(article_id, vote):
    """
        This function receives an article id and a vote,
        Then save vote in votes table.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    cursor.execute(f"""
        INSERT INTO votes (id, article_id, vote)
        VALUES (NULL, '{article_id}', '{vote}')
    """)
    db_connection.commit()
    cursor.close()
    return redirect(f'/single-article/{article_id}#add_vote')

@app.route('/login', methods = ['GET', 'POST'])
def login():
    """
        This function is for login page.
    """

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
        email = request.args.get('email')
    else:
        email = ''

    return render_template('login.html', title = config.APP_NAME, email = email)

@app.route('/register', methods = ['GET', 'POST'])
def register():
    """
        This function is for register page.
    """

    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        error = False
        errors = []
        fields = ['name', 'email', 'password', 'confirm_password']
        if not request.form['name']:
            flash('فیلد نام و نام خانوادگی الزامی می باشد.')
            error = True
            errors.append('name')

        if not request.form['email']:
            flash('فیلد ایمیل الزامی می باشد.')
            error = True
            errors.append('email')

        if not request.form['password']:
            flash('فیلد رمز عبور الزامی می باشد.')
            error = True
            errors.append('password')

        if not request.form['confirm_password']:
            flash('فیلد تکرار رمز عبور الزامی می باشد.')
            error = True
            errors.append('confirm_password')

        if request.form['password'] != request.form['confirm_password']:
            flash('رمز عبور به درستی تکرار نشده است. لطفاً تکرار رمز عبور را مجدداً وارد نمایید.')
            error = True
            if 'password' not in errors:
                errors.append('password')

            if 'confirm_password' not in errors:
                errors.append('confirm_password')

        if request.form['name'] and request.form['email'] and \
            request.form['password'] and request.form['confirm_password'] and \
                request.form['password'] == request.form['confirm_password'] and \
                    check_user_exists(request.form['email'], request.form['password']):
                    flash('کاربری با این مشخصات وجود دارد. لطفاً اطلاعات خود را تغییر دهید.')
                    error = True

        if error:
            session['register_name_value'] = request.form['name']
            session['register_email_value'] = request.form['email']
            for e in errors:
                session['register_' + e + '_error'] = True

            for field in fields:
                if request.form[field]:
                    session.pop('register_' + field + '_error', None)
            
            return redirect(url_for('register'))

        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        db_connection = connect_to_database()
        cursor = db_connection.cursor()
        cursor.execute(f"""
            INSERT INTO users (id, name, email, password)
            VALUES (NULL, '{name}', '{email}', '{password}')
        """)
        new_user_id = cursor.lastrowid
        db_connection.commit()
        cursor.close()
        user = User(new_user_id)
        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('register.html',
                           title = config.APP_NAME)

@app.route('/logout')
@login_required
def logout():
    """
        This function is for user logout.
    """

    logout_user()
    return redirect('/')

@app.route('/dashboard', methods = ['GET', 'POST'])
@login_required
def dashboard():
    """
        This function is for dashboard page.
    """

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

    return render_template('dashboard.html',
                           title = config.APP_NAME,
                           categories = categories,
                           show_form = show_form,
                           category_name = category_name)

@app.route('/delete-category/<int:id>')
@login_required
def delete_category(id):
    """
        This function receives a category id and delete this category.
    """

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
    """
        This function is for articles page in admins dashboard.
    """

    if get_user_articles(current_user.get_id(), True):
        all_articles = get_user_articles(current_user.get_id(), True)
        articles = {}
        for i in range(0, len(all_articles)):
            articles[i + 1] = all_articles[i]
    else:
        articles = {}
    return render_template('articles.html', title = config.APP_NAME, articles = articles)

@app.route('/delete-article/<int:id>')
@login_required
def delete_article(id):
    """
        This function receives an article id and delete this article.
    """

    db_connection = connect_to_database()
    cursor = db_connection.cursor()
    article_image = get_single_article(id)[2]
    image_path = os.path.join(
                    config.CURRENT_WORKING_DIRECTORY + '/static/articles_images/',
                    article_image)
    os.remove(image_path)
    cursor.execute(f"DELETE FROM articles WHERE id = '{id}'")
    flash('success-----مقاله شما با موفقیت حذف شد.')
    db_connection.commit()
    cursor.close()
    return redirect(url_for('articles'))

@app.route('/add-article', methods = ['GET', 'POST'])
@login_required
def add_article():
    """
        This function is for add article page.
    """

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
            if request.form['category_id'] != 'empty':
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
    """
        This function is for upload new article image.
    """

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
        shutil.copyfile(f'static/uploads/{image_new_name}',
                        f'static/articles_images/{image_new_name}')
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image_new_name)
        os.remove(image_path)
        cursor.execute(f"""
            UPDATE articles SET image = '{image_new_name}' WHERE id = '{id}'
        """)

        db_connection.commit()
        cursor.close()
        return redirect(f'/single-article/{id}')

    article = get_single_article(id)
    return render_template('upload_new_article_image.html',
                           title = config.APP_NAME,
                           article = article)

@app.route('/edit-article/<int:id>', methods = ['GET', 'POST'])
@login_required
def edit_article(id):
    """
        This function is for edit article page.
    """

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
            shutil.copyfile(f'static/uploads/{image_new_name}',
                            f'static/articles_images/{image_new_name}')
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
    return render_template('edit_article.html',
                           title = config.APP_NAME,
                           categories = categories,
                           article = article)

if __name__ == '__main__':
    app.run(debug=True)
