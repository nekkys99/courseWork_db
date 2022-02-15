import sqlite3
import os
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g
from FDataBase import FDataBase

DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'fasodjo1iojdasiou092310ajsdp/,m,jjpasdo443'

app = Flask(__name__)
# app.config['SECRET_KEY'] = 'fgfgsfgsf21fg214fgfg31sff33as1'
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))


def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    return conn


def create_db():
    db = connect_db()
    with app.open_resource('sq_db.sql', mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


def get_db():
    if not hasattr(g, 'link_db'):
        g.link_db = connect_db()
    return g.link_db


dbase = None


# Создание перехватчика запросов
@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


menu = [{"name": "О сайте", "url": "about"},
        {"name": "Рецептики", "url": "recipes"},
        {"name": "Регистрация", "url": "registrate"},
        {"name": "Повара", "url": "cook"},
        {"name": "Обратная связь", "url": "contact"}]


@app.route("/")
def index():
    print(url_for('index'))
    return render_template("index.html", title="Главная страница", menu=menu)


@app.route("/about")
def about():
    print(url_for('about'))
    return render_template("about.html", title="О сайте", menu=menu)


@app.route("/profile/<username>")
def profile(username):
    if 'userLogged' not in session or session['userLogged'] != username:
        abort(401)
    return f"Пользватель: {username}"


@app.route("/contact", methods=["POST", "GET"])
def contact():
    if request.method == 'POST':
        if len(request.form['username']) > 2:
            flash('Сообщение отправлено', category='success')
        else:
            flash('Ошибка отправки', category='error')

    return render_template('contact.html', title='Обратная связь', menu=menu)


@app.errorhandler(404)
def pageNotFound(error):
    return render_template('page404.html', title='Страница не найдена', menu=menu)


@app.route("/login", methods=["POST", "GET"])
def login():
    return render_template("login.html", menu=dbase.getMenu(),title="Авторизация")


@app.route("/register")
def register():
    return render_template("register.html",menu=dbase.getMenu(),title="Регистрация")


@app.route("/testdb")
def test_data():
    return render_template('testdb.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce())


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route("/add_post", methods=["POST", "GET"])
def addPost():
    if request.method == "POST":
        if len(request.form['name']) > 4 and len(request.form['post']) > 10:
            res = dbase.addPost(request.form['name'], request.form['post'], request.form['url'])
            if not res:
                flash('Ошибка добавления статьи', category='error')
            else:
                flash('Статья добавлена успешно', category='success')
        else:
            flash('Ошибка добавления статьи', category='error')

    return render_template('add_post.html', menu=dbase.getMenu(), title="Добавление статьи")


@app.route("/post/<alias>")
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


if __name__ == "__main__":
    app.run(debug=True)
