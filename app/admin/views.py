from flask import render_template, current_app as app, redirect,url_for,flash,request
from . import admin
from .forms import AddProductForm,EditProductForm,AddStockForm,UpdateStockForm,AddBannerImageForm,AddVoucherForm
from ..models import Address, Product, Category, StockAndSize, BannerImage,Role, Voucher, Order,User,Revenue
from .. import db
from werkzeug.utils import secure_filename
import uuid as uuid
import os
import json
from config import config
from flask_login import current_user
from functools import wraps
import datetime

def is_admin(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if (current_user.role.permission & 63) < 32:
            flash("Bạn không có quyền truy cập!")
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin.route('/')
@is_admin
def index():
    return render_template('admin/index.html')

@admin.route('/e')
def manage():
    role = current_user.role.name
    if role == 'Admin':
        return redirect(url_for('admin.index'))
    return render_template('manage/index.html', user=current_user)
    
    
@admin.route('/add_product', methods=['GET','POST'])
def AddProduct():
    form = AddProductForm()
    print(form.validate_on_submit())
    if form.validate_on_submit():
        category = Category.query.filter_by(category_name=form.category.data).first()
        uploaded_picture = form.product_img.data
        uploaded_sub_picture1 = form.product_subimg1.data
        uploaded_sub_picture2 = form.product_subimg2.data
        uploaded_sub_picture3 = form.product_subimg3.data
        print(form.product_name.data)
        #Secure Product Picture Prevent Inject SQL Attck
        uploaded_picture_name = secure_filename(uploaded_picture.filename)
        uploaded_sub_picture1_name =  secure_filename(uploaded_sub_picture1.filename)
        uploaded_sub_picture2_name =  secure_filename(uploaded_sub_picture2.filename)
        uploaded_sub_picture3_name =  secure_filename(uploaded_sub_picture3.filename)

        #Set unique id to picture name and save
        product_img_name = str(uuid.uuid1()) + "_" + uploaded_picture_name
        uploaded_picture.save(os.path.join(app.config['UPLOAD_FOLDER'], product_img_name))


        product_subimg1_name = str(uuid.uuid1()) + "_" + uploaded_sub_picture1_name
        uploaded_sub_picture1.save(os.path.join(app.config['UPLOAD_FOLDER'], product_subimg1_name))
        
        product_subimg2_name = str(uuid.uuid1()) + "_" + uploaded_sub_picture2_name
        uploaded_sub_picture2.save(os.path.join(app.config['UPLOAD_FOLDER'], product_subimg2_name))
        
        product_subimg3_name = str(uuid.uuid1()) + "_" + uploaded_sub_picture3_name
        uploaded_sub_picture3.save(os.path.join(app.config['UPLOAD_FOLDER'], product_subimg3_name))
        
        product = Product(product_name=form.product_name.data,
                            product_img=product_img_name,
                            product_subimg1=product_subimg1_name,
                            product_subimg2=product_subimg2_name,
                            product_subimg3=product_subimg3_name,
                            price = form.price.data,
                            desc = form.desc.data,
                            categories=category)
        db.session.add(product)
        db.session.commit()
 
    return render_template('admin/add_product.html', form=form)

@admin.route('/manage_product/<category>', methods=['GET','POST'])
def ManageProduct(category):
    ctgr = Category.query.filter_by(category_name=category).first()
    products = Product.query.filter_by(category_id=ctgr.id).all()
    return render_template('admin/manage_product.html', products=products)

@admin.route('/delete/<product_id>', methods=['GET','POST'])
def DeleteProduct(product_id):
    is_deleted = Product.query.filter_by(id=product_id).delete()
    db.session.commit()
    return redirect(url_for('admin.ManageProduct',category='shoes'))

@admin.route('/edit_for/<product_id>', methods=['GET','POST'])
def EditProduct(product_id):
    product = Product.query.filter_by(id=product_id).first()
    ctgr = Category.query.filter_by(id=product.category_id).first()
    print(ctgr.category_name)
    editForm = EditProductForm()
    if editForm.validate_on_submit():
        product.product_name = editForm.product_name.data
        product.price = editForm.price.data
        product.tag = editForm.tag.data 
        product.color = editForm.color.data
        product.style = editForm.style.data
        product.material = editForm.material.data
        db.session.commit()
        return redirect(url_for('admin.ManageProduct',category=ctgr.category_name))   
    return render_template('admin/edit_product.html', product=product, form=editForm,ctgr=ctgr)
   
@admin.route('/check_stock/<product_id>', methods=['GET','POST'])
def CheckStock(product_id):
    product = Product.query.filter_by(id=product_id).first()
    ctgr = Category.query.filter_by(id=product.category_id).first()
    sizes = StockAndSize.query.filter_by(product_id=product_id)
    stockForm = AddStockForm()
    updateForm = UpdateStockForm()
    if stockForm.validate_on_submit():
        print("STOCK FORM SUBMIT")
        size_exist = StockAndSize.query.filter_by(size=stockForm.size.data,product_id=product.id).first()
        if( not size_exist):
            stock = StockAndSize(size=stockForm.size.data,
                                    stock=stockForm.stock.data,
                                    product_id=product.id)
            db.session.add(stock)
            db.session.commit()
        else:
            flash("Size Exist")
            return redirect(url_for('admin.CheckStock',product_id=product.id))   
    if updateForm.validate_on_submit():
        print("UPDATING STOCK VALUE")
    return render_template('admin/product_stock.html', product=product,sizes=sizes,form=stockForm, updateForm=updateForm,ctgr=ctgr)

@admin.route('/update_stock/<size_id>', methods=['POST'])
def UpdateStock(size_id):
    stock = StockAndSize.query.filter_by(id=size_id).first()
    product = Product.query.filter_by(id=stock.product_id).first()
    updateForm = UpdateStockForm()
    if updateForm.validate_on_submit():
        stock.stock = updateForm.stock.data
        db.session.commit()
        print(stock.stock)
        print(updateForm.stock.data)
        print("FORM WORKING")
    return "Updated"
    # return redirect(url_for('admin.CheckStock',product_id=product.id))   

@admin.route('/banner_page', methods=['GET','POST'])
def PageBanner():
    banners = BannerImage.query.all()
    addbannerForm = AddBannerImageForm()
    if addbannerForm.validate_on_submit():
        banner_image_name = str(uuid.uuid1()) + "_" + secure_filename(addbannerForm.banner.data.filename)
        addbannerForm.banner.data.save(os.path.join(app.config['UPLOAD_FOLDER']+'/Banner', banner_image_name))
        banner = BannerImage(
            banner = banner_image_name,
            is_disable = addbannerForm.is_disable.data
        )
        db.session.add(banner)
        db.session.commit()
        return redirect(url_for('admin.PageBanner'))
    return render_template('admin/page_banner.html',banners=banners, addbannerForm = addbannerForm)

@admin.route('/disable_banner/<banner_id>', methods=['GET','POST'])
def DisableBanner(banner_id):
    banner = BannerImage.query.filter_by(id=banner_id).first()
    banner.is_disable=True
    db.session.commit()
    return redirect(url_for('admin.PageBanner'))

@admin.route('/enable_banner/<banner_id>', methods=['GET','POST'])
def EnableBanner(banner_id):
    banner = BannerImage.query.filter_by(id=banner_id).first()
    banner.is_disable=False
    db.session.commit()
    return redirect(url_for('admin.PageBanner'))

@admin.route('/delete_banner/<banner_id>', methods=['GET','POST'])
def DeleteBanner(banner_id):
    is_deleted = BannerImage.query.filter_by(id=banner_id).delete()
    db.session.commit()
    return redirect(url_for('admin.PageBanner'))

@admin.route('/voucher', methods=['GET','POST'])
def MangeVoucher():
    form = AddVoucherForm()
    if form.validate_on_submit():
        new_voucher = Voucher(name=form.name.data,
                        code = form.code.data,
                        discount=form.discount.data,
                        expire_date=form.expire_date.data,
                        max_usage=form.max_usage.data)
        db.session.add(new_voucher)
        db.session.commit()
        flash('Added new voucher')
    vouchers = Voucher.query.all()
    return render_template('admin/manage_voucher.html',form = form,vouchers=vouchers)

@admin.route('/delete_voucher/<voucher_id>', methods=['GET','POST'])
def DeleteVoucher(voucher_id):
    is_deleted_voucher = Voucher.query.filter_by(id=voucher_id).delete()
    db.session.commit()
    flash("Deleted voucher")
    return redirect(url_for('admin.MangeVoucher'))

@admin.route('/mange_order', methods=['GET','POST'])
def ManageOrder():
    orders = Order.query.all()
    user_model = User.query
    address_model = Address.query
    return render_template('admin/manage_order.html',orders=orders,user_model=user_model,address_model=address_model)

@admin.route('/set_order_status_up/<ord_id>', methods=['GET','POST'])
def SetOrderUp(ord_id):
    order = Order.query.filter_by(id=ord_id).first()
    if(order.status=='Preparing'):
        order.status='Packaging'
    else:
        if(order.status=='Packaging'):
            order.status='Shipping'
        else:
            if(order.status=='Shipping'):
                order.status='Delievering'
            else:
                if(order.status=='Delievering'):
                    order.status='Done'
    db.session.commit()
    return redirect(url_for('admin.ManageOrder'))


@admin.route('/set_order_status_down/<ord_id>', methods=['GET','POST'])
def SetOrderDown(ord_id):
    order = Order.query.filter_by(id=ord_id).first()
    if(order.status=='Done'):
        order.status='Delievering'
    else:
        if(order.status=='Delievering'):
            order.status='Shipping'
        else:
            if(order.status=='Shipping'):
                order.status='Packaging'
            else:
                if(order.status=='Packaging'):
                    order.status='Preparing'
    db.session.commit()
    return redirect(url_for('admin.ManageOrder'))


@admin.route('/manage_revenue', methods=['GET','POST'])
def ManageRevenue():
    quarter = request.args.get('quarter')
    year = request.args.get('year')
    
    if(year and quarter):
        find_revenues = Revenue.query.filter_by(quarter=quarter,year=year).all()
        return render_template('admin/manage_revenue.html',all_revenues=find_revenues)
    if(year):
        find_revenues = Revenue.query.filter_by(year=year).all()
        return render_template('admin/manage_revenue.html',all_revenues=find_revenues)
    all_revenues = Revenue.query.all()
    return render_template('admin/manage_revenue.html',all_revenues=all_revenues)

@admin.route('/detail_revenue/<year>/<quarter>', methods=['GET','POST'])
def DetailRevenue(year,quarter):
    revenue = Revenue.query.filter_by(quarter=quarter,year=year).first()
    orders = Order.query.filter_by(revenue_id=revenue.id).all()
    user_model = User.query
    address_model = Address.query
    return render_template('admin/manage_revenue_detail.html',revenue=revenue, orders=orders,user_model=user_model,address_model=address_model)

@admin.route('/record_sale/<order_id>', methods=['GET','POST'])
def RecordSale(order_id):
    new_order = Order.query.filter_by(id=order_id).first()
     #Add to revenue

    order_date = new_order.create_date.strftime("%Y-%m-%d")
    order_month = datetime.datetime.strptime(order_date, "%Y-%m-%d").month 
    order_year = datetime.datetime.strptime(order_date, "%Y-%m-%d").year 
        
    print("Order Date", order_date)
    print("Order Month ",order_month)
    print("Order Year ", order_year)
    quater = 0
    if(order_month>0 and order_month<4):
        quater = 1
    if(order_month>3 and order_month<7):
        quater = 2
    if(order_month>6 and order_month<10):
        quater = 3
    if(order_month>9 and order_month<13):
        quater = 4
    
    print(quater)
    sale_revenue = Revenue.query.filter_by(quarter=quater,year=order_year).first()
    if( not sale_revenue ):
        new_sale = Revenue(
            total_sale=new_order.total,
            quarter=quater,
            year=order_year
        )
        db.session.add(new_sale)
        db.session.commit()
    else:
        new_order.revenue_id=sale_revenue.id
        new_order.status = 'Recorded'
        sale_revenue.total_sale += new_order.total
        db.session.commit()

    return redirect(url_for('admin.ManageOrder'))
    

# For Batch Data Adding
@admin.route('/add_role')
def AddRole():
    role = Role(
        name='Admin',
        permission=32
    )
    role_2 = Role(
        name='User',
        permission=1
    )
    role_3 = Role(
        name='Manager',
        permission=16
    )
    role_4 = Role(
        name='Sales Employee',
        permission=4
    )
    role_5 = Role(
        name='Warehouse Manager',
        permission=8
    )
    db.session.add_all([role,role_2,role_3,role_4,role_5])
    db.session.commit()
    return "added_role"

@admin.route('/add_category')
def AddCategory():
    shoe = Category(category_name='shoes')
    sneaker = Category(category_name='sneakers')
    boot = Category(category_name='boots')
    slipper = Category(category_name='slippers')
    accessory = Category(category_name='accessories')
    db.session.add_all([shoe,sneaker,boot,slipper,accessory])
    db.session.commit()
    flash("Added all category")
    return redirect(url_for('admin.index'))

@admin.route('/add_batch')
def AddBatch():
    datadir = "/Users/longvu/Projects/Moroexe_Flask/app/static/data"
    datas = []
    img_names = []
    with os.scandir(datadir) as folders:
        for folder in folders:
            if(folder.name!='.DS_Store'):
                #print("In Folder: "+folder.name)
                folderPath = (folder.path)
                for file in os.scandir(folderPath):
                    if( file!='.DS_Store' ):
                        #print(file)
                        if(file.name=='infor.JSON'):
                            with open(file, 'r') as fcc_file:
                                datas.append(json.load(fcc_file)) 


    # print (datas[1])
    
    for data in datas:
        category = Category.query.filter_by(category_name=(data['category'])).first()
        pd_name = (data['product_name'])
        pd_price = (data['price'])
        pd_desc = (data['desc'])
        img_1 = (data['product_img'])
        img_2 = (data['product_subimg1'])
        img_3 = (data['product_subimg2'])
        img_4 = (data['product_subimg3'])
        color = (data['color'])
        style = (data['style'])
        material = (data['material'])
        product = Product(product_name = pd_name,
                            price = pd_price,
                            desc = pd_desc,
                            product_img = img_1,
                            product_subimg1 = img_2,
                            product_subimg2 = img_3,
                            product_subimg3 = img_4,
                            categories=category,
                            color=color,
                            style=style,
                            material=material
                            )
        db.session.add(product)
        db.session.commit()
    flash("Added a bunch of data")
    return redirect(url_for('admin.index'))

@admin.route('/add_product_size')
def AddProductSize():
    all_shoe        = Product.query.filter_by(category_id=1).all()
    all_sneaker     = Product.query.filter_by(category_id=2).all()
    all_boots       = Product.query.filter_by(category_id=3).all()
    all_slipper     = Product.query.filter_by(category_id=4).all()
    all_accessory   = Product.query.filter_by(category_id=5).all()
    
    
    for shoe in all_shoe:
        for i in range(37,43):
            print(i)
            stock = StockAndSize(size=i,
                                stock=100,
                                product_id=shoe.id)
            db.session.add(stock)
            db.session.commit()
        print("Added size for ", shoe.product_name)
    
    for sneaker in all_sneaker:
        for i in range(37,43):
            print(i)
            stock = StockAndSize(size=i,
                                stock=100,
                                product_id=sneaker.id)
            db.session.add(stock)
            db.session.commit()
        print("Added size for ", sneaker.product_name)

    for boot in all_boots:
        for i in range(37,43):
            print(i)
            stock = StockAndSize(size=i,
                                stock=100,
                                product_id=boot.id)
            db.session.add(stock)
            db.session.commit()
        print("Added size for ", boot.product_name)

    for slipper in all_slipper:
        for i in range(37,43):
            print(i)
            stock = StockAndSize(size=i,
                                stock=100,
                                product_id=slipper.id)
            db.session.add(stock)
            db.session.commit()
        print("Added size for ", slipper.product_name)
    size = ["S", "M", "L"]
    for accs in all_accessory:
        for i in size:
            print(i)
            stock = StockAndSize(size=i,
                                stock=100,
                                product_id=accs.id)
            db.session.add(stock)
            db.session.commit()
        print("Added size for ", accs.product_name)
    
    flash("Added a bunch of size")
    return redirect(url_for('admin.index'))