from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField, BooleanField, SelectField, ValidationError
from wtforms.validators import DataRequired, Length, Regexp, Email
from flask_pagedown.fields import PageDownField
from ..models import User, Role


class NameForm(FlaskForm):
    name = StringField('What is your name?', validators=[DataRequired()])
    submit = SubmitField('Submit')


class EditProfileForm(FlaskForm):
    """Form for profile editing by user"""
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField()


class EditProfileAdminForm(FlaskForm):
    """Form for profile editing by admin"""
    username = StringField('Username', validators=[DataRequired(), Regexp('^[A-Za-z][A-Za-z_.]*$'), Length(1, 64)])
    email = StringField('Email', validators=[DataRequired(), Length(1, 64), Email()])
    confirmed = BooleanField('Confirmed')
    role = SelectField('Role', coerce=int)
    name = StringField('Real name', validators=[Length(0, 64)])
    location = StringField('Location', validators=[Length(0, 64)])
    about_me = TextAreaField('About me')
    submit = SubmitField('Submit')

    def __init__(self, user, *args, **kwargs):
        super(EditProfileAdminForm, self).__init__(*args, **kwargs)

        # Setup choices for the 'role' field
        self.role.choices = [(role.id, role.name)
                             for role in Role.query.order_by(Role.name).all()]
        self.user = user

    def validate_email(self, field):
        if field.data != self.user.email and User.query.filter_by(email=field.data).first():
            raise ValidationError('Email already registered.')

    def validate_username(self, field):
        if field.data != self.user.username and User.query.filter_by(username=field.data).first():
            raise ValidationError('Username already in use')


class PostForm(FlaskForm):
    """Simple post form"""
    body = PageDownField('What\'s in your mind?', validators=[DataRequired()])
    submit = SubmitField()


class CommentForm(FlaskForm):
    """Simple comment form"""
    body = StringField('', validators=[DataRequired()])
    submit = SubmitField('Submit')
