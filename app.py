from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
# from flask_login import LoginManager, login_user, logout_user, login_required


app = Flask(__name__)

app.config['SESSION_COOKIE_SECURE'] = True  # Обязательно убедитесь, что сайт работает через HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SECRET_KEY'] = '213jhbfguj1h1gs'

db = SQLAlchemy(app)

admin = Admin(app)


class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    about = db.Column(db.Text)
    price = db.Column(db.Integer)
    isActive = db.Column(db.Boolean, default=True)

    def __repr__(self):
        return self.title


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(50), nullable=False)
    password = db.Column(db.Text, nullable=False)
    isAdmin = db.Column(db.Boolean, default=False)

    def check_password(self, password):
        return check_password_hash(self.password, password)


menu = [
    {"name": "Главная", "url": "/"},
    {"name": "Каталог", "url": "/goods"},
    {"name": "Услуги", "url": "/services"},
    {"name": "О нас", "url": "/about"},
    {"name": "Новости", "url": "/news"},
]


# class UserModelView(ModelView):
#     column_exclude_list = ['password']


admin.add_view(ModelView(Item, db.session))
admin.add_view(ModelView(User, db.session))


@app.route('/')
def index():  # put application's code here
    return render_template('index.html', menu=menu)


@app.route('/profile')
def profile():
    user = None
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
    return render_template('profile.html', user=user)


@app.route('/authorization', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['user_id'] = user.id
            flash('Login successful', 'success')
            return redirect(url_for('profile'))
        else:
            flash('Login failed. Check your credentials.', 'danger')

    return render_template('authorization.html')


# @app.route('/logout')
# def logout():
#     session.pop('user_id', None)
#     flash('You have been logged out', 'info')
#     return redirect(url_for('index'))


@app.route('/registration', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        # Проверяем, существует ли пользователь с таким email
        existing_user = User.query.filter_by(email=email).first()

        if existing_user:
            flash('User with this email already exists', 'error')
        else:
            # Хэшируем пароль перед сохранением
            hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

            new_user = User(username=username, email=email, password=hashed_password)
            db.session.add(new_user)
            db.session.commit()

            flash('You have been registered successfully', 'success')

            # Устанавливаем сессию для пользователя
            session['user_id'] = new_user.id

            return redirect(url_for('profile'))

    return render_template('registration.html', menu=menu)


@app.route('/about')
def about():
    return render_template('about.html', menu=menu)


@app.route('/goods')
def goods():
    items = Item.query.order_by(Item.price).all()
    return render_template('goods.html', menu=menu, data=items)


@app.route('/services')
def services():
    return render_template('services.html', menu=menu)


@app.route('/news')
def news():
    return render_template('news.html', menu=menu)


if __name__ == '__main__':
    app.run(debug=True)