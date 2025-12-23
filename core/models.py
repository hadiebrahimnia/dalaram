from django.db import models
from django.contrib.auth.models import AbstractUser

class CustomUser(AbstractUser):
    username = models.CharField(
        "شماره موبایل",
        max_length=11,
        unique=True,
        help_text="شماره موبایل کاربر (۱۱ رقمی)",
    )

    GENDER_CHOICES = [
        ('M', 'مرد'),
        ('F', 'زن'),
    ]

    HAND_CHOICES = [
        ('R', 'راست'),
        ('L', 'چپ'),
    ]
    birth_date = models.DateField("تاریخ تولد", null=True)
    gender = models.CharField("جنسیت", max_length=1, choices=GENDER_CHOICES)
    hand = models.CharField("دست غالب", max_length=1, choices=HAND_CHOICES)
    disorder = models.TextField("سابقه بیماری", max_length=200, blank=True)
    drug = models.TextField("سابقه مصرف دارو", max_length=100, blank=True)

    def __str__(self):
        return self.username
    
# پرسشنامه
class Questionnaire(models.Model):
    
    title = models.CharField(max_length=200, verbose_name="عنوان پرسشنامه")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    def __str__(self):
        return self.title
# ویژگی
class Attribute(models.Model):
    title = models.CharField(max_length=200, verbose_name="ویژگی")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان ایجاد")
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    def __str__(self):
        return self.title
# سوالات
class Question(models.Model):
    QUESTION_TYPES = [
        ('MC', 'چندگزینه‌ای'),
        ('TX', 'متن آزاد'),
        ('SC', 'مقیاس (مثل لیکرت)'),
    ]
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='questions')
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='ویژگی')
    text = models.TextField(verbose_name="متن سؤال")
    question_type = models.CharField(max_length=2, choices=QUESTION_TYPES, verbose_name="نوع سؤال")
    order = models.PositiveIntegerField(default=1, verbose_name="ترتیب نمایش")
    required = models.BooleanField(default=True, verbose_name="اجباری")

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"{self.text[:50]}..."
# گزینه ها
class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='choices')
    text = models.CharField(max_length=200, verbose_name="متن گزینه")
    value = models.IntegerField(default=0, verbose_name="ارزش عددی (برای امتیازدهی)")

    def __str__(self):
        return self.text
# آزمون
class Response(models.Model):
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, related_name='responses')
    respondent = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="پاسخ‌دهنده")  # اگر کاربر لاگین باشد
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تکمیل")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")

    def __str__(self):
        return f"پاسخ به {self.questionnaire.title} توسط {self.respondent or 'ناشناس'}"
# جواب
class Answer(models.Model):
    response = models.ForeignKey(Response, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)  # برای چندگزینه‌ای
    text_answer = models.TextField(blank=True, verbose_name="پاسخ متنی")  # برای متن آزاد
    scale_value = models.IntegerField(null=True, blank=True, verbose_name="ارزش مقیاس")  # برای لیکرت
    RT = models.PositiveIntegerField(null=True, blank=True, verbose_name="زمان پاسخ‌دهی (ثانیه)")
    
    def __str__(self):
        return f"جواب به {self.question.text[:20]}..."
    

class Result(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="کاربر")
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, verbose_name="آزمون")
    response = models.ForeignKey(Response, on_delete=models.CASCADE, verbose_name="Response")
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name="Attribute")
    raw_score = models.FloatField(verbose_name="نمره خام", default=0.0)  # جمع جواب‌های مربوط به ویژگی
    num_questions = models.IntegerField(verbose_name="تعداد سوالات مربوط به ویژگی", default=0)
    average_score = models.FloatField(verbose_name="میانگین نمره", default=0.0)
    sum_rt = models.PositiveIntegerField(verbose_name="جمع RT", default=0)
    average_rt = models.FloatField(verbose_name="میانگین RT", default=0.0)

    class Meta:
        unique_together = ('response', 'attribute')  # هر نتیجه منحصر به فرد برای هر response و attribute

    def __str__(self):
        return f"نتیجه {self.attribute.title} برای {self.user.username} در {self.questionnaire.title}"