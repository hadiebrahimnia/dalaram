# decorators.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from .models import Questionnaire, Response

def questionnaires_required(questionnaire_ids):
    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            for q_id in questionnaire_ids:
                if not Response.objects.filter(
                    questionnaire_id=q_id,
                    respondent=request.user,
                    is_completed=True
                ).exists():
                    # ذخیره URL فعلی برای بازگشت بعد از تکمیل
                    request.session['next_url'] = request.get_full_path()
                    # ریدایرکت به اولین پرسشنامه پیش‌نیاز تکمیل‌نشده
                    return redirect('respond_questionnaire', pk=q_id)
            # همه پیش‌نیازها تکمیل شده → ادامه به ویو اصلی
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator