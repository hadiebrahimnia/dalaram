from django import forms
from core.models import Participant
from core.widget import *

class ParticipantForm(forms.ModelForm):
    class Meta:
        model = Participant
        fields = ['phone', 'birth_date', 'gender', 'hand', 'disorder', 'drug']

    phone = forms.CharField(
        widget=PersianPhoneInput(attrs={
            'class': 'custom-input form-control text-center',
            'placeholder': 'شماره موبایل',
        }),
        label='شماره موبایل',
    )

    birth_date = forms.DateField(
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ تولد',
            'data-jdp-max-date': 'today',
        }),
        label='تاریخ تولد',
    )

    gender = forms.ChoiceField(
        choices=[('', 'لطفاً جنسیت را انتخاب کنید')] + list(Participant.GENDER_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select text-center custom-select',
        }),
        label='جنسیت',
        required=True,
    )

    hand = forms.ChoiceField(
        choices=[('', 'لطفاً دست غالب را انتخاب کنید')] + list(Participant.HAND_CHOICES),
        widget=forms.Select(attrs={
            'class': 'form-select text-center custom-select',
        }),
        label='دست غالب',
        required=True,
    )

    disorder = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 4,
            'placeholder': 'در صورت وجود، توضیح دهید',
        }),
        label='سابقه بیماری',
        help_text=' بیماری‌های روانی یا جسمی که در حال حاضر دارید',
        required=False,
    )

    drug = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 4,
            'placeholder': 'در صورت مصرف ذکر کنید ',
        }),
        label='سابقه مصرف دارو',
        help_text='داروهایی که در حال حاضر مصرف می‌کنید',
        required=False,
    )

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            phone = ''.join(filter(str.isdigit, phone))
            if not phone.startswith('09') or len(phone) != 11:
                raise forms.ValidationError("شماره موبایل باید ۱۱ رقم باشد و با ۰۹ شروع شود.")
            return phone
        return phone

