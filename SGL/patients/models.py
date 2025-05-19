from django.db import models
from django.core.validators import RegexValidator
from core.models import BaseModel
import qrcode
from io import BytesIO
from django.core.files import File
from auditlog.registry import auditlog
from auditlog.models import AuditlogHistoryField


class Patient(BaseModel):
    history = AuditlogHistoryField()  # Add this line

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+999999999'."
    )
    phone_number = models.CharField(validators=[phone_regex], max_length=17)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    qr_code = models.ImageField(upload_to='qr_codes', blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    def save(self, *args, **kwargs):
        # Generate QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(f"PatientID:{self.id}")
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffer = BytesIO()
        img.save(buffer, format="PNG")

        self.qr_code.save(f'qr_{self.id}.png', File(buffer), save=False)

        super().save(*args, **kwargs)


auditlog.register(Patient)