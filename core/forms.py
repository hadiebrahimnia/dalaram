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
        fields = ['birth_date', 'gender', 'hand', 'disorder', 'drug']

    birth_date = forms.DateField(
        widget=PersianDateInput(attrs={
            'class': 'form-control text-center date',
            'placeholder': 'تاریخ تولد',
            'data-jdp-max-date': 'today',
        }),
        label='تاریخ تولد',
    )

    gender = forms.ChoiceField(
        choices=[('', 'لطفاً جنسیت را انتخاب کنید')] + list(CustomUser.GENDER_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
        label='جنسیت',
        required=True,
    )

    hand = forms.ChoiceField(
        choices=[('', 'لطفاً دست غالب را انتخاب کنید')] + list(CustomUser.HAND_CHOICES),
        widget=forms.Select(attrs={'class': 'form-select text-center custom-select'}),
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
        help_text='بیماری‌های روانی یا جسمی که در حال حاضر دارید',
        required=False,
    )

    drug = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'custom-textarea form-control',
            'rows': 4,
            'placeholder': 'در صورت مصرف ذکر کنید',
        }),
        label='سابقه مصرف دارو',
        help_text='داروهایی که در حال حاضر مصرف می‌کنید',
        required=False,
    )