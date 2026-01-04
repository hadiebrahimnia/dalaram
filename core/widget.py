from django import forms
from datetime import datetime, date
import jdatetime
from django.templatetags.static import static
import re
from django.core.validators import RegexValidator
from django.utils.translation import gettext_lazy as _

class PersianDateInput(forms.DateInput):
    """
    A custom widget for handling Persian (Jalali) dates in Django forms.
    Displays dates in Persian format (YYYY/MM/DD) and stores them in Gregorian format.
    Integrates with persian-datepicker.js for a better user experience.
    """
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control form-control-lg date',
            'data-jdp': 'data-jdp',
            'autocomplete': 'off',
            'placeholder': 'تاریخ ',
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(attrs=default_attrs, format='%Y/%m/%d')

    def format_value(self, value):
        """
        Convert Gregorian date to Persian (Jalali) date for display.
        """
        if value and isinstance(value, (datetime, date, str)):
            try:
                if isinstance(value, str):
                    # Parse string to datetime if needed
                    value = datetime.strptime(value, '%Y-%m-%d')
                elif isinstance(value, datetime):
                    value = value.date()
                # Convert Gregorian to Jalali
                jalali_date = jdatetime.date.fromgregorian(date=value)
                return jalali_date.strftime('%Y/%m/%d')
            except (ValueError, TypeError):
                return value
        return value

    def get_context(self, name, value, attrs):
        """
        Ensure Persian date is rendered in templates.
        """
        context = super().get_context(name, value, attrs)
        context['widget']['value'] = self.format_value(value)
        return context

    def value_from_datadict(self, data, files, name):
        """
        Convert Persian date input to Gregorian for form processing.
        """
        value = super().value_from_datadict(data, files, name)
        if value:
            try:
                # Expect input in format like '1403/12/05'
                year, month, day = map(int, value.split('/'))
                # Convert Jalali to Gregorian
                gregorian_date = jdatetime.JalaliToGregorian(year, month, day).getGregorianList()
                return date(*gregorian_date)
            except (ValueError, TypeError):
                raise forms.ValidationError(
                    "فرمت تاریخ نامعتبر است. لطفاً تاریخ را به صورت 1403/12/05 وارد کنید."
                )
        return value

    class Media:
        # استفاده از static() برای تولید آدرس correct در همه محیط‌ها
        css = {
            'all': (
                static('plugins/jalalidatepicker/jalalidatepicker.css'),
            )
        }
        js = (
            static('plugins/jalalidatepicker/jalalidatepicker.js'),
        )



class PersianusernameInput(forms.TextInput):
    """
    ویجیت اختصاصی برای شماره موبایل ایرانی
    - فقط 11 رقم عددی
    - باید با 09 شروع شود
    - ورودی غیرعددی را بلاک می‌کند
    """

    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'form-control text-center',
            'placeholder': '۰۹۱۲۳۴۵۶۷۸۹',
            'maxlength': '11',
            'minlength': '11',
            'inputmode': 'numeric',  # کیبورد عددی در موبایل
            'pattern': '[0-9]{11}',  # برای اعتبارسنجی HTML5
            'dir': 'ltr',  # چون اعداد لاتین هستند
        }
        if attrs:
            default_attrs.update(attrs)

        super().__init__(attrs=default_attrs)

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        # اضافه کردن event برای جلوگیری از ورودی غیرعددی
        attrs.setdefault('oninput', "this.value = this.value.replace(/[^0-9]/g, '')")
        attrs.setdefault('onkeypress', "return event.charCode >= 48 && event.charCode <= 57")
        return attrs


# اختیاری: اعتبارسنجی قوی‌تر در سطح فیلد فرم
username_validator = RegexValidator(
    regex=r'^09\d{9}$',
    message=_("شماره موبایل باید ۱۱ رقم باشد و با ۰۹ شروع شود."),
    code='invalid_username'
)