from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Optional, Length


class DescriptionForm(FlaskForm):
    description = TextAreaField('Description', validators=[Optional(), Length(0, 300)])
    submit = SubmitField()


class TagForm(FlaskForm):
    tag = StringField('Add tag (use space to separate)', validators=[Optional(), Length(0, 64)])
    submit = SubmitField()
