import os
import config
import MySQLdb
from flask import Flask, render_template, url_for, Response

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('home.html', icon = config.APP_ICON, title = config.APP_NAME)

if __name__ == '__main__':
    app.run(debug=True)
