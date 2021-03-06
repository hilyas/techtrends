import sqlite3
import sys
from logging.config import dictConfig

from flask import Flask, jsonify, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort

TOTAL_DB_CONNECTIONS = 0

# Configuring logging
dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s] %(levelname)s: %(message)s',
        }
    },
    'handlers': {
        'stdout': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stdout',
            'formatter': 'default'
        },
        'stderr': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://sys.stderr',
            'formatter': 'default'
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': ['stdout', 'stderr']
    }
})

# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'

# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    try:
        connection = sqlite3.connect('database.db')
        connection.row_factory = sqlite3.Row
        global TOTAL_DB_CONNECTIONS
        TOTAL_DB_CONNECTIONS += 1
    except sqlite3.Error as e:
        app.logger(f"Error {e.args[0]}")
        sys.exit(1)
    finally:
        if connection:
            return connection

# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post

def get_total_posts():
    connection = get_db_connection()
    total_posts = len(connection.execute('SELECT * FROM posts').fetchall())
    connection.close()
    return total_posts

@app.route("/healthz")
def status():
    resp_data = {"result":"OK - healthy"}
    app.logger.info("/healthz page retrieved!")
    return jsonify(resp_data), 200

@app.route("/metrics")
def metrics():
    resp_data = {"status":"success",
                "code":0,
                "data":{"db_connection_count":TOTAL_DB_CONNECTIONS,"post_count":get_total_posts()}}
    app.logger.info("/metrics page retrieved!")
    return jsonify(resp_data), 200

# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)

# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
      app.logger.error("A non-existing article was accessed! 404 error!")
      return render_template('404.html'), 404
    else:
      app.logger.info(f"Article '{post['title']}' retrieved!")
      return render_template('post.html', post=post)

# Define the About Us page
@app.route('/about')
def about():
    app.logger.info("/about page retrieved!")
    return render_template('about.html')

# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info(f"Article '{title}' created!")
            return redirect(url_for('index'))
    return render_template('create.html')

# start the application on port 3111
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='3111')
