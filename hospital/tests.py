from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from .models import DiagnosticTest, InvoiceItem, Patient, PatientInvoice


class DiagnosticBillingTests(TestCase):
    def setUp(self):
        admin_group, _ = Group.objects.get_or_create(name='ADMIN')
        patient_group, _ = Group.objects.get_or_create(name='PATIENT')
        self.admin = User.objects.create_user(username='billing-admin', password='test-pass')
        self.admin.groups.add(admin_group)
        self.patient_user = User.objects.create_user(username='patient-one', password='test-pass')
        self.patient_user.groups.add(patient_group)
        self.patient = Patient.objects.create(
            user=self.patient_user,
            address='Main road',
            mobile='01712345678',
            symptoms='Checkup',
            status=True,
        )
        self.test = DiagnosticTest.objects.create(
            name='Blood test',
            category='Laboratory',
            price=500,
        )

    def create_patient(self, username):
        user = User.objects.create_user(username=username, password='test-pass')
        return Patient.objects.create(
            user=user,
            address='Other road',
            mobile='01712345679',
            symptoms='Checkup',
            status=True,
        )

    def test_staff_invoice_uses_catalog_price_and_keeps_item_snapshot(self):
        self.client.force_login(self.admin)
        self.assertEqual(self.client.get(reverse('admin-billing')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin-billing-test')).status_code, 200)
        self.assertEqual(self.client.get(reverse('admin-create-invoice')).status_code, 200)
        self.assertContains(
            self.client.get(reverse('admin-create-invoice')),
            'Blood test — Laboratory — BDT 500',
        )
        response = self.client.post(reverse('admin-create-invoice'), {
            'patient': self.patient.pk,
            'tests': [self.test.pk],
            'quantity': 3,
        })

        self.assertRedirects(response, reverse('admin-billing'))
        invoice = PatientInvoice.objects.get()
        item = InvoiceItem.objects.get(invoice=invoice)
        self.assertEqual(invoice.total_amount, 1500)
        self.assertEqual(invoice.payment_status, 'Unpaid')
        self.assertEqual((item.test_name, item.unit_price, item.quantity), ('Blood test', 500, 3))

        self.test.name = 'Updated test name'
        self.test.price = 700
        self.test.save()
        item.refresh_from_db()
        self.assertEqual((item.test_name, item.unit_price), ('Blood test', 500))

    def test_staff_invoice_supports_multiple_tests(self):
        xray = DiagnosticTest.objects.create(
            name='Chest X-ray',
            category='Imaging',
            price=700,
        )
        self.client.force_login(self.admin)
        response = self.client.post(reverse('admin-create-invoice'), {
            'patient': self.patient.pk,
            'tests': [self.test.pk, xray.pk],
            'quantity': 2,
        })

        self.assertRedirects(response, reverse('admin-billing'))
        invoice = PatientInvoice.objects.get()
        self.assertEqual(invoice.total_amount, 2400)
        self.assertEqual(invoice.items.count(), 2)

    def test_patient_can_only_open_their_own_invoice(self):
        own_invoice = PatientInvoice.objects.create(patient=self.patient, total_amount=100)
        other_patient = self.create_patient('patient-two')
        other_invoice = PatientInvoice.objects.create(patient=other_patient, total_amount=200)
        self.client.force_login(self.patient_user)

        own_response = self.client.get(reverse('patient-invoice-detail', args=[own_invoice.pk]))
        other_response = self.client.get(reverse('patient-invoice-detail', args=[other_invoice.pk]))
        other_pdf_response = self.client.get(
            reverse('patient-invoice-download', args=[other_invoice.pk])
        )
        list_response = self.client.get(reverse('patient-bill'))

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(other_response.status_code, 404)
        self.assertEqual(other_pdf_response.status_code, 404)
        self.assertContains(list_response, f'#{own_invoice.pk}')
        self.assertNotContains(
            list_response,
            reverse('patient-invoice-detail', args=[other_invoice.pk]),
        )

    def test_patient_cannot_record_payment(self):
        invoice = PatientInvoice.objects.create(patient=self.patient, total_amount=100)
        self.client.force_login(self.patient_user)

        response = self.client.post(
            reverse('admin-record-invoice-payment', args=[invoice.pk]),
            {'payment_method': 'Cash'},
        )

        invoice.refresh_from_db()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(invoice.payment_status, 'Unpaid')

    def test_staff_can_record_confirmed_digital_payment(self):
        invoice = PatientInvoice.objects.create(patient=self.patient, total_amount=100)
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse('admin-record-invoice-payment', args=[invoice.pk]),
            {'payment_method': 'bKash', 'transaction_id': 'STAFF-CONFIRMED-123'},
        )

        self.assertRedirects(response, reverse('admin-billing'))
        invoice.refresh_from_db()
        self.assertEqual(invoice.payment_status, 'Paid')
        self.assertEqual(invoice.payment_method, 'bKash')
        self.assertEqual(invoice.transaction_id, 'STAFF-CONFIRMED-123')

    def test_patient_payment_request_stays_unpaid_and_pdf_is_downloadable(self):
        invoice = PatientInvoice.objects.create(patient=self.patient, total_amount=100)
        InvoiceItem.objects.create(
            invoice=invoice,
            test=self.test,
            test_name=self.test.name,
            unit_price=100,
            quantity=1,
        )
        self.client.force_login(self.patient_user)

        response = self.client.post(
            reverse('patient-request-invoice-payment', args=[invoice.pk]),
            {'payment_method': 'Nagad', 'transaction_id': 'PATIENT-SUBMITTED-123'},
        )
        invoice.refresh_from_db()
        pdf_response = self.client.get(
            reverse('patient-invoice-download', args=[invoice.pk])
        )

        self.assertRedirects(
            response,
            reverse('patient-invoice-detail', args=[invoice.pk]),
        )
        self.assertEqual(invoice.payment_status, 'Unpaid')
        self.assertEqual(invoice.payment_method, 'Nagad')
        self.assertEqual(invoice.transaction_id, 'PATIENT-SUBMITTED-123')
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response['Content-Type'], 'application/pdf')
        self.assertIn('attachment; filename="invoice-', pdf_response['Content-Disposition'])

    def test_demo_seed_adds_30_tests_without_overwriting_existing_prices(self):
        self.test.name = 'Complete Blood Count (CBC)'
        self.test.price = 777
        self.test.save()
        call_command('seed_diagnostic_tests', verbosity=0)
        first_count = DiagnosticTest.objects.count()
        call_command('seed_diagnostic_tests', verbosity=0)

        self.assertEqual(first_count, 30)
        self.assertEqual(DiagnosticTest.objects.count(), 30)
        self.test.refresh_from_db()
        self.assertEqual(self.test.price, 777)
