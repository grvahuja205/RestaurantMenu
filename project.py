from flask import Flask, render_template, request, url_for, redirect, flash, jsonify, g
from sqlalchemy import create_engine, and_, or_
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Restaurant, MenuItem, User, AuthUser
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField
from wtforms.validators import DataRequired, InputRequired, EqualTo
from flask_wtf.file import FileField, FileRequired, FileAllowed
from passlib.hash import sha256_crypt
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from datetime import timedelta
from flask_httpauth import HTTPTokenAuth, MultiAuth
from itsdangerous import (JSONWebSignatureSerializer as Serializer, BadSignature, SignatureExpired)
import os
from werkzeug.datastructures import CombinedMultiDict
from werkzeug.utils import secure_filename

engine = create_engine("mysql://root:root@localhost/RESTAURANTMENU")
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()

UPLOAD_FOLDER = '/home/gaurav/project/RestaurantMenu/static'
#ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])

#auser = AuthUser()

app = Flask(__name__)

#app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['REMEMBER_COOKIE_DURATION'] = timedelta(hours = 8)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

token_auth = HTTPTokenAuth()
#multi_auth = MultiAuth(login_manager, token_auth)


@login_manager.user_loader
def load_user(user_id):
    return session.query(User).filter_by(id = int(user_id)).one()

@token_auth.verify_token
def verify_token(api_key):
	api_key = request.args.get('api_key')
	if api_key == '' or api_key == None:
		if current_user.is_authenticated:
			return True
		else:
			return False
	else:
		s = Serializer('SECRET_KEY')
		try:
			data = s.loads(api_key)
		except BadSignature:
			return False
		email_t = data['email']
		auser = session.query(AuthUser).filter_by(email = email_t).count()
		if auser == 1:
			return True
		else:
			return False


@app.route('/')
@app.route('/restaurants')
def ShowRestaurants():
	output = ""

	rest_a = session.query(Restaurant).all()
	
	return render_template('main.html', restaurant = rest_a)

@app.route('/restaurant/<int:restaurant_id>/')
def DisplayRestaurantMenu(restaurant_id):
	output = ""

	rest = session.query(Restaurant).filter_by(id = restaurant_id).one()

	menu = session.query(MenuItem).filter_by(restaurant_id = rest.id).all()

	return render_template('menu.html', restaurant = rest, items = menu)

@app.route('/restaurant/JSON')
#@login_required
@token_auth.login_required
def restaurantJSON():
	allrest = session.query(Restaurant).all()
	return jsonify(Restaurant=[rest.serialize for rest in allrest])

@app.route('/restaurant/<int:restaurant_id>/JSON')
@token_auth.login_required
#@multi_auth.login_required
def restaurantMenuJSON(restaurant_id):
	restid = session.query(Restaurant).filter_by(id = restaurant_id).one()
	items = session.query(MenuItem).filter_by(restaurant_id = restaurant_id).all()
	return jsonify(MenuItems=[i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/JSON')
#@multi_auth.login_required
#@login_required
@token_auth.login_required
def restaurantMenuItmeJSON(restaurant_id, menu_id):
	#restid = session.query(Restaurant).filter_by(id = restaurant_id).one()
	item = session.query(MenuItem).filter_by(id = menu_id).one()
	print item.name
	#item = session.query(MenuItem).filter_by(id = items.id)
	return jsonify(MenuItem=item.serialize)

# Task 0: Create route for New restaurant
@app.route('/restaurant/new')
def newRestaurant():
    return "page to create a new restaurant. Task 0 complete!"

# Task 1: Create route for newMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/new', methods = ['GET', 'POST'])
@login_required
def newMenuItem(restaurant_id):
	#return "Item Page"

	currrest = session.query(Restaurant).filter_by(id =restaurant_id).one()

	mform = AddNewMenuItem(request.form)

	if currrest.owner_id == current_user.id:
		if request.method == 'POST' and mform.validate():
			newn = request.form['mname']
			newd = request.form['mdesc']
			newp = request.form['mprice']
			newt = request.form['mtype']
			newi = MenuItem(name = newn, description = newd, price = newp, course = newt, restaurant = currrest)
			session.add(newi)
			session.commit()
			return redirect(url_for('DisplayRestaurantMenu', restaurant_id = restaurant_id))
		else:
			return render_template('newMenuItem.html', restaurant_name = currrest.name, restaurant_id = currrest.id, form = mform)

	else:
		flash(u"Unauthorized Access", "error")
		return redirect(url_for("DisplayRestaurantMenu", restaurant_id = restaurant_id))
		#return render_template('newMenuItem.html',restaurant_name = curr_rest.name, restaurant_id = restaurant_id)
    #return "page to create a new menu item. Task 1 complete!"

# Task 2: Create route for editMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/edit', methods = ['GET', 'POST'])
@login_required
def editMenuItem(restaurant_id, menu_id):

	eform = EditMenuItem(request.form)

	ed_curr_rest = session.query(Restaurant).filter_by(id =restaurant_id).one()
	rmenu = session.query(MenuItem).filter_by(id = menu_id).one()

	if ed_curr_rest.owner_id == current_user.id: 
		if request.method == 'POST' and eform.validate():
			updateItem = session.query(MenuItem).filter_by(id = menu_id).one()
			if request.form['ename'] != '':
				updateItem.name = request.form['ename']
			if request.form['edesc'] != '':
				updateItem.description = request.form['edesc']
			if request.form['eprice'] != '':
				updateItem.price = request.form['eprice']
			if request.form['ecourse'] != '':
				updateItem.course = request.form['ecourse']
			session.add(updateItem)
			session.commit()
			flash('Item Edited')
			return redirect(url_for('DisplayRestaurantMenu', restaurant_id = restaurant_id))
		else:
			return render_template('editMenuItem.html', item_name = rmenu.name, menu_id = rmenu.id, restaurant_id = restaurant_id, form = eform)
	else:
		flash(u"Not Uthorized",'error')
		return redirect(url_for('DisplayRestaurantMenu', restaurant_id = restaurant_id))
    #return "page to edit a menu item. Task 2 complete!"

# Task 3: Create a route for deleteMenuItem function here
@app.route('/restaurant/<int:restaurant_id>/<int:menu_id>/delete', methods = ['GET', 'POST'])
@login_required
def deleteMenuItem(restaurant_id, menu_id):
	deletItem = session.query(MenuItem).filter_by(id = menu_id).one()
	del_curr_rest = session.query(Restaurant).filter_by(id = restaurant_id).one()

	if del_curr_rest.owner_id == current_user.id:
		if request.method == 'POST':
			session.delete(deletItem)
			session.commit()
			flash("Menu Item Deleted")
			return redirect(url_for('DisplayRestaurantMenu', restaurant_id = restaurant_id))
		else:
			return render_template('deleteMenuItem.html', itemName = deletItem.name, restaurant_id = restaurant_id, menu_id = deletItem.id)
	else:
		flash(u"Unauthorized Access",'error')
		return redirect(url_for('DisplayRestaurantMenu', restaurant_id = restaurant_id))	
    #return "page to delete a menu item. Task 3 complete!"

class RegisterForm(FlaskForm):
	name = StringField('Name', validators = [DataRequired(),InputRequired(message= " No Data Was Provided")])
	email = StringField('Email', validators = [DataRequired(),InputRequired(message= " No Data Was Provided")])
	password = PasswordField('Password', validators = [DataRequired(),InputRequired(message= " No Data Was Provided"),EqualTo('confirm', message = 'Password Must Match')])
	confirm = PasswordField('Repeat password')

class LoginForm(FlaskForm):
	uname = StringField('Username', validators = [DataRequired(),InputRequired(message= " No Data Was Provided")])
	password_login = PasswordField('Password', validators = [DataRequired(),InputRequired(message= " No Data Was Provided")])

class AddRestaurant(FlaskForm):
	rname = StringField('Restaurant Name', validators = [DataRequired(),InputRequired(message= " No Data Was Provided")])
	img_file = FileField('Image For Restaurant',validators=[FileRequired(),FileAllowed(['png', 'jpg', 'jpeg', 'gif'])])

class AddNewMenuItem(FlaskForm):
	mname = StringField('Menu item Name', validators = [InputRequired(message = "No Data Was Provided")])
	mdesc = StringField('Menu Item Description')
	mprice = StringField('Menu Item Price Like $2.45')
	mtype = StringField("Type Of Course")

class GetToken(FlaskForm):
	tname = StringField('Name', validators = [InputRequired(message = "No Name Was Provided")])
	email = StringField('Email', validators = [InputRequired(message = "No Email Was Provides")])

class EditMenuItem(FlaskForm):
	ename = StringField('Edit Menu Item Name')
	eprice = StringField('New Price')
	edesc = StringField('New Description')
	ecourse = StringField('New Course')

@app.route('/login', methods = ['GET','POST'])
def login():
	lform = LoginForm(request.form)
	if request.method == 'POST' and lform.validate():
		name = request.form['uname']
		password = request.form['password_login']
		record = session.query(User).filter_by(email = name).one()

		if sha256_crypt.verify(password, record.password):
			flash("You Are Logged In")
			#print 'User Passed'
			login_user(record)
			return redirect(url_for('dash', user_id = record.id))
		else:
			flash(u"Invalid Username And Password",'error')
			redirect(url_for('login'))
	else:
		return render_template('login.html', form = lform)



@app.route('/register', methods = ['GET','POST'])
def register():
	uform = RegisterForm(request.form)
	if request.method == 'POST' and uform.validate():
		name = request.form['name']
		email = request.form['email']
		password = sha256_crypt.encrypt(str(request.form['password']))
		us = session.query(User).filter_by(email = email).count()
		if  us != 0:
			flash(u"Email Already Registered",'error')
			return redirect(url_for('register'))
		else:
			newUser = User(name = name, email = email, password = password)
			session.add(newUser)
			session.commit()
			flash("User User ID Created With Username As Your Email")
			flash('Login To Continue')
			return redirect(url_for('login'))
	else:
		#flash('Login To Continue')
		return render_template('register.html',form = uform)


@app.route('/dashboard/<int:user_id>',methods = ['GET', 'POST'])
@login_required
def dash(user_id):
	rform = AddRestaurant(CombinedMultiDict((request.files, request.form)))
	cuser = session.query(User).filter_by(id = user_id).one()
	if request.method == 'POST' and rform.validate():
		rrname = request.form['rname']
		file_u = request.files['img_file']
		print file_u
		filename = secure_filename(file_u.filename)
		filename = rrname+filename
		print filename
		file_u.save(os.path.join(UPLOAD_FOLDER, filename))
		new_res = Restaurant(name = rrname, user = cuser, image = filename)
		session.add(new_res)
		session.commit()
		nres = session.query(Restaurant).filter_by(name = rrname).one()
		return redirect(url_for('DisplayRestaurantMenu', restaurant_id = nres.id))
	else:
		return render_template('dashboard.html', name = current_user.name, user_id = current_user.id, form = rform)

@app.route('/logout')
@login_required
def logout():
	logout_user()
	return redirect(url_for('login')) 

@app.route('/restaurants/api', methods = ['GET', 'POST'])
def getApi():
	tform = GetToken(request.form)

	if request.method == 'POST' and tform.validate():
		name = request.form['tname']
		email = request.form['email']
		q = session.query(AuthUser).filter_by(email = email)
		c = q.count()
		if c == 1:
			d = q.one()
			flash(u"Email Already Exixts",'error')
			return render_template('api.html', token = d.token.decode('ascii'))
		else:
			au = AuthUser(name = name, email = email)
			session.add(au)
			session.commit()
			tk = au.generate_auth_token()
			v = session.query(AuthUser).filter_by(email = email).one()
			v.token = tk
			session.add(v)
			session.commit()
			return render_template('api.html', token = tk.decode('ascii'))
	else:
		return render_template("getapi.html", tform = tform)

if __name__ == '__main__':
	app.secret_key = 'super_secret_key'
	app.debug = True
	app.run(host = '0.0.0.0', port = 5000)