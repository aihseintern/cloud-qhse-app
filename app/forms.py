# app/forms.py
from flask_login import current_user
from flask_wtf import FlaskForm
from flask import session
from wtforms import BooleanField, IntegerField, SelectMultipleField, StringField, SubmitField, SelectField, TextAreaField, PasswordField, FileField, widgets
from wtforms.validators import DataRequired, IPAddress, Length, URL, EqualTo, ValidationError
from app.models import CCTV, Contact, Detector, MessageTemplate, Permission, User, DetectorType, Weight, CCTVLocation
from app.extensions import db
from utils.auth import get_allowed_permission_ids

class AddCCTVForm(FlaskForm):
    location = StringField('Location', validators=[DataRequired()], 
                           render_kw={"placeholder": "Location tidak boleh duplicate"})    
    type = SelectField('Type', choices=[('Cabin', 'Cabin'), ('Entrance', 'Entrance'), ('Exit', 'Exit'), ('Working Area', 'Working Area')], coerce=str)
    ip_address = StringField('IP Address', validators=[URL(allow_ip=True)])        
    submit = SubmitField('Add CCTV')

class EditCCTVForm(FlaskForm):
    location = StringField('Location', validators=[DataRequired()])    
    type = SelectField('Type', choices=[('Cabin', 'Cabin'), ('Entrance', 'Entrance'), ('Exit', 'Exit'), ('Working Area', 'Working Area')], coerce=str)
    ip_address = StringField('IP Address', validators=[URL()])    
    status = SelectField('Status', choices=[('0', 'Inactive'), ('1', 'Active')], coerce=int)
    submit = SubmitField('Edit CCTV')

class CCTVForm(FlaskForm):
    location_id = SelectField('Location', coerce=int, validators=[DataRequired()])
    location_name = StringField('Location Name', default=None)
    type = StringField('Type')
    ip_address = StringField('IP Address', validators=[DataRequired()])    
    status = SelectField('Status', choices=[('0', 'Inactive'), ('1', 'Active')], coerce=int, default=1)
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.location_id.choices = [(location.id, location.name) for location in CCTVLocation.query.all()]

class SelectCCTVForm(FlaskForm):
    cctv = SelectField('Select CCTV', coerce=int, validators=[DataRequired()])
    submit = SubmitField('View Feed')

class DetectorForm(FlaskForm):
    id = IntegerField('ID')
    cctv_id = SelectField('CCTV', coerce=int, validators=[DataRequired()])    
    weight_id = SelectField('Weight', coerce=int, validators=[DataRequired()])
    running = BooleanField('Running', default=False)
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cctv_id.choices = [(cctv.id, f"{cctv.cctv_location.name} - {cctv.type}") for cctv in CCTV.query.filter(CCTV.permission_id == session.get('permission_id')).all()]
        self.weight_id.choices = [(weight.id, weight.name) for weight in Weight.query.filter(Weight.permission_id == session.get('permission_id')).all()]
        

class ModelForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    detector_type_id = SelectField('Detector Type', coerce=int, validators=[DataRequired()])
    detector_type_name = StringField('Detector Type Name', default=None)
    file = FileField('File')
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detector_type_id.choices = [(detector_type.id, detector_type.name) for detector_type in DetectorType.query.all()]

class ContactForm(FlaskForm):
    phone_number = StringField('Phone', validators=[Length(max=64)])
    name = StringField('Name', validators=[Length(max=30)])
    description = TextAreaField('Description', validators=[Length(max=100)])
    submit = SubmitField('Save')

class MessageTemplateForm(FlaskForm):
    name = StringField('Name', validators=[Length(max=30)])
    template = TextAreaField('Template', validators=[Length(max=4096)])

class NotificationRuleForm(FlaskForm):
    detector_id = SelectField('Detector', coerce=int, validators=[DataRequired()])
    contact_id = SelectField('Contact', coerce=int, validators=[DataRequired()])
    message_template_id = SelectField('Message Template', coerce=int, validators=[DataRequired()])
    
    submit = SubmitField('Save')

    def __init__(self, session_role=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.detector_id.choices = [(detector.id, detector.id) for detector in Detector.query.filter(Detector.permission_id == session.get('permission_id')).all()]
        self.contact_id.choices = [(contact.id, contact.name) for contact in Contact.query.filter(Contact.permission_id == session.get('permission_id')).all()]
        self.message_template_id.choices = [(template.id, template.name) for template in MessageTemplate.query.filter(MessageTemplate.permission_id == session.get('permission_id')).all()]

class MenuForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    url = StringField('URL')
    file = FileField('Image')
    permission_id = SelectField('Permission', coerce=int, validators=[DataRequired()])    
    permission_name = StringField('Permission Name', default=None)
    permission_description = TextAreaField('Permission Description', default=None, validators=[Length(max=100)])
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.permission_id.choices = [(permission.id, permission.name) for permission in Permission.query.all()]        

    def validate_on_submit(self, extra_validators=None) :
        return super().validate_on_submit(extra_validators)

class OTPForm(FlaskForm):
    otp_code = PasswordField('OTP Code', validators=[DataRequired()])
    submit = SubmitField('Verify')

class LoginForm(FlaskForm):
    nik = StringField('NIK', validators=[DataRequired(), Length(min=10, max=10)])
    submit = SubmitField('Send OTP')

class RegistrationForm(FlaskForm):
    nik = StringField('NIK', validators=[DataRequired(), Length(min=10, max=10)])
    name = StringField('Name', validators=[DataRequired(), Length(min=2, max=64)])
    email = StringField('Email', validators=[DataRequired(), Length(min=8, max=64)])
    phone = StringField('Phone Number', validators=[DataRequired(), Length(min=8, max=64)])    
    role = SelectField('Role', choices=[            
        ('user', 'user'),
        ('guest', 'guest'),      
    ], validators=[DataRequired()])
    submit = SubmitField('Register')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered.')
    
    def validate_phone(self, phone):
        user = User.query.filter_by(phone_number=phone.data).first()
        if user:
            raise ValidationError('Phone number already registered.')
             

    def validate_name(self, name):
        user = User.query.filter_by(name=name.data).first()
        if user:
            raise ValidationError('Username already taken.')

        
class AccessForm(FlaskForm):
    # This will create checkboxes for all permissions dynamically
    permissions = SelectMultipleField(
        'Permissions',
        coerce=int,  # We use `int` because the permission ID is an integer
        option_widget=widgets.CheckboxInput(),  # Use checkboxes
        widget=widgets.ListWidget(prefix_label=False),  # Arrange them in a list
        # validators=[DataRequired()]  # Ensure the form gets at least one permission selected
    )

    def __init__(self, *args, **kwargs):
        super(AccessForm, self).__init__(*args, **kwargs)
        # Dynamically fetch permissions from the database
        self.permissions.choices = [(perm.id, perm.name) for perm in Permission.query.all()]

class UserApprovalForm(FlaskForm):
    user_id = SelectField('User', coerce=str, validators=[DataRequired()])
    approved = BooleanField('Approved', default=None)
    approve = SubmitField('Approve') 
    reject = SubmitField('Reject')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id.choices = [(user.id, user.name) for user in User.query.filter_by(approved=None).all()]

class UserPermissionForm(FlaskForm):
    user_id = SelectField('User', coerce=str, validators=[DataRequired()])
    permission_id = SelectMultipleField('Permissions', coerce=int, option_widget=widgets.CheckboxInput(), widget=widgets.ListWidget(prefix_label=False))
    submit = SubmitField('Save')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user_id.choices = [(user.id, user.name) for user in User.query.all()]
        self.permission_id.choices = [(perm.id, perm.name) for perm in Permission.query.all()]
        
class ForgotForm(FlaskForm):
    nik = StringField('NIK', validators=[DataRequired(), Length(min=16, max=16)])
    submit = SubmitField('Submit')
    
class ResetPasswordForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Length(min=8, max=64)])
    otp = PasswordField('OTP', validators=[DataRequired(), Length(min=6, max=6)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=8, max=128)])
    password2 = PasswordField('Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Submit')