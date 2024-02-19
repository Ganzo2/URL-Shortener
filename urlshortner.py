import random
import string
from flask import Flask, render_template, redirect, request, g
import sqlite3
import re  

app = Flask(__name__)

DATABASE = 'urls.db'

URL_REGEX = re.compile(
    r'^(?:http|ftp)s?://'  # http:// or https://
    r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'  # domain...
    r'localhost|'  # localhost...
    r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
    r'(?::\d+)?'  # optional port
    r'(?:/?|[/?]\S+)$', re.IGNORECASE)

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db

def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS urls
                        (id INTEGER PRIMARY KEY, long_url TEXT, short_url TEXT)''')
        db.commit()

def generate_short_url(length=6):
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        long_url = request.form['long_url']
        if not is_valid_url(long_url):
            return "Invalid URL. Please enter a valid URL.", 400 
        short_url = generate_short_url()
        db = get_db()
        cursor = db.cursor()
        cursor.execute("INSERT INTO urls (long_url, short_url) VALUES (?, ?)", (long_url, short_url))
        db.commit()
        return f"{request.url_root}{short_url}"
    return render_template("index.html")

@app.route("/<short_url>")
def redirect_url(short_url):
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT long_url FROM urls WHERE short_url=?", (short_url,))
    row = cursor.fetchone()
    if row:
        long_url = row[0]
        return redirect(long_url)
    else:
        return "URL not found", 404
    
def is_valid_url(url):
    return re.match(URL_REGEX, url) is not None

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
