from django.contrib import admin
from .models import (
    Doctor,
    Patient,
    Appointment,
    PatientDischargeDetails,
    DiagnosticTest,
    PatientInvoice,
    InvoiceItem,
)

class DoctorAdmin(admin.ModelAdmin):
    pass

admin.site.register(Doctor, DoctorAdmin)


class PatientAdmin(admin.ModelAdmin):
    pass

admin.site.register(Patient, PatientAdmin)


class AppointmentAdmin(admin.ModelAdmin):
    pass

admin.site.register(Appointment, AppointmentAdmin)


class PatientDischargeDetailsAdmin(admin.ModelAdmin):
    pass

admin.site.register(PatientDischargeDetails, PatientDischargeDetailsAdmin)

admin.site.register(DiagnosticTest)
admin.site.register(PatientInvoice)
admin.site.register(InvoiceItem)