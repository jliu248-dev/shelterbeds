from flask_wtf import FlaskForm
from wtforms import BooleanField, PasswordField, RadioField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length

from app.models import Role


class RegisterForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=255)])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=8, max=128)])
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
    )
    # Only these two roles can be chosen; "admin" is rejected by the validator.
    role = RadioField(
        "I am a...",
        choices=[
            (Role.SEEKER, "Person looking for a bed"),
            (Role.SHELTER_STAFF, "Shelter staff (needs admin approval)"),
        ],
        default=Role.SEEKER,
        validators=[DataRequired()],
    )
    submit = SubmitField("Create account")


class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember = BooleanField("Remember me")
    submit = SubmitField("Log in")
