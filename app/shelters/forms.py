from flask_wtf import FlaskForm
from flask_wtf.file import FileAllowed, FileField
from wtforms import BooleanField, RadioField, StringField, SubmitField, TextAreaField
from wtforms.validators import URL, DataRequired, Length, Optional, ValidationError


class ReviewForm(FlaskForm):
    rating = RadioField(
        "Rating",
        choices=[("5", "5"), ("4", "4"), ("3", "3"), ("2", "2"), ("1", "1")],
        validators=[DataRequired(message="Pick a star rating.")],
    )
    body = TextAreaField(
        "Your review",
        validators=[DataRequired(), Length(min=10, max=2000)],
        render_kw={"rows": 4, "placeholder": "How was your stay? Staff, safety, cleanliness, check-in..."},
    )
    submit = SubmitField("Post review")


class ShelterEditForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=150)])
    operator = StringField("Run by", validators=[Optional(), Length(max=150)])
    address = StringField("Street address", validators=[DataRequired(), Length(max=255)])
    city = StringField("City", validators=[DataRequired(), Length(max=80)])
    zip_code = StringField("ZIP", validators=[Optional(), Length(max=10)])
    serves = StringField("Who it serves", validators=[Optional(), Length(max=150)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=4000)],
                                render_kw={"rows": 5})
    website = StringField("Website", validators=[Optional(), URL(require_tld=True), Length(max=255)])
    photo = FileField("Photo (JPG, PNG or WebP, max 5 MB)",
                      validators=[FileAllowed(["jpg", "jpeg", "png", "webp"], "Images only.")])
    remove_photo = BooleanField("Remove current photo")
    submit = SubmitField("Save changes")

    def validate_website(self, field):
        # Block javascript: and other non-web links.
        if field.data and not field.data.lower().startswith(("http://", "https://")):
            raise ValidationError("Website must start with http:// or https://")
