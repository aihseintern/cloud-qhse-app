# guide_bot/forms.py
from flask_wtf import FlaskForm
from wtforms import StringField, FileField, MultipleFileField, SelectMultipleField, SubmitField
from wtforms.validators import DataRequired

from app.models import Permission

class DocumentForm(FlaskForm):
    files = MultipleFileField('Files', validators=[DataRequired()])
    permission_id = SelectMultipleField('Permission', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Upload')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_id.choices = [(permission.id, permission.name) for permission in Permission.query.all()]

class NewFolderForm(FlaskForm):
    folder_name = StringField('Folder Name', validators=[DataRequired()])
    permission_id = SelectMultipleField('Permission', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_id.choices = [(permission.id, permission.name) for permission in Permission.query.all()]

class EditFileForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    allowed_roles = SelectMultipleField('Allowed Roles', choices=[
        ('IT', 'IT'),
        ('HR', 'HR'),
        ('Finance', 'Finance'),
        ('Accounting', 'Accounting'),
        ('Security', 'Security')
    ])