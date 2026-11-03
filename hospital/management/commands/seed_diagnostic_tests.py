from django.core.management.base import BaseCommand

from hospital.models import DiagnosticTest


DEMO_TESTS = [
    ('Complete Blood Count (CBC)', 'Hematology', 500),
    ('ESR', 'Hematology', 250),
    ('Blood Grouping and Rh Typing', 'Hematology', 300),
    ('Fasting Blood Glucose', 'Biochemistry', 200),
    ('Random Blood Glucose', 'Biochemistry', 200),
    ('2-Hour Postprandial Blood Glucose', 'Biochemistry', 200),
    ('HbA1c', 'Biochemistry', 900),
    ('Lipid Profile', 'Biochemistry', 1000),
    ('Liver Function Test (LFT)', 'Biochemistry', 1200),
    ('Renal Function Test (RFT)', 'Biochemistry', 1000),
    ('Serum Creatinine', 'Biochemistry', 400),
    ('Blood Urea', 'Biochemistry', 400),
    ('Serum Electrolytes', 'Biochemistry', 800),
    ('Serum Uric Acid', 'Biochemistry', 400),
    ('Serum Calcium', 'Biochemistry', 500),
    ('Serum Bilirubin', 'Biochemistry', 400),
    ('Thyroid Profile (TSH)', 'Hormone', 700),
    ('Free T4 (FT4)', 'Hormone', 700),
    ('Urine R/E', 'Clinical Pathology', 300),
    ('Urine C/S', 'Microbiology', 800),
    ('Stool R/E', 'Clinical Pathology', 300),
    ('Pregnancy Test (Urine)', 'Immunology', 300),
    ('Hepatitis B Surface Antigen (HBsAg)', 'Immunology', 600),
    ('Anti-HCV', 'Immunology', 700),
    ('Dengue NS1 Antigen', 'Immunology', 700),
    ('Dengue IgG and IgM', 'Immunology', 800),
    ('Widal Test', 'Microbiology', 500),
    ('Chest X-ray (P/A View)', 'Imaging', 600),
    ('Ultrasonography (Whole Abdomen)', 'Imaging', 1500),
    ('Electrocardiogram (ECG)', 'Cardiology', 500),
]


class Command(BaseCommand):
    help = (
        'Add 30 clearly labeled demo diagnostic test estimates. '
        'Existing test records and prices are not changed.'
    )

    def handle(self, *args, **options):
        created_count = 0
        existing_count = 0
        for name, category, price in DEMO_TESTS:
            _, created = DiagnosticTest.objects.get_or_create(
                name=name,
                defaults={
                    'category': category,
                    'price': price,
                    'is_active': True,
                },
            )
            if created:
                created_count += 1
            else:
                existing_count += 1

        self.stdout.write(self.style.SUCCESS(
            'Diagnostic catalog seeded: {} added, {} already existed. '
            'All seeded prices are DEMO estimates; verify and edit before use.'
            .format(created_count, existing_count)
        ))
