from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DateField, IntegerField, TimeField, PasswordField, RadioField, HiddenField
from wtforms.validators import InputRequired, NumberRange, EqualTo, Length, ValidationError



class EventForm(FlaskForm):
    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError("End date must be >= start date.")
    name = StringField("Name:", validators=[InputRequired(message="Name is required.")])
    description = StringField("Description:")
    start_date = DateField("Start date: ", validators=[InputRequired()])
    end_date = DateField("End date: ", validators=[InputRequired(),validate_end_date])
    start_time = TimeField("Start time:", validators=[InputRequired()])
    end_time = TimeField("End time:", validators=[InputRequired()])
    location = StringField("Location:")
    participants = StringField("Participants: ")
    repeats = IntegerField("Number of repeats: ", validators=[NumberRange(min=1,max=100)])
    repeat_frequency = IntegerField("Repeat frequency (days)", validators=[NumberRange(min=0,max=370)])
    id = HiddenField()
    submit = SubmitField("Create event")
   
    

class EditEventForm(FlaskForm):
    def validate_end_date(self, field):
        # function adapted from https://stackoverflow.com/questions/64952614/field-validations-to-compare-two-date-fields-in-flask-wtforms
        if field.data < self.start_date.data:
            raise ValidationError("End date must be >= start date.")
    name = StringField("Name:", validators=[InputRequired()])
    description = StringField("Description:")
    start_date = DateField("Start date: ", validators=[InputRequired()])
    end_date = DateField("End date: ", validators=[InputRequired(),validate_end_date])
    start_time = TimeField("Start time:", validators=[InputRequired()])
    end_time = TimeField("End time:", validators=[InputRequired()])
    location = StringField("Location:")
    participants = StringField("Participants: ")
    id = HiddenField()
    submit = SubmitField("Submit")

class RegistrationForm(FlaskForm):
    user_id = StringField("User id:", validators=[InputRequired(),Length(min=5)])
    password = PasswordField("Password:", validators=[InputRequired(), Length(min=5)])
    password2 = PasswordField("Repeat password:", validators=[InputRequired(),EqualTo("password")])
    submit = SubmitField("Submit")

class LoginForm(FlaskForm):
    user_id = StringField("User id:", validators=[InputRequired()])
    password = PasswordField("Password:", validators=[InputRequired()])
    submit = SubmitField("Submit")

class CalendarViewForm(FlaskForm):
    view_select = RadioField(choices=[("week","Week view"),("month","Month view")],default="week", validators=[InputRequired()])
    date_select = DateField("Please choose a start date:",validators=[InputRequired()])
    submit=SubmitField("Reload")