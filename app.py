from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap5
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import Integer, String, Boolean
from flask_login import UserMixin, login_user, LoginManager, current_user, logout_user
from forms import LoginForm, RegisterForm, ToDoForm
from werkzeug.security import generate_password_hash, check_password_hash
import os
from dotenv import load_dotenv


load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ["SECRETKEY"]

database_url = os.getenv('JAWSDB_URL')
if not database_url:
    raise ValueError("JAWSDB_URL is not set in environment variables!")
app.config['SQLALCHEMY_DATABASE_URI'] = database_url.replace("mysql://", "postgresql://")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
Bootstrap5(app)


# Configure Flask-Login's Login Manager
login_manager = LoginManager()
login_manager.init_app(app)

# CREATE DATABASE
class Base(DeclarativeBase):
    pass


# app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///todo.db"

# Create the extension
db = SQLAlchemy(model_class=Base)
# Initialise the app with extension
db.init_app(app)

# Create a user_loader callback
@login_manager.user_loader
def load_user(user_id):
    return db.get_or_404(User, user_id)

# User Model
class User(db.Model, UserMixin):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(100), nullable=False)
    username: Mapped[str] = mapped_column(String(100), nullable=False)

    # Relationship with TodoList
    todo_lists = relationship("TodoList", back_populates="user")

class TodoList(db.Model):
    __tablename__ = "todo_lists"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(100), nullable=False)
    user_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Relationship with Task
    tasks = relationship('Task', back_populates='todo_list')
    # Back-populates with User
    user = relationship("User", back_populates="todo_lists")


# Task TABLE Configuration
class Task(db.Model):
    __tablename__ = "tasks"
    id: Mapped[int] = mapped_column(db.Integer, primary_key=True)
    title: Mapped[str] = mapped_column(db.String(200), nullable=False)
    done: Mapped[bool] = mapped_column(db.Boolean, default=False)
    todo_list_id: Mapped[int] = mapped_column(db.Integer, db.ForeignKey('todo_lists.id'), nullable=False)

    todo_list = relationship("TodoList", back_populates="tasks")

with app.app_context():
    db.create_all()


@app.route('/', methods=["GET", 'POST'])
def home():
    list_form = ToDoForm()
    todo_lists = (TodoList.query.all())
    # Add new todolist
    if list_form.validate_on_submit():
        list_title = list_form.title.data

        todo_list = db.session.execute(db.select(TodoList).where(TodoList.title == list_title)).scalar()
        if not todo_list:
            new_list = TodoList(
                title=list_title,
                user_id=current_user.id
            )
            db.session.add(new_list)
            db.session.commit()

            return redirect(url_for("home"))
        # List already exists
        else:
            flash("You already have this list!")
            return redirect(url_for('home'))
    return render_template('index.html',logged_in=current_user.is_authenticated,
                           todo_lists=todo_lists, list_form=list_form)

@app.route('/list/<int:todo_list_id>')
def open_list(todo_list_id):
    todo_lists = TodoList.query.all()
    tasks = Task.query.filter_by(todo_list_id=todo_list_id).all()
    list_form = ToDoForm()
    todo_list = db.session.execute(db.select(TodoList).where(TodoList.id == todo_list_id)).scalar()

    return render_template('index.html', logged_in=current_user.is_authenticated,
                           todo_lists=todo_lists, tasks=tasks,todo_list=todo_list, todo_list_id=todo_list_id, list_form=list_form)

@app.route('/add/<int:todo_list_id>', methods=['POST'])
def add_task(todo_list_id):
    task_title = request.form.get('title')
    if task_title and todo_list_id:
        new_task = Task(title=task_title, todo_list_id=int(todo_list_id))
        db.session.add(new_task)
        db.session.commit()
    return redirect(url_for('open_list', todo_list_id=todo_list_id))

@app.route('/done/<int:task_id>/<int:todo_list_id>')
def done_task(task_id, todo_list_id):
    task = Task.query.get(task_id)
    task.done = not task.done
    db.session.commit()
    return redirect(url_for('open_list', todo_list_id=todo_list_id))

@app.route('/delete/<int:task_id>/<int:todo_list_id>')
def delete_task(task_id, todo_list_id):
    task = Task.query.get(task_id)
    db.session.delete(task)
    db.session.commit()
    return redirect(url_for('open_list', todo_list_id=todo_list_id))

@app.route('/delete_list/<int:todo_list_id>')
def delete_todo_list(todo_list_id):
    todo_list = db.session.execute(db.select(TodoList).where(TodoList.id == todo_list_id)).scalar()
    if todo_list:
        Task.query.filter_by(todo_list_id=todo_list_id).delete()

        db.session.delete(todo_list)
        db.session.commit()
    return redirect(url_for('home'))

@app.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data
        # Find user by email entered.
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()

        if not user:
            flash("Email doesn't exist. try again")
            return redirect(url_for('login'))

        # Check stored password hash against entered password hashed
        elif check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for("home"))
        else:
            flash("Incorrect Password")
            return redirect(url_for('login'))
    return render_template("login.html", form=form, logged_in=current_user.is_authenticated)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        email = form.email.data
        username = form.username.data
        hash_and_salted_pass = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8)
        user = db.session.execute(db.select(User).where(User.email == email)).scalar()
        if not user:
            new_user = User(
                email=email,
                username=username,
                password=hash_and_salted_pass
            )
            db.session.add(new_user)
            db.session.commit()

            return redirect(url_for("home"))
        # User already exists
        else:
            flash("You've already singed up with this email, log in instead !")
            return redirect(url_for('login'))

    return render_template("register.html", form=form, logged_in=current_user.is_authenticated)

if __name__ == "__main__":
    # Get the PORT from environment variable, default to 5000 if not set
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)