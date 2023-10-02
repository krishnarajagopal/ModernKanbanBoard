import json, os
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, url_for, flash,jsonify
from flask_login import LoginManager,UserMixin,login_user,login_required,logout_user,current_user
from flask_bootstrap import Bootstrap5
from faker import Faker
from faker.providers import DynamicProvider,BaseProvider
from flask_wtf import FlaskForm
from wtforms import DecimalField,FloatField
from wtforms.fields import TimeField, URLField, StringField, SubmitField,SelectField,DateField,IntegerRangeField,IntegerField,TextAreaField,DateField,EmailField,PasswordField
from wtforms.validators import DataRequired, URL, NoneOf, NumberRange,Regexp
from wtforms_validators import AlphaSpace
import sqlite3
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

# from flask_modals import render_template_modal
# from flask_modals import Modal

# '''
# Red underlines? Install the required packages first: 
# Open the Terminal in PyCharm (bottom left). 

# On Windows type:
# python -m pip install -r requirements.txt

# On MacOS type:
# pip3 install -r requirements.txt

# This will install the packages from requirements.txt for this project.
# '''
db = SQLAlchemy()
app = Flask(__name__)
# app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///new_defects_collection.db"
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DB_URI", "sqlite:///new_defects_collection.db")
app.config['SECRET_KEY'] = os.environ.get('FLASK_KEY')
csrf = CSRFProtect(app)
db.init_app(app)
bootstrap = Bootstrap5(app)
print(f"SECTRET KEY: {app.config['SECRET_KEY']}")
#initialize login manager and configure it
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'alert-danger'

#Create User_Loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    description = db.Column(db.String(250), unique=False, nullable=False)
    name_assignee = db.Column(db.String(50), unique=False, nullable=False)
    status = db.Column(db.String(50), unique=False, nullable=False)
    due_date=db.Column(db.Date, unique=False, nullable=False)
    percent_complete = db.Column(db.Integer, nullable=False)

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(250), unique=True, nullable=False)
    password = db.Column(db.String(250), unique=False, nullable=False)
    email = db.Column(db.String(250), unique=True, nullable=False)
    def serialize(self):
        return {
            'id': self.id,
            'username': self.username,
            'password': self.password,
            'email': self.email,
            # Include other attributes as needed
        }
    def is_active(self):
        return True
    def is_authenticated(self):
        return True
    def get_id(self):
        return str(self.id)
    

faker_status=DynamicProvider(
    provider_name="task_status",
    elements=["TO DO", "IN PROGRESS", "REVIEW", "COMPLETE"],
)

fake=Faker(locale='en_US')
fake.add_provider(faker_status)
Faker.seed(0)

# ##Use this to create a DICTIONARY of Dictionaries of Fake data
# tasks = {}
# for i in range(0, 3):
#     tasks[i]={}
#     tasks[i]['id'] = i+1
#     tasks[i]['title'] = fake.sentence(nb_words=3)
#     tasks[i]['description'] = fake.paragraph(nb_sentences=1)
#     tasks[i]['name_assignee'] = fake.name()
#     tasks[i]['status'] = fake.task_status()
#     tasks[i]['due_date'] = fake.date_this_month(before_today=False, after_today=True)
#     tasks[i]['percent_complete'] = fake.random_int(min= 0, max= 100, step= 1)
# print(tasks)

##Use this to create a LIST of Dictionaries of Fake data
task = {}
tasks=[]
for i in range(0, 30):
    task['id'] = i+1
    task['title'] = fake.sentence(nb_words=3)
    task['description'] = fake.paragraph(nb_sentences=5)
    task['name_assignee'] = fake.name()
    task['status'] = fake.task_status()
    task['due_date'] = fake.date_this_month(before_today=False, after_today=True)
    task['percent_complete'] = fake.random_int(min= 0, max= 100, step= 1)
    tasks.append(task.copy())
#     print(task)
# print(tasks)

#use this to create a LIST of Dictionaries of Fake user data
user = {}
users=[]
for i in range(0, 10):
    user['id'] = i+1
    user['username'] = fake.name()
    user['email'] = fake.email()
    user['password'] = fake.password()
    users.append(user.copy())
# print(users)

##Create Table
with app.app_context():
    db.create_all()


#Insert Initial Fake Rows:

with app.app_context():
    record_exists = db.session.query(db.session.query(Task).filter_by(id=1).exists()).scalar()
    user_exists = db.session.query(db.session.query(User).filter_by(id=1).exists()).scalar()
    if not record_exists:
        for task_item in tasks:
            add_new_task_to_db = Task(**task_item)
            db.session.add(add_new_task_to_db)
            db.session.commit()

    if not user_exists:
        for user_item in users:
            add_new_user_to_db = User(**user_item)
            db.session.add(add_new_user_to_db)
            db.session.commit()


class update_task_form(FlaskForm):
    id = IntegerField(label='Task ID', validators=[DataRequired()], render_kw={'readonly': True})
    title = StringField(label='Title')
    description = TextAreaField (label='Description',  validators=[DataRequired()])
    name_assignee=StringField (label='Name Assignee', validators=[DataRequired(),AlphaSpace()])
    status=SelectField (label='Status', choices=["TO DO", "IN PROGRESS", "REVIEW", "COMPLETE"],coerce=str,validate_choice=True,validators=[DataRequired()])
    due_date=DateField (label='Due Date', validators=[DataRequired(message="Valid due Date required")])
    percent_complete = IntegerField (label="Percent Complete",validators=[DataRequired(),NumberRange(min=0,max=100,message="Enter a number between 0 and 100")])
    submit = SubmitField(label='Update Task')

class register_form(FlaskForm):
    firstname = StringField(label='FirstName', validators=[DataRequired()])
    lastname = StringField(label='LastName', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    email=EmailField(label='Email', validators=[DataRequired()])
    submit = SubmitField(label='Register')

class login_form(FlaskForm):
    email=EmailField(label='Email', validators=[DataRequired()])
    password = PasswordField(label='Password', validators=[DataRequired()])
    submit = SubmitField(label='Login')


# class Delete_task_form(FlaskForm):
#     id = IntegerField(label='Task ID', validators=[DataRequired()], render_kw={'readonly': True})
#     title = StringField(label='Title')
#     submit = SubmitField(label='Delete Task')



@app.route('/', methods=['GET'])
def home():
    form=update_task_form()
    all_tasks=Task.query.all()
    all_users=User.query.all()
    #    print(all_tasks)
    # # print(all_users) and all_tasks in json format
    # tasks_data=[task.serialize() for task in all_tasks]
    # users_data=[user.serialize() for user in all_users]
    # print(json.dumps(users_data,indent=4))
    # print ( f"tasks_json:  {json.dumps(tasks_data,indent=4)}")
    return render_template('index.html',tasks=list(all_tasks),form=form,login_form=login_form(),register_form=register_form())

@app.route('/', methods=['POST'])
@login_required
def update_task():
    form=update_task_form()
    if  request.method=='POST' and form.validate_on_submit():
        task_id=request.form.get('id')
        task_to_edit = db.get_or_404(Task, task_id)
        print(f'Task ID to DB: {task_id}')
        # print(f'Task ID from DB: {db_result_to_update}')
        # print(f"Title:{form.title.data}, Description:{form.description.data}, Name_Assignee:{form.name_assignee.data},Status:{form.status.data},due_date:{form.due_date.data},percent_complete:{form.percent_complete.data}")
        task_to_edit.title = form.title.data
        task_to_edit.description = form.description.data 
        task_to_edit.name_assignee = form.name_assignee.data
        task_to_edit.status = form.status.data
        task_to_edit.due_date = form.due_date.data
        task_to_edit.percent_complete = form.percent_complete.data
        db.session.commit()
        # return jsonify(status='ok')
        # all_tasks=get_tasks() 
        flash(f"Task Details for : { task_to_edit.title} updated successfully",category="alert-success")
        return redirect(url_for("home"))
    else:
       return redirect(url_for("home"))
        # data = json.dumps(form.errors, ensure_ascii=False)
        # return jsonify(data)

@app.route('/postmethod', methods = ['POST'])
@login_required
def post_status_update_data():
    jsdata = request.get_json(force=True,)
    print (f"\nID: {jsdata['id']},\nStatus: {jsdata['status']}")
    id = jsdata['id']
    task_to_edit = db.get_or_404(Task, id)
    task_to_edit.status = jsdata['status']
    db.session.commit()
    flash(f"Status for Task Title ' {task_to_edit.title} ': updated successfully to '{ task_to_edit.status}' ",category="alert-success")
    return jsonify({'status':'success'})
    
@app.route("/add", methods=[ "POST"])
@login_required
def add():
    """
    Add a new task to the database.
    This function is triggered when a POST request is made to the "/add" endpoint of the API.
    It retrieves the title, description, name assignee, status, due date, and percent complete
    from the request form, and then adds a new task object to the database using the SQLAlchemy ORM.

    Parameters:
    None

    Returns:
    None
    """
    form=update_task_form()
    if request.method == "POST":
        # print(f"\
        # title = {form.title.data}\
        # description = {form.description.data} \
        # name_assignee = {form.name_assignee.data}\
        # status = {form.status.data}\
        # due_date = {form.due_date.data}\
        # percent_complete = {form.percent_complete.data}\
        # percent_complete = {request.form['percent_complete']}")
        new_task=Task(
        title = form.title.data,
        description = form.description.data, 
        name_assignee = form.name_assignee.data,
        status = form.status.data,
        due_date = form.due_date.data,
        percent_complete = form.percent_complete.data,)
        db.session.add(new_task)
        db.session.commit()
        flash(message=f"Book Name : {new_task.title} Added successfully", category="alert-success")
        return redirect(url_for('home'))

@app.route("/delete", methods=["POST"])
@login_required
def delete():
    """
    Delete a task from the database.

    This function is triggered when a POST request is made to the "/delete" endpoint of the API.
    It retrieves the ID of the task to be deleted from the request form, and then retrieves the task
    object from the database using the ID. The task object is then deleted from the database using
    the SQLAlchemy ORM. Finally, a flash message is displayed to indicate the successful deletion
    of the task, and the user is redirected to the home page.

    Parameters:
    None

    Returns:
    None
    """

    # if  request.method=='POST' :
    task_id=request.form.get('id')
    task_to_delete = db.get_or_404(Task, task_id)
    # print(f'Method: {request.method}\nTask ID to be deleted in DB: {task_id}\nTask retreived from DB: {task_to_delete.id}')
    db.session.delete(task_to_delete)
    db.session.commit()
    flash(message= f"Book Name : {task_to_delete.title} Deleted successfully",category="alert-danger")
    return redirect(url_for('home'))

# A register route for the API
@app.route("/register", methods=["POST"])
def register():
    """
    Registers a new user in the database.

    This function is triggered when a POST request is made to the "/register" endpoint of the API.
    It retrieves the form data from the request form, and then creates a new user object with the
    form data. The user object is then added to the database using the SQLAlchemy ORM. Finally, a
    flash message is displayed to indicate the successful creation of the user, and the user is
    redirected to the login page.

    Parameters:
    None

    Returns:
    None
    """
    form=register_form()
    if request.method == "POST":
        firstname = str(form.firstname.data)
        lastname = str(form.lastname.data)
        new_user=User(
        username = f"{firstname.capitalize()} {lastname.capitalize()}",
        password = generate_password_hash(password=form.password.data, method='pbkdf2:sha256', salt_length=16),
        email = form.email.data,)
        # user_json = new_user.serialize()
        # print(json.dumps(user_json, indent=4))
        db.session.add(new_user)
        db.session.commit()
        flash(message= f"User Name : {new_user.username} Created successfully",category="alert-success")
        return redirect(url_for('home'))

# A login route for the API
@app.route("/login", methods=["GET","POST"])
def login():
    """
    Login function for handling user authentication.
    
    Parameters:
    - None
    
    Returns:
    - None
    
    Description:
    This function is responsible for handling the user login process. It receives a POST request with the user's email and password, and checks if the provided credentials are correct. If the credentials are correct, the user is redirected to the home page. If the credentials are incorrect, appropriate error messages are flashed and the user is redirected to the home page.
    """   
    form=login_form()
    if request.method == "GET" and not current_user.is_authenticated:

        return redirect(url_for('home',user_logged_in=False))
    elif request.method == "POST":
        email=str(form.email.data)
        password=str(form.password.data)
        user=User.query.filter_by(email=email).first()
        if user:
            if check_password_hash(user.password, password):
                flash(message= f"User Name : {user.username} Logged in successfully",category="alert-success")
                login_user(user,remember=True)
                return redirect(url_for('home'))
            else:
                flash(message= f"User Name : {user.username} Password Incorrect",category="alert-danger")
                return redirect(url_for('home'))
        else:
            flash(message= f"User Name : {email} Email Incorrect",category="alert-danger")
            return redirect(url_for('home'))

# A logout route for the API
@app.route("/logout", methods=["POST"])
@login_required
def logout():
    current_user_name=current_user.username
    logout_user()
    flash(message= f"User Name : {current_user_name} Logged out successfully",category="alert-success")
    return redirect(url_for('home'))

if __name__ == "__main__":
    app.run(debug=False)
