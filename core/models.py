from django.db import models

class Participant(models.Model):
    GENDER_CHOICES = [
        ('M', 'مرد'),
        ('F', 'زن'),
    ]

    name = models.CharField("نام", max_length=100)
    age = models.PositiveIntegerField("سن")
    gender = models.CharField("جنسیت", max_length=1, choices=GENDER_CHOICES)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.age} ساله"
