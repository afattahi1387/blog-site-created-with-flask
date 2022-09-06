import os
import config
import MySQLdb
from flask import Flask, render_template, url_for, Response

app = Flask(__name__)

db_connection = MySQLdb.connect(host = config.DB_HOST, user = config.DB_USERNAME, passwd = config.DB_PASSWORD, db = config.DB_NAME)

cursor = db_connection.cursor()

def create_tables_in_database():
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS `articles` (
            `id` INT(255) NOT NULL PRIMARY KEY AUTO_INCREMENT,
            `name` VARCHAR(255) NOT NULL,
            `short_description` TEXT NOT NULL,
            `long_description` TEXT NOT NULL
        ) ENGINE InnoDB DEFAULT CHARSET=utf8 COLLATE=utf8_persian_ci;
    ''')

create_tables_in_database()

@app.route('/')
def home():
    return render_template('home.html', icon = config.APP_ICON, title = config.APP_NAME)

if __name__ == '__main__':
    db_connection.commit()
    db_connection.close()
    app.run(debug=True)
