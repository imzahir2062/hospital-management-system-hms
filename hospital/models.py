from django.db import models
from django.contrib.auth.models import User



departments=[('Cardiologist','Cardiologist'),
('Dermatologists','Dermatologists'),
('Emergency Medicine Specialists','Emergency Medicine Specialists'),
('Allergists/Immunologists','Allergists/Immunologists'),
('Anesthesiologists','Anesthesiologists'),
('Colon and Rectal Surgeons','Colon and Rectal Surgeons')
]
class Doctor(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/DoctorProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    department= models.CharField(max_length=50,choices=departments,default='Cardiologist')
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return "{} ({})".format(self.user.first_name,self.department)



class Patient(models.Model):
    user=models.OneToOneField(User,on_delete=models.CASCADE)
    profile_pic= models.ImageField(upload_to='profile_pic/PatientProfilePic/',null=True,blank=True)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=False)
    symptoms = models.CharField(max_length=100,null=False)
    assignedDoctorId = models.PositiveIntegerField(null=True)
    admitDate=models.DateField(auto_now=True)
    status=models.BooleanField(default=False)
    @property
    def get_name(self):
        return self.user.first_name+" "+self.user.last_name
    @property
    def get_id(self):
        return self.user.id
    def __str__(self):
        return self.user.first_name+" ("+self.symptoms+")"


class Appointment(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    doctorId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40,null=True)
    doctorName=models.CharField(max_length=40,null=True)
    appointmentDate=models.DateField(auto_now=True)
    description=models.TextField(max_length=500)
    status=models.BooleanField(default=False)



class PatientDischargeDetails(models.Model):
    patientId=models.PositiveIntegerField(null=True)
    patientName=models.CharField(max_length=40)
    assignedDoctorName=models.CharField(max_length=40)
    address = models.CharField(max_length=40)
    mobile = models.CharField(max_length=20,null=True)
    symptoms = models.CharField(max_length=100,null=True)

    admitDate=models.DateField(null=False)
    releaseDate=models.DateField(null=False)
    daySpent=models.PositiveIntegerField(null=False)

    roomCharge=models.PositiveIntegerField(null=False)
    medicineCost=models.PositiveIntegerField(null=False)
    doctorFee=models.PositiveIntegerField(null=False)
    OtherCharge=models.PositiveIntegerField(null=False)
    total=models.PositiveIntegerField(null=False)


# hospital/models.py
from django.db import models
from .models import Patient

class BillingRecord(models.Model):
    PAYMENT_METHODS = (
        ('Cash', 'Cash'),
        ('bKash', 'bKash'),
        ('Nagad', 'Nagad'),
    )
    
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    test_fees = models.PositiveIntegerField(default=0)
    doctor_fee = models.PositiveIntegerField(default=0)
    medicine_fee = models.PositiveIntegerField(default=0)
    total_amount = models.PositiveIntegerField()
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    transaction_id = models.CharField(max_length=100, blank=True, null=True) # ক্যাশ হলে ফাকা থাকবে
    billing_date = models.DateTimeField(auto_now_add=True)
    collected_by = models.CharField(max_length=100, default='Billing Clerk') # কে বিল তুললো

    def __str__(self):
        return f"Bill for {self.patient} - Total: ৳{self.total_amount} ({self.payment_method})"    
class DiagnosticTest(models.Model):
    name = models.CharField(max_length=120, unique=True)
    category = models.CharField(max_length=80)
    price = models.PositiveIntegerField(help_text="Price in BDT")
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.price} BDT"


class PatientInvoice(models.Model):
    PAYMENT_METHODS = [
        ('Cash', 'Cash'),
        ('bKash', 'bKash'),
        ('Nagad', 'Nagad'),
        ('Upay', 'Upay'),
    ]

    PAYMENT_STATUSES = [
        ('Unpaid', 'Unpaid'),
        ('Paid', 'Paid'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    created_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    total_amount = models.PositiveIntegerField(default=0)
    payment_method = models.CharField(
        max_length=10,
        choices=PAYMENT_METHODS,
        blank=True
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PAYMENT_STATUSES,
        default='Unpaid'
    )
    transaction_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Invoice #{self.id} - {self.patient}"


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(
        PatientInvoice,
        related_name='items',
        on_delete=models.CASCADE
    )
    test = models.ForeignKey(
        DiagnosticTest,
        null=True,
        blank=True,
        on_delete=models.SET_NULL
    )
    test_name = models.CharField(max_length=120)
    unit_price = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.test_name} × {self.quantity}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity