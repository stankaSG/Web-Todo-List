from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.fields.simple import EmailField, PasswordField
from wtforms.validators import DataRequired, URL

class RegisterForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    username = StringField("User Name", validators=[DataRequired()])
    submit = SubmitField("SING ME UP!")


class LoginForm(FlaskForm):
    email = EmailField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("LOG IN!")

class ToDoForm(FlaskForm):
    title = StringField("Make New ToDo List", validators=[DataRequired()])
    save = SubmitField("Save it!")