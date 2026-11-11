from flask_wtf import FlaskForm
from wtforms import IntegerField, StringField, SubmitField
from wtforms.validators import DataRequired, InputRequired, Length, NumberRange, ValidationError

MAX_BEDS = 1000


class _CountsMixin:
    """Shared validation: open beds can't be more than the total."""

    def validate_available(self, field):
        if self.total.data is not None and field.data is not None and field.data > self.total.data:
            raise ValidationError("Open beds can't be more than the total.")


class BedTypeForm(_CountsMixin, FlaskForm):
    label = StringField("Bed group", validators=[DataRequired(), Length(max=80)])
    total = IntegerField("Total beds", validators=[
        InputRequired(message="Enter a number."), NumberRange(min=0, max=MAX_BEDS)])
    available = IntegerField("Open now", validators=[
        InputRequired(message="Enter a number."), NumberRange(min=0, max=MAX_BEDS)])
    submit = SubmitField("Add bed group")


class BedCountsForm(_CountsMixin, FlaskForm):
    total = IntegerField("Total", validators=[
        InputRequired(message="Enter a number."), NumberRange(min=0, max=MAX_BEDS)])
    available = IntegerField("Open", validators=[
        InputRequired(message="Enter a number."), NumberRange(min=0, max=MAX_BEDS)])
    submit = SubmitField("Save")
