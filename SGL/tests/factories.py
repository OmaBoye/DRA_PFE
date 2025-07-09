# tests/factories.py
import factory
from factory import fuzzy
from datetime import datetime, timedelta
from django.utils import timezone
from analysis.models import Analysis, AnalysisType
from samples.models import Sample, SampleType
from patients.models import Patient
from users.models import User
import json


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.Sequence(lambda n: f"user_{n}@example.com")
    password = factory.PostGenerationMethodCall('set_password', 'password')
    is_active = True


class PatientFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Patient

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    date_of_birth = factory.Faker('date_of_birth', minimum_age=18, maximum_age=90)
    gender = fuzzy.FuzzyChoice(['M', 'F', 'O'])
    phone_number = factory.Faker('phone_number')


class SampleTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = SampleType

    name = factory.Sequence(lambda n: f"SampleType_{n}")
    description = factory.Faker('sentence')
    processing_days = fuzzy.FuzzyInteger(1, 5)


class SampleFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sample

    patient = factory.SubFactory(PatientFactory)
    collection_date = factory.LazyFunction(timezone.now)
    barcode = factory.Sequence(lambda n: f"SMP{n:08d}")
    current_technician = factory.SubFactory(UserFactory)

    @factory.post_generation
    def sample_type(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for st in extracted:
                self.sample_type.add(st)
        else:
            self.sample_type.add(SampleTypeFactory())


class AnalysisTypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AnalysisType

    name = factory.Sequence(lambda n: f"AnalysisType_{n}")
    code = factory.LazyAttribute(lambda o: f"TEST{o.id:03d}")
    category = fuzzy.FuzzyChoice(['blood', 'urine', 'tissue', 'molecular', 'microbiology'])
    description = factory.Faker('paragraph')
    turnaround_time = fuzzy.FuzzyInteger(1, 72)
    is_auto_verifiable = fuzzy.FuzzyChoice([True, False])
    is_blood_panel = fuzzy.FuzzyChoice([True, False])
    test_cost = fuzzy.FuzzyDecimal(10.0, 500.0)

    @factory.post_generation
    def sample_types(self, create, extracted, **kwargs):
        if not create:
            return

        if extracted:
            for st in extracted:
                self.sample_types.add(st)
        else:
            self.sample_types.add(SampleTypeFactory())


class AnalysisFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Analysis

    sample = factory.SubFactory(SampleFactory)
    analysis_type = factory.SubFactory(AnalysisTypeFactory)
    status = fuzzy.FuzzyChoice(['pending', 'in_progress', 'completed', 'verified'])
    priority = fuzzy.FuzzyChoice(['routine', 'urgent', 'stat'])
    created_by = factory.SubFactory(UserFactory)
    technician = factory.Faker('name')

    @factory.lazy_attribute
    def selected_panels(self):
        if self.analysis_type.is_blood_panel:
            return [panel[0] for panel in Analysis.BLOOD_PANELS[:2]]
        return []

    @factory.post_generation
    def timestamps(self, create, extracted, **kwargs):
        if not create:
            return

        now = timezone.now()
        if self.status in ['in_progress', 'completed', 'verified']:
            self.started_at = now - timedelta(hours=2)

        if self.status in ['completed', 'verified']:
            self.completed_at = now

        if self.status == 'verified':
            self.verified_at = now
            self.verified_by = factory.SubFactory(UserFactory)

    @factory.post_generation
    def qc_status(self, create, extracted, **kwargs):
        if not create:
            return

        if self.status in ['completed', 'verified']:
            self.qc_status = fuzzy.FuzzyChoice(['pass', 'fail', 'pending']).fuzz()