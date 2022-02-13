from flask import Flask, render_template, url_for, request, flash, session, redirect, abort
import sqlite3
import os


DATABASE='/tmp/flsite.db'
DEBUG=True
SECRET_KEY='fasodjo1iojdasiou092310ajsdp/,m,jjpasdo443'


app = Flask(__name__)
#app.config['SECRET_KEY'] = 'fgfgsfgsf21fg214fgfg31sff33as1'
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))


def connect_db():
    conn=sqlite3.connect(app.config['DATABASE'])
    conn.row_factory=sqlite3.Row
    return conn


def create_db():
    db=connect_db()
    with app.open.resouce('sq_db.sql',mode='r') as f:
        db.cursor().executescript(f.read())
    db.commit()
    db.close()


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
    if 'userLogged' in session:
        return redirect(url_for('profile', username=session['userLogged']))
    elif request.method == 'POST' and request.form['username'] == "malinov" and request.form['psw'] == '123':
        session['userLogged'] = request.form['username']
        return redirect(url_for('profile', username=session['userLogged']))
    return render_template("login.html", title="Авторизация",menu=menu)


if __name__ == "__main__":
    app.run(debug=True)
