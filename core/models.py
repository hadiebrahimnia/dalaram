from django.db import models
from django.contrib.auth.models import AbstractUser

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 

class CustomUser(AbstractUser):

    username = models.CharField(
        "شماره موبایل",
        max_length=11,
        unique=True,
        help_text="شماره موبایل کاربر (۱۱ رقمی)",
    )

    birth_date = models.DateField(
        "تاریخ تولد",
        null=True,
        blank=True,
    )

    GENDER_CHOICES = [
        ("M", "مرد"),
        ("F", "زن"),
    ]

    gender = models.CharField(
        "جنسیت",
        max_length=1,
        choices=GENDER_CHOICES,
        null=True,
        blank=True,
    )

    HAND_CHOICES = [
        ("R", "راست"),
        ("L", "چپ"),
    ]
    hand = models.CharField(
        "دست غالب",
        max_length=1,
        choices=HAND_CHOICES,
        null=True,
        blank=True,
    )

    MARRIAGE_CHOICES = [
        ("S", "مجرد"),
        ("M", "متاهل"),
    ]
    marriage = models.CharField(
        "وضعیت تاهل",
        max_length=1,
        choices=MARRIAGE_CHOICES,
        null=True,
        blank=True,
    )

    EDUCATION_CHOICES = [
        ("NONE", "بدون تحصیلات رسمی"),
        ("PRIMARY", "ابتدایی"),
        ("SECONDARY", "متوسطه"),
        ("DIPLOMA", "دیپلم"),
        ("ASSOCIATE", "کاردانی"),
        ("BACHELOR", "کارشناسی"),
        ("MASTER", "کارشناسی ارشد"),
        ("PHD", "دکتری"),
    ]
    education = models.CharField(
        "سطح تحصیلات",
        max_length=20,
        choices=EDUCATION_CHOICES,
        null=True,
        blank=True,
    )

    SMOKING_CHOICES = [
        ("NONE", "هرگز مصرف نکرده‌ام"),
        ("PAST", "در گذشته مصرف می‌کردم (فعلاً خیر)"),
        ("OCCASIONAL", "گاه‌به‌گاه مصرف می‌کنم"),
        ("REGULAR", "مصرف منظم دارم"),
    ]
    smoking = models.CharField(
        "مصرف سیگار",
        max_length=12,
        choices=SMOKING_CHOICES,
        null=True,
        blank=True,
    )

    ALCOHOL_CHOICES = [
        ("NONE", "هرگز مصرف نکرده‌ام"),
        ("PAST", "در گذشته مصرف می‌کردم (فعلاً خیر)"),
        ("OCCASIONAL", "گاه‌به‌گاه مصرف می‌کنم"),
        ("REGULAR", "مصرف منظم دارم"),
    ]
    alcohol = models.CharField(
        "مصرف الکل",
        max_length=12,
        choices=ALCOHOL_CHOICES,
        null=True,
        blank=True,
    )

    CAFFEINE_CHOICES = [
        ("NONE", "اصلاً مصرف نمی‌کنم"),
        ("LOW", "کم (۱ فنجان یا کمتر در روز)"),
        ("MODERATE", "متوسط (۲–۳ فنجان در روز)"),
        ("HIGH", "زیاد (بیش از ۳ فنجان در روز)"),
    ]
    caffeine = models.CharField(
        "مصرف کافئین",
        max_length=10,
        choices=CAFFEINE_CHOICES,
        null=True,
        blank=True,
    )

    TRAUMA_CHOICES = [
        ("NONE", "ندارم"),
        ("MILD", "رویداد استرس‌زای خفیف"),
        ("MODERATE", "رویداد استرس‌زای متوسط"),
        ("SEVERE", "ترومای شدید یا چندین رویداد"),
    ]
    trauma = models.CharField(
        "سابقه تروما یا رویدادهای استرس‌زا",
        max_length=10,
        choices=TRAUMA_CHOICES,
        null=True,
        blank=True,
    )

    SUBSTANCE_CHOICES = [
        ("NONE", "هرگز مصرف نکرده‌ام"),
        ("PAST", "در گذشته مصرف کرده‌ام (فعلاً خیر)"),
        ("OCCASIONAL", "گاه‌به‌گاه مصرف می‌کنم"),
        ("REGULAR", "مصرف منظم دارم"),
    ]
    substance = models.CharField(
        "مصرف مواد مخدر",
        max_length=12,
        choices=SUBSTANCE_CHOICES,
        null=True,
        blank=True,
    )

    SUPPLEMENT_CHOICES = [
        ("NONE", "مصرف نمی‌کنم"),
        ("OCCASIONAL", "گاه‌به‌گاه"),
        ("REGULAR", "به‌صورت منظم"),
    ]
    supplement = models.CharField(
        "مصرف مکمل‌ها یا ویتامین‌ها",
        max_length=12,
        choices=SUPPLEMENT_CHOICES,
        null=True,
        blank=True,
    )

    TBI_CHOICES = [
        ("NONE", "ندارم"),
        ("MILD", "ضربه خفیف (بدون از دست دادن هوشیاری)"),
        ("MODERATE", "ضربه متوسط (از دست دادن کوتاه‌مدت هوشیاری)"),
        ("SEVERE", "ضربه شدید (از دست دادن طولانی‌مدت هوشیاری یا بستری)"),
    ]
    tbi = models.CharField(
        "سابقه ضربه مغزی",
        max_length=10,
        choices=TBI_CHOICES,
        null=True,
        blank=True,
    )

    SEIZURE_CHOICES = [
        ("NONE", "ندارم"),
        ("PAST", "در گذشته داشتم (فعلاً خیر)"),
        ("CONTROLLED", "دارم ولی تحت کنترل است"),
        ("ACTIVE", "دارم و فعال است"),
    ]
    seizure = models.CharField(
        "سابقه تشنج یا صرع",
        max_length=12,
        choices=SEIZURE_CHOICES,
        null=True,
        blank=True,
    )

    SLEEP_CHOICES = [
        ("NONE", "ندارم"),
        ("INSOMNIA", "بی‌خوابی"),
        ("HYPERSOMNIA", "خواب‌آلودگی بیش از حد"),
        ("SLEEP_APNEA", "آپنه خواب"),
        ("NIGHTMARE", "کابوس‌های مکرر"),
        ("OTHER", "سایر اختلالات خواب"),
    ]
    sleep = models.CharField(
        "اختلال خواب",
        max_length=15,
        choices=SLEEP_CHOICES,
        null=True,
        blank=True,
    )

    sleep_hours = models.FloatField(
        "میانگین ساعات خواب",
        null=True,
        blank=True,
    )

    MENTAL_DISORDER_CHOICES = [
        ("DEPRESSION", "افسردگی"),
        ("ANXIETY", "اضطراب"),
        ("PANIC", "اختلال پانیک"),
        ("OCD", "وسواس فکری-عملی (OCD)"),
        ("PTSD", "اختلال استرس پس از سانحه (PTSD)"),
        ("BIPOLAR", "اختلال دوقطبی"),
        ("SCHIZOPHRENIA", "اسکیزوفرنی"),
        ("ADHD", "اختلال کمبود توجه/بیش‌فعالی (ADHD)"),
        ("PERSONALITY", "اختلال شخصیت"),
        ("OTHER", 'سایر(در قسمت " توضیحات تکمیلی " توضیح دهید)'),
    ]

    mental_disorders = models.JSONField(
        "اختلالات روانی",
        default=list,
        blank=True,
        help_text="می‌توانید چند مورد را انتخاب کنید",
    )

    disorder = models.TextField(
        "سابقه بیماری",
        max_length=200,
        blank=True,
    )

    drug = models.TextField(
        "سابقه مصرف دارو",
        max_length=100,
        blank=True,
    )

    notes = models.TextField(
        "توضیحات تکمیلی",
        blank=True,
    )

    def __str__(self):
        return self.username

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 

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
    num_questions = models.IntegerField(verbose_name="تعداد سوالات مربوط به ویژگی", default=0)
    raw_score = models.FloatField(verbose_name="نمره خام", default=0.0)
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
    

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
class DeviceLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='device_logs')
    stage = models.CharField(max_length=50, verbose_name="مرحله")
    device_type = models.CharField(max_length=20)
    os = models.CharField(max_length=30)
    browser = models.CharField(max_length=30)
    screen_width = models.PositiveIntegerField(null=True, blank=True, verbose_name="طول صفحه" )
    screen_height = models.PositiveIntegerField( null=True, blank=True, verbose_name="ارتفاع صفحه" )
    is_touch = models.BooleanField( default=False, verbose_name="دستگاه لمسی؟" )
    audio_volume = models.FloatField( null=True, blank=True, verbose_name="حجم صدای تنظیم‌شده" )
    
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        verbose_name = "لاگ تغییر دستگاه"
        verbose_name_plural = "لاگ‌های تغییر دستگاه"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.stage} | {self.device_type}"

class VolumeLog(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='volume_log')
    volume = models.PositiveIntegerField( null=True, blank=True, verbose_name="volume" )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "حجم صدا"
        verbose_name_plural = "حجم صدا"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} | {self.volume} "

class FeedbackSettings(models.Model):
    # ... فیلدهای دیگر تنظیمات ...
    FEEDBACK_MODE_CHOICES = [
        ('always', 'همیشه نمایش داده شود'),
        ('never', 'هرگز نمایش داده نشود'),
        ('first_n', 'فقط در N محرک اول'),
        ('until_n_correct', 'تا رسیدن به N پاسخ درست متوالی یا کلی'),
        ('first_n_or_until_correct', 'N محرک اول یا تا رسیدن به M پاسخ درست (هرکدام زودتر)'),
    ]

    feedback_mode = models.CharField(
        max_length=30,
        choices=FEEDBACK_MODE_CHOICES,
        default='always',
        verbose_name="حالت نمایش فیدبک"
    )

    feedback_first_n = models.PositiveIntegerField(
        default=5,
        verbose_name="تعداد محرک اول برای نمایش فیدبک (در حالت first_n)"
    )

    feedback_until_correct = models.PositiveIntegerField(
        default=5,
        verbose_name="تعداد پاسخ درست مورد نیاز برای قطع فیدبک (در حالت until_n_correct)"
    )

    # اگر بخوای متوالی باشه یا تجمعی:
    feedback_correct_consecutive = models.BooleanField(
        default=False,
        verbose_name="پاسخ‌های درست باید متوالی باشند؟"
    )

    class Meta:
        verbose_name = "تنظیمات PCM"
        verbose_name_plural = "تنظیمات PCM"

    
    
class RatingPractice(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField()
    stimulus = models.CharField(max_length=100)
    valence = models.IntegerField(null=True, blank=True)
    valence_rt = models.PositiveIntegerField(null=True, blank=True)
    valence_delay_number = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    arousal = models.IntegerField(null=True, blank=True)
    arousal_rt = models.PositiveIntegerField(null=True, blank=True)
    arousal_delay_number = models.PositiveIntegerField(default=0, blank=True)
    arousal_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial')
        verbose_name = "A-0)practice"
        ordering = ['trial']


class RatingResponse(models.Model):
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        verbose_name="کاربر"
    )
    trial = models.PositiveIntegerField(null=True, blank=True)
    stimulus = models.CharField(
        max_length=50,
        verbose_name="محرک"
    )
    stimulus_file = models.CharField(max_length=200,null=True, blank=True)
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
    valence_delay_number = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    
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
    arousal_delay_number = models.PositiveIntegerField(default=0, blank=True)
    arousal_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'stimulus')  # هر کاربر فقط یک بار برای هر محرک رتبه بدهد
        verbose_name = "A-1)Rating"
        verbose_name_plural = "A-1)Rating"
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
    

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
# مرحله 1
class PCMValencePracticeResponse(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    stimulus1 = models.CharField(max_length=100, null=True, blank=True)
    stimulus2 = models.CharField(max_length=100, null=True, blank=True)
    category_stim1 = models.CharField(max_length=10, null=True, blank=True)
    category_stim2 = models.CharField(max_length=10, null=True, blank=True)
    valence_stim1 = models.IntegerField(null=True, blank=True)
    valence_rt_stim1 = models.PositiveIntegerField(null=True, blank=True)
    valence_delay_number_stim1 = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_stim1 = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    valence_stim2 = models.IntegerField(null=True, blank=True)
    valence_rt_stim2 = models.PositiveIntegerField(null=True, blank=True)
    valence_delay_number_stim2 = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_stim2 = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    valence_sequence = models.IntegerField(null=True, blank=True)
    valence_rt_sequence = models.PositiveIntegerField(null=True, blank=True)
    valence_delay_number_sequence = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_sequence = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial')
        verbose_name = "B-1)ValencePractice"
        ordering = ['trial']

# مرحله 2
class PCMSequencePracticeResponse(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    block = models.PositiveIntegerField(
            verbose_name="شماره بلاک", null=True, blank=True
        )
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    stimulus1 = models.CharField(max_length=100, null=True, blank=True)
    stimulus2 = models.CharField(max_length=100, null=True, blank=True)
    category_stim1 = models.CharField(max_length=10, null=True, blank=True)
    category_stim2 = models.CharField(max_length=10, null=True, blank=True)
    expected_sequence = models.CharField(
        max_length=30,
        verbose_name="توالی مورد انتظار",
        blank=True,
        null=True
    )
    is_consistent = models.BooleanField(
        default=True,
        verbose_name="آیا توالی ارائه‌شده با کیو سازگار بود؟"
    )
    user_response = models.CharField(max_length=30, null=True, blank=True)
    response_rt = models.PositiveIntegerField(null=True, blank=True)
    delay_number = models.PositiveIntegerField(default=0, blank=True) 
    response_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial', 'created_at')
        verbose_name = "B-2)SequencePractice"
        ordering = ['created_at']


class PCMSequenceCatchResponse(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    block = models.PositiveIntegerField(
        verbose_name="شماره بلاک", null=True, blank=True
    )
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    user_response = models.CharField(max_length=30, null=True, blank=True)  # توالی انتخابی
    response_rt = models.PositiveIntegerField(null=True, blank=True)
    delay_number = models.PositiveIntegerField(default=0, blank=True)
    response_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial', 'created_at')
        verbose_name = "B-3)SequenceCatch"
        ordering = ['created_at']

# مرحله 3
class PCMCatchResponse(models.Model):  
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    block = models.PositiveIntegerField(
        verbose_name="شماره بلاک", null=True, blank=True
    )
    trial = models.PositiveIntegerField()
    cue = models.CharField(max_length=100)
    user_response = models.CharField(max_length=30, null=True, blank=True)  # توالی انتخابی
    response_rt = models.PositiveIntegerField(null=True, blank=True)
    delay_number = models.PositiveIntegerField(default=0, blank=True)
    response_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    is_correct = models.BooleanField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial', 'created_at')
        verbose_name = "B-4)PCM-Catch"
        ordering = ['created_at']

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
    valence_delay_number_stim1 = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_stim1 = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
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
    valence_delay_number_stim2 = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_stim2 = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
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
    valence_delay_number_sequence = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method_sequence = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="زمان ایجاد"
    )
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'block', 'trial')
        verbose_name = "B-5)PCM-Main"
        verbose_name_plural = "B-5)PCM-Main"
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
    valence_delay_number = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    arousal = models.IntegerField(null=True, blank=True)
    arousal_rt = models.PositiveIntegerField(null=True, blank=True)
    arousal_delay_number = models.PositiveIntegerField(default=0, blank=True)
    arousal_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'trial')
        verbose_name = "B-6)RatingPractice"
        ordering = ['trial']

class RatingMainResponse(models.Model):  # مرحله ۵ - رتبه‌بندی
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    trial = models.PositiveIntegerField(null=True, blank=True)
    stimulus_file = models.CharField(max_length=200)
    stimulus_number = models.CharField(max_length=50)
    valence = models.IntegerField(null=True, blank=True)
    valence_rt = models.PositiveIntegerField(null=True, blank=True)
    valence_delay_number = models.PositiveIntegerField(default=0, blank=True)
    valence_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    arousal = models.IntegerField(null=True, blank=True)
    arousal_rt = models.PositiveIntegerField(null=True, blank=True)
    arousal_delay_number = models.PositiveIntegerField(default=0, blank=True)
    arousal_input_method = models.CharField(
        max_length=20, 
        null=True, 
        blank=True,
        choices=[
            ('keyboard', 'Keyboard'),
            ('mouse', 'Mouse'),
            ('touch', 'Touch'),
        ]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True, verbose_name="فعال/غیرفعال")

    class Meta:
        unique_together = ('user', 'stimulus_number')
        verbose_name = "B-7)Rating"
        ordering = ['-created_at']


class PCMCueMapping(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, primary_key=True)
    mapping = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "نگاشت ثابت Cue به Sequence در PCM"


###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 