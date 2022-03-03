import sqlite3
import os
from flask import Flask, render_template, url_for, request, flash, session, redirect, abort, g ,make_response
from FDataBase import FDataBase
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager,login_user,login_required,logout_user,current_user
from UserLogin import UserLogin
from forms import LoginForm,RegisterForm
from admin.admin import admin
# конфига датабэйз
DATABASE = '/tmp/flsite.db'
DEBUG = True
SECRET_KEY = 'fasodjo1iojdasiou092310ajsdp/,m,jjpasdo443'
MAX_CONTENT_LENGTH = 1024 * 1024


app = Flask(__name__)
# app.config['SECRET_KEY'] = 'fgfgsfgsf21fg214fgfg31sff33as1'
app.config.from_object(__name__)
app.config.update(dict(DATABASE=os.path.join(app.root_path, 'flsite.db')))

app.register_blueprint(admin, url_prefix='/admin')

login_manager = LoginManager(app)
login_manager.login_view ='login'
login_manager.login_message ='Для доступа к информации необходимо авторизоватся'
login_manager.login_message_category = "success"

@login_manager.user_loader
def load_user(user_id):
    print("load_user")
    return UserLogin().fromDB(user_id, dbase)


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
@app.route("/testdb")
def testdb():
    return render_template('testdb.html', menu=dbase.getMenu(), posts=dbase.getPostsAnonce())


@app.route("/about")
def about():
    print(url_for('about'))
    return render_template("about.html", title="О сайте", menu=menu)


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
    if current_user.is_authenticated:
        return redirect(url_for('profile'))

    form = LoginForm()
    if form.validate_on_submit():
        user = dbase.getUserByEmail(form.email.data)
        if user and check_password_hash(user['psw'], form.psw.data):
            userlogin = UserLogin().create(user)
            rm = form.remember.data
            login_user(userlogin, remember=rm)
            return redirect(request.args.get("next") or url_for("profile"))

        flash("Неверная пара логин/пароль", "error")

    return render_template("login.html", menu=dbase.getMenu(), title="Авторизация", form=form)

    # if request.method == "POST":
    #     user = dbase.getUserByEmail(request.form['email'])
    #     if user and check_password_hash(user['psw'], request.form['psw']):
    #         userlogin = UserLogin().create(user)
    #         rm = True if request.form.get('remainme') else False
    #         login_user(userlogin, remember=rm)
    #         return redirect(request.args.get("next") or url_for("profile"))
    #
    #     flash("Неверная пара логин/пароль", "error")
    #
    # return render_template("login.html", menu=dbase.getMenu(), title="Авторизация")


@app.route("/register", methods=["POST", "GET"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
            hash = generate_password_hash(form.psw.data)
            res = dbase.addUser(form.name.data, form.email.data, hash)
            if res:
                flash("Ты в нашей тусе,colledge boy!", "success")
                return redirect(url_for('login'))
            else:
                flash("Почта уже использована", "error")

    return render_template("register.html", menu=dbase.getMenu(), title="Регистрация",form=form)



@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@app.route("/add_post", methods=["POST", "GET"])
@login_required
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
@login_required
def showPost(alias):
    title, post = dbase.getPost(alias)
    if not title:
        abort(404)

    return render_template('post.html', menu=dbase.getMenu(), title=title, post=post)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash("Вы вышли из профиля","success")
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return render_template('profile.html',menu=dbase.getMenu(),title='Профиль')


@app.route('/userava')
@login_required
def userava():
    img = current_user.getAvatar(app)
    if not img:
        return ""
    h = make_response(img)
    h.headers['Content-Type'] = 'image/png'
    return h


@app.route('/upload',methods =["POST","GET"])
@login_required
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and current_user.verifyExt(file.filename):
            try:
                img = file.read()
                res = dbase.updateUserAvatar(img,current_user.get_id())
                if not res:
                    flash("Ошибка обновления аватара профиля","error")
                flash("Аватар обновлен","success")
            except FileNotFoundError as e:
                flash("Ошибка чтения файла","error")
        else:
            flash("Ошибка обновления аватара","error")
    return redirect(url_for('profile'))
if __name__ == "__main__":
    app.run(debug=True)
