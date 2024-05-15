from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import Integer, String, Float
from flask_bootstrap import Bootstrap5
import random
import smtplib
from email.message import EmailMessage
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = "123456789"
app.config['SESSION_TYPE'] = 'filesystem'
bootstrap = Bootstrap5(app)


class Base(DeclarativeBase):
    pass


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
db = SQLAlchemy(model_class=Base)
db.init_app(app)


class Book(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(250), nullable=False)
    author: Mapped[str] = mapped_column(String(500), nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    category: Mapped[str] = mapped_column(String(500), nullable=False)
    img_name: Mapped[str] = mapped_column(String(500), nullable=True)
    price: Mapped[float] = mapped_column(Float(10), nullable=False)


with app.app_context():
    db.create_all()

# --------------------- EMAIL MANAGER ------------------------------------
my_email = os.environ.get('MY_EMAIL')
my_pw = os.environ.get('MY_PW')


def send_email(order):
    with smtplib.SMTP("smtp.gmail.com", port=587) as connection:
        msg = EmailMessage()
        msg['Subject'] = "Potvzení objednávky."
        msg['To'] = os.environ.get('MSG_TO')

        html_content = render_template('confirmation_email_client.html', order=order)
        msg.set_content(html_content, subtype='html')

        connection.starttls()
        connection.login(user=my_email, password=my_pw)
        connection.send_message(msg)


# --------------------- BOOKS BROWSING SECTION -----------------------------
@app.route("/", methods=(["GET", "POST"]))
def home():
    result = db.session.execute(db.select(Book).order_by(Book.id))
    data = result.scalars().all()

    unique_authors_tuple = db.session.query(Book.author).group_by(Book.author).all()
    unique_authors = [name[0] for name in unique_authors_tuple]

    unique_categories_tuple = db.session.query(Book.category).group_by(Book.category).all()
    unique_categories = [name[0] for name in unique_categories_tuple]

    # default setting
    menu_setting = {
        'authors': [(item, '') for item in unique_authors],
        'categories': [(item, '') for item in unique_categories],
    }

    if request.method == "POST":
        categories = request.form.getlist('category')
        authors = request.form.getlist('author')

        search_query = db.session.query(Book)
        if categories:
            search_query = search_query.filter(Book.category.in_(categories))
            menu_setting['categories'] = [(item, 'checked' if item in categories else '') for item in unique_categories]
        if authors:
            search_query = search_query.filter(Book.author.in_(authors))
            menu_setting['authors'] = [(item, 'checked' if item in authors else '') for item in unique_authors]
        data = search_query.order_by(Book.id).all()

    return render_template("index.html", data=data, settings=menu_setting)


@app.route("/kniha")
def book_detail():
    book_id = request.args.get('id')
    book_to_show = db.session.execute(db.select(Book).where(Book.id == book_id)).scalar()
    return render_template("book.html", book=book_to_show)


@app.route("/search", methods=(["POST"]))
def search():
    keyword = request.form.get('keyword')

    books = db.session.query(Book).filter(
        Book.name.ilike(f"%{keyword}%") |
        Book.author.ilike(f"%{keyword}%")).all()

    return render_template("search.html", books=books)


# --------------------- SHOPPING SECTION -----------------------------
def find_name(book_id):
    book = db.session.execute(db.select(Book).where(Book.id == book_id)).scalar()
    return book.name


@app.route('/add_to_cart/<item_id>')
def add_to_cart(item_id):
    if 'cart' not in session:
        session['cart'] = []
    session['cart'].append(item_id)
    flash(f'Položka "{find_name(item_id)}" úspěšně přidána.', 'success')  # Flash success message
    return redirect(url_for('view_cart'))


@app.route('/remove_from_cart/<item_id>')
def remove_from_cart(item_id):
    if 'cart' in session and item_id in session['cart']:
        session['cart'].remove(item_id)
        flash(f'Položka "{find_name(item_id)}" odebrána z košíku.', 'success')

    return redirect(url_for('view_cart'))


def ids_to_objects():
    cart_items = session.get('cart', [])
    items = [db.session.execute(db.select(Book).where(Book.id == int(id_from_cart))).scalar() for id_from_cart in
             cart_items]

    price = sum(item.price for item in items)
    return items, price


@app.route('/cart')
def view_cart():
    items, price = ids_to_objects()
    return render_template('cart.html', cart_items=items, price=price)


@app.route('/objednat_1')
def checkout_step_one():
    return render_template('checkout_s1.html')


@app.route('/objednat_2', methods=(["POST"]))
def checkout_step_two():
    # cart
    items, price = ids_to_objects()

    # delivery details
    del_options = {
        "personal": ["Osobní vyzvednutí", 0],
        "transport": ["Kurýrní služba", 99]
    }
    del_way = request.form.get('delivery')
    del_choice = del_options[del_way][0]

    # payment details
    pay_options = {
        "bank_transfer": ["Platba převodem", 0],
        "cod": ["Platba dobírkou přepravci při převzení", 30],
        "on_spot": ["Platba hotově při osobním vyzvednutí", 0]
    }
    pay_way = request.form.get('payment')
    payment_choice = pay_options[pay_way][0]

    # payment & delivery price
    price_two = float(del_options[del_way][1] + pay_options[pay_way][1])

    details = {
        "email": request.form.get('email'),
        "delivery": del_choice,
        "payment": payment_choice,
        "billing_name": request.form.get('billing_name'),
        "billing_address": request.form.get('billing_address'),
        "billing_city": request.form.get('billing_city'),
        "billing_zip": request.form.get('billing_zip'),
        "price_two": price_two
    }
    ship_details = {}
    if request.form.get('another_address') == 'checked':
        ship_details = {
            "shipping_name": request.form.get('shipping_name'),
            "shipping_address": request.form.get('shipping_address'),
            "shipping_city": request.form.get('shipping_city'),
            "shipping_zip": request.form.get('shipping_zip')
        }

    session['order'] = details

    return render_template('checkout_s2.html',
                           cart_items=items,
                           price=price,
                           details=details,
                           ship_details=ship_details)


@app.route('/objednat_2', methods=(["GET", "POST"]))
def checkout_step_three():
    order_details = session.get('order', {})
    print(order_details)
    # send email to customer

    # send email to owner

    return render_template('checkout_s3.html')


# --------------------- CoONDITION SECTION + OTHERS  -----------------------------
@app.route('/obch_podminky')
def business_conditions():
    return render_template('conditions.html')


@app.route('/os_udaje')
def personal_data():
    return render_template('conditions.html')


@app.route("/import")
def import_records():
    categories = ['Beletrie', 'Poezie', 'Literatura faktu', 'Naučná']
    authors = ['Jan Bílý', 'Pavel Bílek', 'Karel Bělský', 'Vilma Budínová']
    book_titles = ["Válka a mír", "Harry Potter a Kámen mudrců", "1984", "Pýcha a předsudek", "Ztracený ráj",
                   "Vítr v křídlech", "Krvavý břeh", "Stín a mlha", "Pán prstenů", "Obléhání"]

    for x in range(15):
        new_entry = Book(
            name=random.choice(book_titles),
            author=random.choice(authors),
            description="Kniha pojednává o zvláštním příběhu dvou lidí, kteří se hluboce mají rádi...",
            category=random.choice(categories),
            img_name="promena.jpg",
            price=random.randint(100, 200),
        )
        db.session.add(new_entry)
        db.session.commit()

    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
