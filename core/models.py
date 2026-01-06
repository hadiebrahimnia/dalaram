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
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, related_name='questions')  # اصلاح: related_name correct شد (قبلاً 'ویژگی' اشتباه بود)
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
    respondent = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name="پاسخ‌دهنده"
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان شروع")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تکمیل")
    is_completed = models.BooleanField(default=False, verbose_name="تکمیل شده")

    def __str__(self):
        return f"پاسخ به {self.questionnaire.title} توسط {self.respondent or 'ناشناس'}"


# جواب
class Answer(models.Model):
    response = models.ForeignKey(
        Response,
        on_delete=models.CASCADE,  # مهم: با حذف Response، تمام Answerها حذف شوند
        related_name='answers'
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice = models.ForeignKey(Choice, on_delete=models.SET_NULL, null=True, blank=True)
    text_answer = models.TextField(blank=True, verbose_name="پاسخ متنی")
    scale_value = models.IntegerField(null=True, blank=True, verbose_name="ارزش مقیاس")
    RT = models.PositiveIntegerField(null=True, blank=True, verbose_name="زمان پاسخ‌دهی (ثانیه)")

    def __str__(self):
        return f"جواب به {self.question.text[:20]}..."


# نتیجه
class Result(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, verbose_name="کاربر")
    questionnaire = models.ForeignKey(Questionnaire, on_delete=models.CASCADE, verbose_name="آزمون")
    response = models.ForeignKey(
        Response,
        on_delete=models.CASCADE,  # مهم: با حذف Response، تمام Resultهای مرتبط هم حذف شوند
        related_name='results',
        verbose_name="Response"
    )
    attribute = models.ForeignKey(Attribute, on_delete=models.CASCADE, verbose_name="Attribute")
    raw_score = models.FloatField(verbose_name="نمره خام", default=0.0)
    num_questions = models.IntegerField(verbose_name="تعداد سوالات مربوط به ویژگی", default=0)
    average_score = models.FloatField(verbose_name="میانگین نمره", default=0.0)
    sum_rt = models.PositiveIntegerField(verbose_name="جمع RT", default=0)
    average_rt = models.FloatField(verbose_name="میانگین RT", default=0.0)

    class Meta:
        unique_together = ('response', 'attribute')
        constraints = [
            models.UniqueConstraint(fields=['response', 'attribute'], name='unique_response_attribute')
        ]

    def __str__(self):
        return f"نتیجه {self.attribute.title} برای {self.user.username} در {self.questionnaire.title}"
    

class RatingResponse(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )
    stimulus = models.CharField(
        max_length=50,
        verbose_name="محرک"
    )

    # نمره خوشایندی (Valence) - از 1 تا 9
    valence = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="خوشایندی (Valence)"
    )
    valence_rt = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="زمان پاسخ خوشایندی (میلی‌ثانیه)"
    )

    # نمره برانگیختگی (Arousal) - از 1 تا 9
    arousal = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="برانگیختگی (Arousal)"
    )
    arousal_rt = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="زمان پاسخ برانگیختگی (میلی‌ثانیه)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد"
    )

    class Meta:
        unique_together = ('user', 'stimulus')  # هر کاربر فقط یک بار برای هر محرک رتبه بدهد
        verbose_name = "0-Rating"
        verbose_name_plural = "0-Rating"
        ordering = ['-created_at']

    def __str__(self):
        v = f"Valence: {self.valence}" if self.valence is not None else "Valence: -"
        a = f"Arousal: {self.arousal}" if self.arousal is not None else "Arousal: -"
        return f"{v} | {a} — {self.stimulus} — {self.user.username}"

    # اختیاری: متدهای کمکی برای بررسی اینکه آیا هر کدام پاسخ داده شده
    def has_valence(self):
        return self.valence is not None

    def has_arousal(self):
        return self.arousal is not None

    def is_complete(self):
        return self.has_valence() and self.has_arousal()
 
 
class PCMSequencePracticeResponse(models.Model):  # مرحله ۱
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    stimulus1 = models.CharField(max_length=100, null=True, blank=True)
    stimulus2 = models.CharField(max_length=100, null=True, blank=True)
    category_stim1 = models.CharField(max_length=10, null=True, blank=True)
    category_stim2 = models.CharField(max_length=10, null=True, blank=True)
    user_response = models.CharField(max_length=30, null=True, blank=True)  # توالی انتخابی
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trial', 'created_at')
        verbose_name = "1-تمرین تشخیص توالی"
        ordering = ['created_at']


class PCMValencePracticeResponse(models.Model):  # مرحله ۲
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    stimulus1 = models.CharField(max_length=100, null=True, blank=True)
    stimulus2 = models.CharField(max_length=100, null=True, blank=True)
    category_stim1 = models.CharField(max_length=10, null=True, blank=True)
    category_stim2 = models.CharField(max_length=10, null=True, blank=True)
    valence_stim1 = models.IntegerField(null=True, blank=True)
    valence_rt_stim1 = models.PositiveIntegerField(null=True, blank=True)
    valence_stim2 = models.IntegerField(null=True, blank=True)
    valence_rt_stim2 = models.PositiveIntegerField(null=True, blank=True)
    valence_sequence = models.IntegerField(null=True, blank=True)
    valence_rt_sequence = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trial')
        verbose_name = "2-تمرین رتبه‌بندی خوشایندی"
        ordering = ['trial']


class PCMMainResponse(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )
    block = models.PositiveIntegerField(
        verbose_name="شماره بلاک"
    )
    trial = models.PositiveIntegerField(
        verbose_name="شماره تریال"
    )
    cue = models.CharField(
        max_length=100,
        verbose_name="نام فایل کیو (Cue)"
    )
    stimulus1 = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="نام فایل محرک اول"
    )
    stimulus2 = models.CharField(
        max_length=100,
        null=True,
        blank=True,
        verbose_name="نام فایل محرک دوم"
    )

    expected_sequence = models.CharField(
        max_length=30,
        verbose_name="توالی مورد انتظار",
        choices=[
            ('Neutral-Neutral', 'Neutral-Neutral'),
            ('Negative-Neutral', 'Negative-Neutral'),
            ('Neutral-Negative', 'Neutral-Negative'),
        ],
        blank=True,
        null=True
    )

    is_consistent = models.BooleanField(
        default=True,
        verbose_name="آیا توالی ارائه‌شده با کیو سازگار بود؟"
    )

    category_stim1 = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="دسته محرک اول"
    )
    category_stim2 = models.CharField(
        max_length=10,
        null=True,
        blank=True,
        verbose_name="دسته محرک دوم"
    )
    valence_stim1 = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="پاسخ خوشایندی محرک اول (Valence)"
    )
    valence_rt_stim1 = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="زمان پاسخ خوشایندی محرک اول (میلی‌ثانیه)"
    )
    valence_stim2 = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="پاسخ خوشایندی محرک دوم (Valence)"
    )
    valence_rt_stim2 = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="زمان پاسخ خوشایندی محرک دوم (میلی‌ثانیه)"
    )
    valence_sequence = models.IntegerField(
        null=True,
        blank=True,
        verbose_name="پاسخ خوشایندی کل توالی (Valence)"
    )
    valence_rt_sequence = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name="زمان پاسخ خوشایندی کل توالی (میلی‌ثانیه)"
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد"
    )

    class Meta:
        unique_together = ('user', 'block', 'trial')
        verbose_name = "3-PCM-main"
        verbose_name_plural = "3-PCM-main"
        ordering = ['-created_at', 'block', 'trial']

    def __str__(self):
        return f"{self.user.username} - Block {self.block} - Trial {self.trial} - Cue: {self.cue}"

    def is_complete(self):
        return (
            self.valence_stim1 is not None and
            self.valence_stim2 is not None and
            self.valence_sequence is not None
        )

class RatingPracticeResponse(models.Model):  # مرحله ۴ - تمرین رتبه‌بندی Valence+Arousal
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField()
    stimulus = models.CharField(max_length=100)
    valence = models.IntegerField(null=True, blank=True)
    valence_rt = models.PositiveIntegerField(null=True, blank=True)
    arousal = models.IntegerField(null=True, blank=True)
    arousal_rt = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'trial')
        verbose_name = "4-تمرین رتبه‌بندی (Valence+Arousal)"
        ordering = ['trial']

class RatingMainResponse(models.Model):  # مرحله ۵ - رتبه‌بندی اصلی
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    stimulus_file = models.CharField(max_length=200)
    stimulus_number = models.CharField(max_length=50)
    valence = models.IntegerField(null=True, blank=True)
    valence_rt = models.PositiveIntegerField(null=True, blank=True)
    arousal = models.IntegerField(null=True, blank=True)
    arousal_rt = models.PositiveIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'stimulus_number')
        verbose_name = "5-رتبه‌بندی اصلی"
        ordering = ['-created_at']


class PCMCueMapping(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    mapping = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نگاشت ثابت Cue به Sequence در PCM"