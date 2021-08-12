from enum import unique
from os import name

from flask import Flask, render_template, redirect, flash, request

from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.fields.core import DateField
from wtforms.fields.simple import TextField
from wtforms.validators import DataRequired, EqualTo, Length
from wtforms.widgets import TextArea

from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.datastructures import Authorization

#create Falsk Instance
app = Flask(__name__)

#create secret token csrf
app.config["SECRET_KEY"] = "my_secret"

#create connection to database
#Flask Tutorial - 3. Setting up Flask with SQLAlchemy & PostgreSQL / https://www.youtube.com/watch?v=PJK950Gp780
#Build & Deploy A Python Web App | Flask, Postgres & Heroku / https://www.youtube.com/watch?v=w25ea_I89iM
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' / "postgresql+psycopg2://<username>:<password>@<server>:5432/<db_name>"

ENV = 'dev'

if ENV == 'dev':
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db' 
else:
    app.config['SQLALCHEMY_DATABASE_URI'] ="postgresql://postgres:ManBitesDog1@localhost:5432/user"

#disable track modification
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

#init database
db = SQLAlchemy(app)
migrate = Migrate(app, db)

#create post class
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250))
    content = db.Column(db.Text)
    author = db.Column(db.String(255))
    date_post = db.Column(db.DateTime, default = datetime.utcnow)
    slug = db.Column(db.String(255))

#create db class
class User(db.Model):
    id= db.Column(db.Integer, primary_key = True)
    name= db.Column(db.String(20), nullable = False, index = True )
    email=db.Column(db.String(80), index=True, nullable = False, unique=True)
    special_power = db.Column(db.String(150))
    date_added=db.Column(db.DateTime, default = datetime.utcnow)
    password_hash=db.Column(db.String(256))

    @property
    def password(self):
        raise AttributeError('Error Password something went wrong')
    
    @password.setter
    def password(self, password):
        self.password_hash=generate_password_hash(password)
    
    def verify_password (self, password):
        return check_password_hash(self.password_hash, password)

#create Post Form
class PostForm(FlaskForm):
    title =StringField("Title", validators = [DataRequired()])
    author = StringField("Author", validators=[DataRequired()])
    content = StringField("Content", validators=[DataRequired()], widget=TextArea())
    slug = StringField("Slug", )
    submit_btn = SubmitField("Submit")

#create a class for user form
class UserForm(FlaskForm):
    name = StringField("Name", validators = [DataRequired()])
    email = StringField("Email", validators = [DataRequired()])
    special_power = StringField("Special Power")
    password_hash = PasswordField("Password", validators=[DataRequired(), EqualTo('password_hash2', message='Passwords Must Match')])
    password_hash2 = PasswordField("Confirm Password", validators = [DataRequired()])
    submit_btn = SubmitField("Submit")

#create class for forms
class NameForm(FlaskForm):
    name_input = StringField("What is your name", validators = [DataRequired()])
    submit_btn = SubmitField("Submit")

class PasswordForm(FlaskForm):
    email = StringField("Email", validators = [DataRequired()])
    password = PasswordField("Password", validators= [DataRequired()])
    submit_btn = SubmitField("Submit")

#create routes
@app.route("/")
def index():
    return render_template("index.html")

@app.route('/posts')
def posts():
    posts = Post.query.order_by(Post.date_post)
    return render_template("posts.html", posts=posts)

@app.route("/add-post", methods = ['GET', 'POST'])
def add_post():
    form = PostForm()

    if form.validate_on_submit():
        post = Post(title = form.title.data, author = form.author.data, content = form.content.data, slug = form.slug.data)
        form.title.data = ""
        form.author.data = ""
        form.content.data = ""
        form.slug.data = ""

        db.session.add(post)
        db.session.commit()
        flash("Post Was Submitted!!!")
    current_posts = Post.query.order_by(Post.date_post)
    return render_template("add_post.html", form = form, current_posts = current_posts)

@app.route("/login_pw", methods = ["GET", "POST"])
def login_pw():
    email = None
    password = None
    pw_to_check = None
    passed = None
    form = PasswordForm()

    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        #look up user in db 
        pw_to_check = User.query.filter_by(email = email).first()

        #check that password
        passed = check_password_hash(pw_to_check.password_hash, password)

        #clear the form
        form.email.data = ''
        form.password.data=''
    
    return render_template('login_pw.html', form=form, email=email, password=password, pw_to_check = pw_to_check, passed = passed)

@app.route("/delete/<int:id>")
def delete(id):
    user_delete = User.query.get_or_404(id)
    form = UserForm()
    name = None
    
    try:
        db.session.delete(user_delete)
        db.session.commit()
        
        current_users = User.query.order_by(User.date_added)
        return render_template('add_user.html', current_users = current_users, name=name, form=form)
    except: 
        flash( "Error go back")

@app.route("/update/<int:id>", methods = ['GET', 'POST'])
def update(id):
    form = UserForm()
    update_name = User.query.get_or_404(id)

    if request.method == 'POST':
        update_name.name = request.form['name']
        update_name.email = request.form['email']
        update_name.special_power = request.form['special_power']
        try:
            db.session.commit()
            flash('User Updated')
            return render_template('update.html', form=form, update_name=update_name)
        except:
            flash('Something went wrong, try again')
            return render_template('update.html', form=form, update_name=update_name)

    else:
        return render_template('update.html', form=form, update_name=update_name)

@app.route("/user/add", methods = ['GET', 'POST'])
def user_add():
    form = UserForm()
    name =None

    if form.validate_on_submit():
        user = User.query.filter_by(email = form.email.data).first()
        if user is None:
            hashed_pw = generate_password_hash(form.password_hash.data, "sha256")
            user = User(name = form.name.data, email = form.email.data, special_power = form.special_power.data, password_hash = hashed_pw)
            db.session.add(user)
            db.session.commit()
        else:
            flash("User already taken, Try Again")
        name = form.name.data
        form.name.data = ''
        form.email.data = ''
        form.special_power.data = ''
        form.password_hash.data =''
        flash(name+" user data added to the database!!!!!")
    current_users = User.query.order_by(User.date_added)
    return render_template('add_user.html', current_users = current_users, name=name, form=form)

@app.route("/user/<name>")
def user(name):
    return render_template("user.html", name = name)

@app.route("/form", methods = ["GET", "POST"])    
def form():
    flask_form = NameForm()
    name = None
    if flask_form.validate_on_submit():
        name = flask_form.name_input.data
        flask_form.name_input.data = ""
        flash("flash message works!!!!!")

    return render_template('form.html', flask_form = flask_form, name = name)

#handle invalid URL, look up server error codes
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

#handle internal server error, look up server error codes
@app.errorhandler(500)
def page_not_found(e):
    return render_template('500.html'), 500