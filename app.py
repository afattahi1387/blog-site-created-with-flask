import os
import config
import MySQLdb
from flask import Flask, render_template, url_for, Response

app = Flask(__name__)

db_connection = MySQLdb.connect(host = config.DB_HOST, user = config.DB_USERNAME, passwd = config.DB_PASSWORD, db = config.DB_NAME)

cursor = db_connection.cursor()

def create_tables_in_database():
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
            `short_description` TEXT NOT NULL,
            `long_description` TEXT NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

def close_database():
    db_connection.commit()
    cursor.close()

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

create_tables_in_database()

@app.route('/')
def home():
    categories = get_all_categories(False)
    articles = get_all_articles(True)
    return render_template('home.html', icon = config.APP_ICON, title = config.APP_NAME, categories = categories, articles = articles)

if __name__ == '__main__':
    app.run(debug=True)
