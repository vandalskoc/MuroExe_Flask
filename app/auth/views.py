from flask import render_template, flash, redirect, url_for, request
from .forms import RegistrationForm, LoginForm, InformationForm, AddressForm, OrderForm,UseVoucherForm
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from ..models import User, Address, Cart, Product, Order, CartItem, Role, OrderProduct, StockAndSize, Voucher, Revenue
from ..import db
from ..email import send_email
from currency2text import currency_to_text




@auth.route('/login', methods=['GET','POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter((User.username==form.username.data.lower()) \
                                    | (User.email==form.username.data.lower())).first()
        # user = User.query.filter_by(username=form.username.data.lower()).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user)
            next = request.args.get('next')
            if next is None or not next.startswith('/'):
                if user.is_user():
                    if(not current_user.confirmed):
                        flash("You need to confirm your email and fill in your information, address to start shopping")
                        return redirect(url_for('auth.infor'))
                    next = url_for('main.index')
                else:
                    next = url_for('admin.manage')
            return redirect(next)
        flash('Invalid user or password.')
    return render_template('auth/login.html',form=form)


@auth.route('/register', methods=['GET','POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        role = Role.query.filter_by(name='User').first()
        print(role)
        user = User(email=form.email.data.lower(),
                    username=form.username.data,
                    password=form.password.data,
                    role=role)
        db.session.add(user)
        db.session.commit()
        flash('Register complete!, Login to fill in more data')
        return redirect(url_for('auth.login'))
    return render_template('auth/register.html', form=form)

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/infor', methods=['GET','POST'])
@login_required
def infor():
    inforForm = InformationForm()
    if(not current_user.confirmed):
        flash("You need to confirm your email and fill in your information, address to start shopping")
    
    if inforForm.validate_on_submit():
        current_user.fullname = inforForm.fullname.data
        current_user.phone = inforForm.phone.data
        current_user.dob = inforForm.dob.data
        db.session.commit()
        flash("Information updated")

    return render_template('user/account_infor.html', inforForm=inforForm)


@auth.route('/address', methods=['GET','POST'])
@login_required
def address():
    addressForm = AddressForm()
    if addressForm.validate_on_submit():    
        new_address = Address(address=addressForm.address.data,
        city=addressForm.city.data,
        postal_code=addressForm.postal_code.data,
        country = addressForm.country.data,
        user_id = current_user.id)
        db.session.add(new_address)
        db.session.commit()
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    print("Addres:",len(addresses))
    return render_template('user/account_address.html', addressForm=addressForm, addresses=addresses)

@auth.route('/delete_address/<address_id>', methods=['GET','POST'])
@login_required
def delete_address(address_id):
    is_deleted = Address.query.filter_by(id=address_id).delete()
    db.session.commit()
    flash('Deleted Address')
    return redirect(url_for('auth.address'))

@auth.route('/make_default/<address_id>', methods=['GET','POST'])
@login_required
def make_address_default(address_id):
    #Check if have other default
    default_address = Address.query.filter_by(is_default=True).first()
    if( default_address ):
        default_address.is_default=False
        db.session.commit()
    else:
        address = Address.query.filter_by(id=address_id).first()
        address.is_default=True
        db.session.commit()
        flash(address.address + ' is now default address')
    return redirect(url_for('auth.address'))

@auth.route('/adding_address', methods=['GET','POST'])
@login_required
def adding_address():
    addressForm = AddressForm()
    if addressForm.validate_on_submit():    
        new_address = Address(address=addressForm.address.data,
        city=addressForm.city.data,
        postal_code=addressForm.postal_code.data,
        country = addressForm.country.data,
        user_id = current_user.id)

        db.session.add(new_address)

        db.session.commit()
        flash('Added new address')
        return redirect(url_for('auth.address'))
    return render_template('user/add_address.html',addressForm=addressForm)

@auth.route('/voucher')
@login_required
def voucher():
    return render_template('user/account_voucher.html')

@auth.route('/history')
@login_required
def history():
    orders = Order.query.filter_by(user_id=current_user.id).all()
    add = Address.query.filter_by(user_id=current_user.id)
    order_pd = OrderProduct
    return render_template('user/account_history.html',orders=orders,add=add,order_pd=order_pd)

@auth.route('/order_bill/<order_id>')
@login_required
def OrderBill(order_id):
    get_order = Order.query.filter_by(id=order_id).first()
    produtcs_inorder = OrderProduct.query.filter_by(order_id=order_id)
    pd_model = Product
    total=0
    address = Address.query.filter_by(id=get_order.address_id).first()

    for pd in produtcs_inorder:
        product = pd_model.query.filter_by(id=pd.product_id).first().price
        total += product*pd.quantity  
    grand_total_intext = str(currency_to_text(get_order.total, 'EUR', 'en_US'))[2:-1]
    return render_template('user/order_bill.html',grand_total_intext=grand_total_intext,address=address,get_order=get_order,produtcs_inorder=produtcs_inorder,pd_model=pd_model,total=total)

@auth.route('/cart', methods=['GET','POST'])
@login_required
def GetCart():
    
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    if(cart):
        cart_items = CartItem.query.filter_by(cart_id=cart.id)
    else:
        new_cart = Cart(user_id=current_user.id)
        db.session.add(new_cart)
        db.session.commit()
        cart_items = None
    #Check voucher code
    voucher_code = request.args.get('voucher')
    voucher = Voucher.query.filter_by(code=voucher_code).first()
    
    if(voucher):
        code = voucher_code
        discount = voucher.discount
    else:
        discount = float(0)
        code = 'n'

    return render_template('user/user_cart.html',cart=cart,cart_items=cart_items,discount=discount,n=code)

@auth.route('/checkout_address/<n>', methods=['GET','POST'])
@login_required
def CheckOutAddress(n):
    if( not current_user.confirmed):
        flash('Please confirm your email before shopping')
        return redirect(url_for('auth.infor'))
    #Check if user fill in all the personal infor and address
    exist_address = Address.query.filter_by(user_id=current_user.id).all()
    if( not exist_address and current_user.fullname == None or not current_user.phone ):
        flash("Please fill in your name,phone number and address before checkout")
        return redirect(url_for('auth.infor'))
    if(not exist_address):
        flash("Please add an shipping address before checkout")
        return redirect(url_for('auth.infor'))
    if( current_user.fullname == None or not current_user.phone):
        flash("Please fill in your name and phone number before checkout")
        return redirect(url_for('auth.infor'))
    print(n)
    #Check voucher code
    voucher = Voucher.query.filter_by(code=n).first()
    if(voucher):
        discount = voucher.discount
    else:
        discount=float(0)
    order_form = OrderForm()
    total=0
    item_count=0
   
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart_items = CartItem.query.filter_by(cart_id=cart.id)
    for pd in cart_items:
        item_count += pd.quantity
        price_per_product = float(pd.product.price) * int(pd.quantity)
        total += price_per_product
    final_price = total + discount
    
    addresses = Address.query.filter_by(user_id=current_user.id).all()
    
    param_address = request.args.get('address_id')
    chosen_address = Address.query.filter_by(id=param_address).first()

    return render_template('user/user_order_address.html',n=n,cart_id=cart.id,form=order_form,cart_items=cart_items,total=total,item_count=item_count,final_price=final_price,discount=discount,addresses=addresses,chosen_address=chosen_address)

@auth.route('/checkout_address/set/<address_id>/<n>', methods=['GET','POST'])
@login_required
def SetOrderAddress(address_id,n):
    return redirect(url_for('auth.CheckOutAddress',address_id=address_id, n=n))


@auth.route('/place_order', methods=['GET','POST'])
@login_required
def PlaceOrder():
    order_form = OrderForm()
    
    if order_form.validate_on_submit():
        new_order = Order(user_id=current_user.id,
                        address_id=order_form.address.data,
                        total = order_form.total.data,
                        payment=order_form.payment.data)
        get_cart_item = CartItem.query.filter_by(cart_id=order_form.cart_id.data).all()
        for item in get_cart_item:
            pd = Product.query.filter_by(id=item.product_id).first()
            order_pd = OrderProduct(
                order=new_order,
                product=pd,
                size=item.size,
                quantity=item.quantity
            )
            #Product Stock decrease by quantity.
            product_stock_size = StockAndSize.query.filter_by(product_id=item.product_id,size=item.size).first()
            in_stock = product_stock_size.stock
            product_stock_size.stock = in_stock - item.quantity
            db.session.add(order_pd)
            db.session.commit()
        #Delete old cart
        old_items = CartItem.query.filter_by(cart_id=order_form.cart_id.data).delete()
        db.session.commit() 
        
       
        # FOR EMAIL CONTENT
        # order_id = new_order.id
        # get_order = Order.query.filter_by(id=order_id).first()
        # produtcs_inorder = OrderProduct.query.filter_by(order_id=order_id)
        # pd_model = Product
        # total=0
        # address = Address.query.filter_by(id=get_order.address_id).first()

        # for pd in produtcs_inorder:
        #     product = pd_model.query.filter_by(id=pd.product_id).first().price
        #     total += product*pd.quantity  
        # grand_total_intext = str(currency_to_text(get_order.total, 'EUR', 'en_US'))[2:-1]
        # discount = get_order.total - total
        # send_email(current_user.email, 'Your shopping receipt','auth/email/bill',discount=discount, grand_total_intext=grand_total_intext,address=address,get_order=get_order,produtcs_inorder=produtcs_inorder,pd_model=pd_model,total=total)
        flash("Your order have been placed.")
    return redirect(url_for('auth.history'))
       
@auth.route('/cancel_order/<order_id>', methods=['GET','POST'])
@login_required
def CancelOrder(order_id):
    order = Order.query.filter_by(id=order_id).first()
    if(order.status=='Preparing'):
        order_product = OrderProduct.query.filter_by(order_id=order_id)
        order_delte = Order.query.filter_by(id=order_id).delete()
        
        for item in order_product:
            print(item.product_id)
            print(item.size)
            print(item.quantity)
            product_stock = StockAndSize.query.filter_by(product_id=item.product_id,size=item.size).first()
            product_stock.stock += item.quantity
            db.session.commit()
        order_product.delete()
        db.session.commit()
        flash('Order canceled')
        return redirect(url_for('auth.history'))
    else:
        flash('Order already shipping, cannot cancel')
        return redirect(url_for('auth.history'))
@auth.route('/checkout_payment', methods=['GET','POST'])
def CheckOutPayment():
    # cart = Cart.query.filter_by(user_id=current_user.id).first()
    return render_template('user/user_order_payment.html')


#EMAIL SECTION
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        db.session.commit()
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.route('/send_confirm', methods=['GET','POST'])
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('auth.infor'))

