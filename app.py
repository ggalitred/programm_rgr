from flask import Flask, render_template, request, g, redirect, jsonify, make_response, flash
import os
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3
from datetime import timedelta, datetime, timezone
from flask_jwt_extended import (JWTManager, create_access_token, jwt_required,
                                get_jwt_identity, get_jwt, get_csrf_token)
from FDataBase import FDataBase

app = Flask(__name__)

load_dotenv()
SECRET_KEY = os.getenv('SECRET_KEY')
JWT_KEY = os.getenv('JWT_KEY')

if SECRET_KEY is None:
    SECRET_KEY = "default_secret_key_should_be_changed"

if JWT_KEY is None:
    JWT_KEY = "default_jwt_key_should_be_changed"


DATABASE = '/tmp/site.db'
DEBUG = True

TOKEN_EXPIRES_LIFE = 300  # время жизни токена в секундах

app.config["JWT_SECRET_KEY"] = JWT_KEY  # секретный ключ
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(seconds=TOKEN_EXPIRES_LIFE)  # время жизни токена
app.config['JWT_TOKEN_LOCATION'] = ['cookies']  # место, в котором нужно искать токен
app.config['JWT_CSRF_IN_COOKIES'] = False  # запрет хранения CSRF-токена в куки-файлах
app.config['JWT_CSRF_CHECK_FORM'] = True  # хранение CSRF-токена в формах HTML

jwt = JWTManager(app)
app.config.from_object(__name__)

app.config.update(dict(DATABASE=os.path.join(app.root_path, 'site.db')))

def connect_db():
    conn = sqlite3.connect(app.config['DATABASE'])
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
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
@app.before_request
def before_request():
    global dbase
    db = get_db()
    dbase = FDataBase(db)


@app.teardown_appcontext
def close_db(error):
    if hasattr(g, 'link_db'):
        g.link_db.close()


@jwt.unauthorized_loader
def custom_unauthorized_response(_err):
    return redirect('/cabinet/login')


@app.after_request
def refresh_expiring_jwt(response):
    try:
        exp_timestamp = get_jwt()["exp"]
        now = datetime.now()
        target_timestamp = datetime.timestamp(now + timedelta(seconds=150))
        if target_timestamp > exp_timestamp:
            access_token = create_access_token(identity=get_jwt_identity())
            jti = get_jwt()["jti"]
            dbase.addRevokedToken(jti)
            response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Strict',
                                max_age=TOKEN_EXPIRES_LIFE)
        return response

    except (RuntimeError, KeyError):
        return response


@jwt.token_in_blocklist_loader
def check_is_token_is_revoked(jwt_header, jwt_payload: dict):
    jti = jwt_payload["jti"]
    token_in_db = dbase.getToken(jti)
    return token_in_db


# Регистрация
@app.route('/cabinet/register', methods=["POST", "GET"])
def register():
    print("register_page")
    print(str(request.method))
    if request.method == "POST":
        print("post")
        name_length = len(request.form['name'])
        if name_length < 2:
            flash('Неправильный ввод имени!', 'error')
            return render_template('register.html')

        patronymic_length = len(request.form['patronymic'])
        if patronymic_length < 2 and patronymic_length != 0:
            flash('Неправильный ввод отчества!', 'error')
            return render_template('register.html')

        if dbase.getUserByEmail(request.form['email']) is not None:
            flash('Пользователь уже зарегистрирован!', 'error')
            return render_template('register.html')

        password_length = len(request.form['password'])
        if password_length < 8:
            flash('Слишком короткий пароль!', 'error')
            return render_template('register.html')

        password = request.form['password']
        confirm_password = request.form['confirm-password']
        if password != confirm_password:
            flash('Пароли не совпадают!', 'error')
            return render_template('register.html')

        hash = generate_password_hash(request.form['password'])
        res = dbase.addUser(surname=request.form['surname'], name=request.form['name'], email=request.form['email'],
                             hpass=hash, patronymic=request.form['patronymic'])
        if res:
            print("OK")
            response = make_response(redirect('/cabinet/login'))
            response.set_cookie('RegMsg', 'Регистрация успешна!', max_age=1)
            return response
        else:
            print("NOT OK")

    return render_template('register.html')


# Вход в кабинет
@app.route('/cabinet/login', methods=["POST", "GET"])
def login():
    reg = request.cookies.get('RegMsg')
    print("REG:")
    print(str(reg))
    if reg:
        flash(reg, category="success")
    if request.method == "POST":
        user = dbase.getUserByEmail(request.form['email'])
        if not user:
            flash('Пользователь не найден!', 'error')
            return render_template('login.html')
        if not check_password_hash(user['password'], request.form['password']):
            flash('Неправильный пароль!', 'error')
            return render_template('login.html')

        access_token = create_access_token(identity=user['id'])
        response = make_response(redirect('/cabinet'))
        response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='Strict',
                            max_age=TOKEN_EXPIRES_LIFE)
        return response

    return render_template('login.html')


# Личный кабинет
@app.route('/cabinet', methods=["POST", "GET"])
@jwt_required()
def cabinet():
    user_id = get_jwt_identity()
    user = dbase.getUser(user_id)
    print("user: " + str(user))
    user_info = [user['surname'], user['name'], user['patronymic'], user['email']]
    return render_template('cabinet.html', user_info=user_info, role=user['role'])


# Выход из аккаунта
@app.route('/cabinet/logout')
@jwt_required()
def logout():
    response = make_response(redirect('/cabinet/login'))
    response.set_cookie('access_token_cookie', '')
    jti = get_jwt()["jti"]
    dbase.addRevokedToken(jti)
    return response


# Заявка на доступ к делу
@app.route('/cabinet/get_case', methods=["POST", "GET"])
@jwt_required()
def get_case():
    user_id = get_jwt_identity()
    print(str(user_id))
    print(request.method)
    token = request.cookies.get('access_token_cookie')
    csrf_token = get_csrf_token(token)

    if request.method == "GET":
        render_template("get_case.html", csrf_token=csrf_token)

    if request.method == "POST":
        res = dbase.addApplication(user_id, request.form['case_id'])
        if res:
            print("OK")
            return redirect('/cabinet/get_case')
        else:
            print("NOT OK")
            return redirect('/cabinet/get_case')

    return render_template("get_case.html", csrf_token=csrf_token)


# Главная страница
@app.route('/', methods=["POST", "GET"])
def hello():
    return JWT_KEY
    news = dbase.getNews(4)
    return render_template('main.html', news=news)


# Добавление дела в базу данных
@app.route('/cabinet/add_case', methods=["POST", "GET"])
@jwt_required()
def add_case():
    user_id = get_jwt_identity()
    user = dbase.getUser(user_id)
    token = request.cookies.get('access_token_cookie')
    csrf_token = get_csrf_token(token)

    if user['role'] != "admin":
        return redirect('/')

    if request.method == "GET":
        render_template("add_case.html", csrf_token=csrf_token)

    if request.method == "POST":
        res = dbase.addCase(request.form['description'], request.form['news_text'], request.form['article'])
        if res:
            print("OK")
        else:
            print("NOT OK")

    return render_template("add_case.html", csrf_token=csrf_token)


# Список дел/заявок
@app.route('/cabinet/cases')
@jwt_required()
def cases():
    user_id = get_jwt_identity()
    user = dbase.getUser(user_id)
    token = request.cookies.get('access_token_cookie')
    csrf_token = get_csrf_token(token)

    if user['role'] == "admin":
        rows = dbase.getApplicationsList()
        for row in rows:
            print(row[0], row[1], row[2], row[3])

        user_info = dbase.getUserByApplicationID(row[0])

        return render_template('admin_cases.html', rows=rows, csrf_token=csrf_token, user_info=user_info)

    rows = dbase.getApplicationsByUserID(user_id)
    cases_output = []
    if rows:
        for row in rows:

            if row['app_status'] == "pass":
                description = dbase.getApplicationInfo(row['case_id'])
                cases_output.append([row['case_id'], row['app_status'], description['description']])
            else:
                cases_output.append([row['case_id'], row['app_status']])

            print(f"ID: {row['id']}, User ID: {row['user_id']}, Case ID: {row['case_id']}, Status: {row['app_status']}")

    print(cases_output)
    return render_template('cases.html', rows=cases_output)


# Разрешение или отказ к доступу для дела
@app.route("/cabinet/cases/<application_id>/grant_access", methods=["POST"])
@jwt_required()
def get_access(application_id):
    user_id = get_jwt_identity()
    user = dbase.getUser(user_id)
    token = request.cookies.get('access_token_cookie')
    csrf_token = get_csrf_token(token)

    if user['role'] != "admin":
        return redirect('/')

    if request.method == "GET":
        render_template("add_case.html", csrf_token=csrf_token)

    print(request.form['app_status'])
    dbase.setApplicationStatus(application_id, request.form['app_status'])
    return redirect('/cabinet/cases')


# Новости
@app.route('/news_list', methods=["GET"])
def news():
    news = dbase.getNews()
    print(news)
    return render_template('news.html', news=news)


# Добавление новости
@app.route('/cabinet/add_news', methods=["POST", "GET"])
@jwt_required()
def add_news():
    user_id = get_jwt_identity()
    user = dbase.getUser(user_id)
    token = request.cookies.get('access_token_cookie')
    csrf_token = get_csrf_token(token)

    if user['role'] != "admin":
        return redirect('/')

    cases = dbase.getCases()
    if request.method == "GET":
        render_template("add_news.html", csrf_token=csrf_token, cases=cases)

    if request.method == "POST":
        res = dbase.addNews(request.form['news_article'], request.form['news_text'], request.form['case_id'])
        if res:
            print("OK")
        else:
            print("NOT OK")

    return render_template('add_news.html', csrf_token=csrf_token, cases=cases)


# Просмотр информации по конкретной новости
@app.route("/news/<news_id>", methods=["GET"])
@jwt_required(optional=True)
def news_info(news_id):
    news = dbase.getOneNews(news_id)
    commentaries = dbase.getCommentaries(news_id)
    try:
        token = request.cookies.get('access_token_cookie')
        if token:
            print("GetUserInfo_started")
            user_id = get_jwt_identity()
            user = dbase.getUser(user_id)
            csrf_token = get_csrf_token(token)
        else:
            user = None
            csrf_token = ""
    except Exception as e:
        print("Ошибка добавления комментария1: " + str(e))
        user = None
        csrf_token = ""
    return render_template("current_news.html", news=news, user=user, csrf_token=csrf_token,
                           commentaries=commentaries, news_id=news_id)


# Добавление комментария к новости
@app.route("/news/<news_id>/add_commentary", methods=["POST"])
@jwt_required()
def add_commentary(news_id):
    if request.method == "POST":
        try:
            token = request.cookies.get('access_token_cookie')
            if token:
                print("fucntion_started")
                user_id = get_jwt_identity()
                user = dbase.getUser(user_id)
                comment_text = request.form['comment_text']
                dbase.addCommentary(news_id, user['email'], comment_text)
            else:
                return redirect("/cabinet/login")
        except Exception as e:
            print("Ошибка добавления комментария2: " + str(e))
            return redirect("/news")

    return redirect("/news/" + news_id)


if __name__ == '__main__':
    app.run()
