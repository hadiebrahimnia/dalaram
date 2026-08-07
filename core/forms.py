from django import forms
from django.forms import inlineformset_factory
from core.models import *
from core.widget import *

class usernameEntryForm(forms.Form):
    username = forms.CharField(
        widget=PersianusernameInput(attrs={
            'class': 'custom-input form-control text-center',
            'placeholder': 'شماره موبایل',
            'autofocus': True,
        }),
        label='شماره موبایل',
        max_length=11,
    )

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if username:
            username = ''.join(filter(str.isdigit, username))
            if not username.startswith('09') or len(username) != 11:
                raise forms.ValidationError("شماره موبایل باید ۱۱ رقم باشد و با ۰۹ شروع شود.")
            return username
        return username

class ParticipantInfoForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'birth_date',
            'gender',
            'hand',
            'marriage',
            'education',
            'smoking',
            'alcohol',
            'caffeine',
            'substance',
            'supplement',
            'trauma',
            'tbi',
            'seizure',
            'sleep',
            'sleep_hours',
            'mental_disorders',
            'disorder',
            'drug',
            'notes',
        ]

    # -------------------- تاریخ تولد --------------------
    birth_date = forms.DateField(
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ تولد',
            'data-jdp-max-date': 'today',
        }),
        label='تاریخ تولد',
        required=True,
    )

    # -------------------- جنسیت --------------------
    gender = forms.ChoiceField(
        choices=[('', 'لطفاً جنسیت را انتخاب کنید')] + list(CustomUser.GENDER_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='جنسیت',
        required=True,
    )

    # -------------------- دست غالب --------------------
    hand = forms.ChoiceField(
        choices=[('', 'لطفاً دست غالب را انتخاب کنید')] + list(CustomUser.HAND_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='دست غالب',
        required=True,
    )

    # -------------------- وضعیت تاهل --------------------
    marriage = forms.ChoiceField(
        choices=[('', 'لطفاً وضعیت تاهل را انتخاب کنید')] + list(CustomUser.MARRIAGE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='وضعیت تاهل',
        required=False,
    )

    # -------------------- سطح تحصیلات --------------------
    education = forms.ChoiceField(
        choices=[('', 'لطفاً سطح تحصیلات را انتخاب کنید')] + list(CustomUser.EDUCATION_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='سطح تحصیلات',
        required=True,
    )

    # -------------------- مصرف سیگار --------------------
    smoking = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.SMOKING_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='مصرف سیگار',
        required=True,
    )

    # -------------------- مصرف الکل --------------------
    alcohol = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.ALCOHOL_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='مصرف الکل',
        required=True,
    )

    # -------------------- مصرف کافئین --------------------
    caffeine = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.CAFFEINE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='مصرف کافئین',
        required=True,
    )

    # -------------------- مصرف مواد مخدر --------------------
    substance = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.SUBSTANCE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='مصرف مواد مخدر',
        required=True,
    )

    # -------------------- مصرف مکمل‌ها --------------------
    supplement = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.SUPPLEMENT_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='مصرف مکمل‌ها یا ویتامین‌ها',
        required=True,
    )

    # -------------------- سابقه تروما --------------------
    trauma = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.TRAUMA_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='سابقه تروما یا رویدادهای استرس‌زا',
        required=True,
    )

    # -------------------- سابقه ضربه مغزی --------------------
    tbi = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.TBI_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='سابقه ضربه مغزی',
        required=True,
    )

    # -------------------- سابقه تشنج --------------------
    seizure = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.SEIZURE_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='سابقه تشنج یا صرع',
        required=True,
    )

    # -------------------- اختلال خواب --------------------
    sleep = forms.ChoiceField(
        choices=[('', 'لطفاً انتخاب کنید')] + list(CustomUser.SLEEP_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='اختلال خواب',
        required=True,
    )

    # -------------------- میانگین ساعات خواب --------------------
    sleep_hours = forms.FloatField(
        widget=forms.NumberInput(attrs={
            'class': 'form-control text-center',
            'placeholder': 'مثلاً ۷.۵',
            'step': '0.5',
            'min': '0',
            'max': '24',
        }),
        label='میانگین ساعات خواب (در شبانه‌روز)',
        required=True,
    )

    # -------------------- اختلالات روانی (چند انتخابی) --------------------
    mental_disorders = forms.MultipleChoiceField(
        choices=CustomUser.MENTAL_DISORDER_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={
            'class': 'form-check-input',
        }),
        label='اختلالات روانی',
        required=False,
    )

    # -------------------- سابقه بیماری --------------------
    disorder = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 3,
            'placeholder': 'در صورت وجود، توضیح دهید',
        }),
        label='سابقه بیماری (جسمی یا روانی)',
        required=False,
    )

    # -------------------- سابقه مصرف دارو --------------------
    drug = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 3,
            'placeholder': 'در صورت مصرف ذکر کنید',
        }),
        label='سابقه مصرف دارو',
        required=False,
    )

    # -------------------- توضیحات تکمیلی --------------------
    notes = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 3,
            'placeholder': 'هر توضیح اضافی که لازم می‌دانید',
        }),
        label='توضیحات تکمیلی',
        required=False,
    )