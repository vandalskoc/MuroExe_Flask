from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app
from flask_login import UserMixin,  AnonymousUserMixin
from . import db, login_manager
from sqlalchemy import DateTime
from datetime import datetime

class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    permission = db.Column(db.Integer, default = 0)
    users = db.relationship('User', backref='role', lazy='dynamic')
    
    def insert_permission(self):
        dict_permission = {
            'Admin' : 32,
            'Manager' : 16,
            'Warehouse Manager' : 8,
            'Sales Employee' : 4,
            'Shipper' : 2,
            'User' :  1 
        }
        self.permission = dict_permission[self.name]
        db.session.commit()
    def __repr__(self):
        return '<Role %r>' % self.name


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64))
    fullname = db.Column(db.String(64))
    phone = db.Column(db.String(10))
    dob = db.Column(db.Date())
    #Create Enum for Gender
    gender = db.Column(db.Boolean, default=False)
    #ballance = db.Column(db.Integer)
    create_date = db.Column(db.DateTime(), default=datetime.utcnow)


    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), default=2)
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)

    #Mot User co nhieu Address
    addresses = db.relationship('Address', backref='users')
    #Mot User co mot Cart
    cart =db.relationship('Cart',uselist=False, backref='users')
    #Mot User co nhieu Order
    order = db.relationship("Order",backref='users')
    
    def is_user(self):
        return Role.query.get(self.role_id).name == 'User'

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id}).decode('utf-8')

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token.encode('utf-8'))
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def __repr__(self):
        return '<User %r>' % self.username
class AnonymousUser(AnonymousUserMixin):

    def is_user(self):
        return "User"

login_manager.anonymous_user = AnonymousUser

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Address(db.Model):
    __tablename__='addresses'
    id = db.Column(db.Integer, primary_key=True)
    address = db.Column(db.String())
    city  = db.Column(db.String())
    area  = db.Column(db.String())
    postal_code  = db.Column(db.String())
    country  = db.Column(db.String())
    is_default = db.Column(db.Boolean(), default=False)
    #Mot Address thuoc ve mot User
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class Category(db.Model):
    __tablename__= 'categories'
    id = db.Column(db.Integer, primary_key=True)
    category_name = db.Column(db.String(64), unique=True, index=True)
    # Mot Category co nhieu san pham
    products = db.relationship('Product', backref='categories')




class Cart(db.Model):
    __tablename__='carts'
    id = db.Column(db.Integer, primary_key=True)
    #Mot cart thuoc ve mot user
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))    
    cart_items = db.relationship('CartItem', backref='cart', lazy='dynamic')
    
class CartItem(db.Model):
    __tablename__="cart_items"
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('carts.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    product = db.relationship("Product", backref=("cart_items"), uselist=False)
    quantity = db.Column(db.Integer)
    size = db.Column(db.Integer)

class OrderProduct(db.Model):
    __tablename__ = 'order_product'
    id = db.Column(db.Integer,primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'))
    size = db.Column(db.Integer)
    quantity = db.Column(db.Integer)
    order = db.relationship("Order", backref=("order_product"))
    product = db.relationship("Product")

    def __init__(self, product=None, order=None, size=None,quantity=None):
        self.order = order
        self.product = product
        self.size = size
        self.quantity = quantity

class Order(db.Model):
    __tablename__='orders'
    id = db.Column(db.Integer,primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    address_id = db.Column(db.Integer, db.ForeignKey('addresses.id'))
    total = db.Column(db.Float)
    status = db.Column(db.String(), default='Preparing')
    product_inorder = db.relationship("Product", secondary='order_product', backref='product_inorders',overlaps="order,order_product")
    payment = db.Column(db.String())
    create_date = db.Column(db.DateTime(), default=datetime.utcnow)
    user_note = db.Column(db.String())
    revenue_id = db.Column(db.Integer, db.ForeignKey('revenue.id'))

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(64), index=True)
    product_img = db.Column(db.String())
    product_subimg1 = db.Column(db.String())
    product_subimg2 = db.Column(db.String())
    product_subimg3 = db.Column(db.String())
    price = db.Column(db.Float)
    desc = db.Column(db.String())
    color = db.Column(db.String())
    material = db.Column(db.String())
    style = db.Column(db.String())
    tag = db.Column(db.String())
    # Mot san pham co nhieu size 
    sizes = db.relationship('StockAndSize', backref='products')
    # Mot San pham thuoc ve mot Category
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
  
    
    
class StockAndSize(db.Model):
    __tablename__ = 'product_stock'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), index=True)
    size = db.Column(db.String())
    stock = db.Column(db.Integer)

    
class BannerImage(db.Model):
    __tablename__='banner_images'
    id = db.Column(db.Integer, primary_key=True)
    banner = db.Column(db.String())
    is_disable = db.Column(db.Boolean(), default=False)


class Voucher(db.Model):
    __tablename__="vouchers"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String())
    code = db.Column(db.Integer)
    discount = db.Column(db.Float)
    expire_date = db.Column(db.Date())
    create_date = db.Column(db.Date(), default=datetime.utcnow)
    max_usage = db.Column(db.Integer, default=1000)

class Revenue(db.Model):
    __tablename__="revenue"
    id = db.Column(db.Integer, primary_key=True)
    total_sale = db.Column(db.Float)
    quarter = db.Column(db.Integer)
    year = db.Column(db.Integer)
    order  = db.relationship('Order')





