from django.db import models

class Participant(models.Model):
    GENDER_CHOICES = [
        ('M', 'مرد'),
        ('F', 'زن'),
    ]

    HAND_CHOICES = [
        ('R', 'راست'),
        ('L', 'چپ'),
    ]
    phone = models.CharField("شماره موبایل", max_length=11)
    birth_date = models.DateField("تاریخ تولد")
    gender = models.CharField("جنسیت", max_length=1, choices=GENDER_CHOICES)
    hand = models.CharField("دست غالب", max_length=1, choices=HAND_CHOICES)
    disorder = models.TextField("سابقه بیماری", max_length=200)
    drug = models.TextField("سابقه مصرف دارو", max_length=100)
    created_at = models.DateTimeField("زمان ثبت", auto_now_add=True)

    def __str__(self):
        return f"{self.phone}"
    

