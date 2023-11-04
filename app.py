from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_admin.contrib.sqla.fields import QuerySelectField
from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate
from wtforms import SelectField
from flask_admin.form import Select2Widget
from wtforms import Form, StringField, TextAreaField, FloatField
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


app = Flask(__name__)

app.config['SESSION_COOKIE_SECURE'] = True  # Обязательно убедитесь, что сайт работает через HTTPS
app.config['SESSION_COOKIE_SAMESITE'] = 'None'

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shop.db'
app.config['SECRET_KEY'] = '213jhbfguj1h1gs'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

admin = Admin(app)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)

    def __str__(self):
        return self.name


class Subcategory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)
    category = db.relationship('Category', backref='subcategories')

    def __str__(self):
        return self.name


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    about = db.Column(db.Text, nullable=True)
    price = db.Column(db.Float, nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategory.id'), nullable=False)
    subcategory = db.relationship('Subcategory', backref='products')

    def __repr__(self):
        return self.title


class Service(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(100), nullable=True)


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


class SubcategoryForm(Form):
    name = StringField('Name')
    category = QuerySelectField('Category', query_factory=lambda: Category.query.all())


class SubcategoryModelView(ModelView):
    column_list = ['name', 'category']  # Список отображаемых колонок
    form_columns = ['name', 'category']  # Колонки, которые отображаются в форме редактирования
    form = SubcategoryForm  # Используем нашу форму
    column_searchable_list = ['name']  # Список колонок, в которых можно выполнять поиск
    column_filters = ['category']  # Список колонок, по которым можно фильтровать данные


admin.add_view(ModelView(Service, db.session))
admin.add_view(ModelView(Category, db.session))
admin.add_view(SubcategoryModelView(Subcategory, db.session))
admin.add_view(ModelView(Product, db.session))
admin.add_view(ModelView(User, db.session))


@app.route('/')
def index():  # put application's code here
    return render_template('index.html', menu=menu, title='Главная')


@app.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('You need to log in to access this page', 'danger')
        return redirect(url_for('authorization'))

    user = User.query.get(session['user_id'])
    return render_template('profile.html', menu=menu, user=user, title=user.username)


@app.route('/authorization', methods=['GET', 'POST'])
def authorization():
    if 'user_id' in session:
        flash('You are already logged in', 'info')
        return redirect(url_for('profile'))

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

    return render_template('authorization.html', menu=menu, title="Авторизация")


@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have been logged out', 'info')
    return redirect(url_for('index'))


@app.route('/registration', methods=['GET', 'POST'])
def register():
    if 'user_id' in session:
        flash('You are already logged in', 'info')
        return redirect(url_for('profile'))

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
    # Получение списка всех категорий
    categories = Category.query.all()

    # Инициализация переменных категории и подкатегории
    selected_category = None
    selected_subcategory = None

    # Проверка, были ли отправлены данные POST-запросом
    if request.method == 'POST':
        # Получение выбранных категории и подкатегории из формы
        selected_category_id = request.form.get('category')
        selected_subcategory_id = request.form.get('subcategory')

        # Поиск выбранных категории и подкатегории
        if selected_category_id:
            selected_category = Category.query.get(selected_category_id)

        if selected_subcategory_id:
            selected_subcategory = Subcategory.query.get(selected_subcategory_id)

    # Получение товаров на основе выбранных категории и подкатегории
    if selected_subcategory:
        products = selected_subcategory.products
    elif selected_category:
        # Если выбрана только категория, получите все товары из подкатегорий этой категории
        products = Product.query.join(Subcategory).filter(Subcategory.category_id == selected_category.id).all()
    else:
        # Если не выбрана категория и подкатегория, получите все товары
        products = Product.query.all()

    return render_template('goods.html', menu=menu, categories=categories, data=products)


@app.route('/get_subcategories', methods=['GET'])
def get_subcategories():
    category_id = request.args.get('category_id')
    subcategories = Subcategory.query.filter_by(category_id=category_id).all()

    print(subcategories)  # Выводите данные в консоль для отладки

    subcategories_data = [{'id': subcategory.id, 'name': subcategory.name} for subcategory in subcategories]
    return jsonify(subcategories_data)


@app.route('/get_products', methods=['GET'])
def get_products():
    category_id = request.args.get('category_id')
    subcategory_id = request.args.get('subcategory_id')

    # Проверьте, были ли предоставлены категория и подкатегория
    if category_id:
        category = Category.query.get(category_id)

        if category:
            if subcategory_id:
                # Если предоставлена как подкатегория, получите товары только из этой подкатегории
                products = Product.query.filter_by(subcategory_id=subcategory_id).all()
            else:
                # Если подкатегория не предоставлена, получите все товары из данной категории
                products = Product.query.join(Subcategory).filter(Subcategory.category_id == category_id).all()
        else:
            # Категория не найдена, вернуть пустой результат или сообщение об ошибке
            return jsonify([])  # или jsonify({'error': 'Category not found'})

    else:
        # Если категория не предоставлена, получите все товары
        products = Product.query.all()

    # Преобразуйте данные о продуктах в формат JSON и верните их клиенту
    product_data = [{'name': product.name, 'about': product.about, 'price': product.price} for product in products]
    return jsonify(product_data)


@app.route('/services')
def services():
    if request.method == 'POST':
        service_name = request.form.get('service_name')
        return render_template('services.html', menu=menu, title="Услуги", service_name=service_name)
    else:
        service = Service.query.order_by(Service.name).all()
        return render_template('services.html', data=service, menu=menu, title="Услуги")


@app.route('/submit_phone', methods=['POST'])
def submit_phone():
    phone_number = request.form['phone_number']
    service_name = request.form['service_name']  # Получаем название услуги

    # Отправка уведомления на почту
    recipient_email = 'paninnskk@gmail.com'  # Замените на вашу почту
    subject = 'Заказ услуги'
    message = f'Номер телефона: {phone_number}, Заказанная услуга: {service_name}'  # Замените service_name на реальное значение

    # Ваш SMTP сервер и учетные данные
    smtp_server = 'connect.smtp.bz'
    smtp_port = 587
    smtp_user = 'paninnskk@gmail.com'
    smtp_password = 'DGkCQEHnLRSR'

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = recipient_email
    msg['Subject'] = subject

    msg.attach(MIMEText(message, 'plain'))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        text = msg.as_string()
        server.sendmail(smtp_user, recipient_email, text)
        server.quit()
    except Exception as e:
        return jsonify({'message': f'Error: {str(e)}'})

    return jsonify({'message': 'Phone number submitted successfully'})


@app.route('/news')
def news():
    return render_template('news.html', menu=menu)


if __name__ == '__main__':
    app.run(debug=True)