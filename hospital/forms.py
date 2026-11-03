from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
import re
from . import models

# Bangladeshi phone number validation function
def check_bd_phone(value):
    local_pattern = r'^01[3-9]\d{8}$'
    if not re.match(local_pattern, value):
        raise ValidationError('Doya kore sothik Bangladeshi mobile number din (jemon: 01712345678)')

#for admin signup
class AdminSigupForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }


#for doctor related form
class DoctorUserForm(forms.ModelForm):
    class Meta:
        model=User
        fields=['first_name','last_name','username','password']
        widgets = {
        'password': forms.PasswordInput()
        }
class DoctorForm(forms.ModelForm):
    mobile = forms.CharField(
        max_length=11, 
        validators=[check_bd_phone],
        widget=forms.TextInput(attrs={'placeholder': '01XXXXXXXXX'})
    )
    class Meta:
        model=models.Doctor
        fields=['address','mobile','department','status','profile_pic']



#for patient related form
class PatientUserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'username', 'password']
        widgets = {
            'password': forms.PasswordInput()
        }

class PatientForm(forms.ModelForm):
    mobile = forms.CharField(
        max_length=11, 
        validators=[check_bd_phone],
        widget=forms.TextInput(attrs={'placeholder': '01XXXXXXXXX'})
    )
    class Meta:
        model = models.Patient
        # Doctor selection ebong file upload bad deya holo, jate patient-ra kono hassle chara easily sign up krte pare
        fields = ['address', 'mobile', 'symptoms']
        fields = ['address', 'mobile', 'symptoms']
class AdminPatientForm(forms.ModelForm):
    assignedDoctorId = forms.ModelChoiceField(
        queryset=models.Doctor.objects.filter(status=True),
        to_field_name='user_id',
        required=False,
        empty_label='Select a doctor'
    )

    def clean_assignedDoctorId(self):
        doctor = self.cleaned_data.get('assignedDoctorId')
        return doctor.user_id if doctor else None

    class Meta:
        model = models.Patient
        fields = [
            'address',
            'mobile',
            'symptoms',
            'assignedDoctorId',
            'profile_pic',
        ]

class AppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Doctor Name and Department", to_field_name="user_id")
    patientId=forms.ModelChoiceField(queryset=models.Patient.objects.all().filter(status=True),empty_label="Patient Name and Symptoms", to_field_name="user_id")
    class Meta:
        model=models.Appointment
        fields=['description','status']


class PatientAppointmentForm(forms.ModelForm):
    doctorId=forms.ModelChoiceField(queryset=models.Doctor.objects.all().filter(status=True),empty_label="Doctor Name and Department", to_field_name="user_id")
    class Meta:
        model=models.Appointment
        fields=['description','status']


#for contact us page
class ContactusForm(forms.Form):
    Name = forms.CharField(max_length=30)
    Email = forms.EmailField()
    Message = forms.CharField(max_length=500,widget=forms.Textarea(attrs={'rows': 3, 'cols': 30}))


class DiagnosticTestForm(forms.ModelForm):
    class Meta:
        model = models.DiagnosticTest
        fields = ['name', 'category', 'price', 'is_active']
        widgets = {
            'price': forms.NumberInput(attrs={'min': 1}),
        }

    def clean_price(self):
        price = self.cleaned_data['price']
        if price <= 0:
            raise ValidationError('Price must be greater than zero.')
        return price


class InvoiceCreationForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=models.Patient.objects.all())
    tests = forms.ModelMultipleChoiceField(
        queryset=models.DiagnosticTest.objects.filter(is_active=True),
        widget=forms.CheckboxSelectMultiple,
        help_text='Select one or more tests. Quantity applies to each selected test.',
    )
    quantity = forms.IntegerField(min_value=1, max_value=100)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['tests'].label_from_instance = lambda test: (
            '{} — {} — BDT {}'.format(
                test.name, test.category, test.price
            )
        )


class InvoicePaymentForm(forms.Form):
    payment_method = forms.ChoiceField(choices=models.PatientInvoice.PAYMENT_METHODS)
    transaction_id = forms.CharField(max_length=100, required=False)

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        transaction_id = cleaned_data.get('transaction_id', '').strip()
        if payment_method != 'Cash' and not transaction_id:
            self.add_error('transaction_id', 'Enter the transaction reference confirmed by staff.')
        cleaned_data['transaction_id'] = transaction_id
        return cleaned_data