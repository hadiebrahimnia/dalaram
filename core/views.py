from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles.storage import staticfiles_storage
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .decorators import questionnaires_required
import json
from django.utils import timezone
import os
import random
from django.templatetags.static import static
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from typing import Dict, List, Tuple, Optional
from django.views.decorators.csrf import csrf_exempt
from collections import defaultdict, Counter
from jdatetime import datetime as jdatetime
from django.views.decorators.http import require_POST
import datetime
from django.db.models import Avg, Count

import json

@login_required
@require_POST
def save_device_log(request):
    try:
        data = json.loads(request.body)

        DeviceLog.objects.create(
            user=request.user,
            stage=data.get('stage', 'unknown'),
            device_type=data.get('device_type', 'Unknown'),
            os=data.get('os', 'Unknown'),
            browser=data.get('browser', 'Unknown'),
            screen_width=data.get('screen_width'),
            screen_height=data.get('screen_height'),
            is_touch=data.get('is_touch', False),
            audio_volume=data.get('audio_volume'),
        )

        return JsonResponse({'status': 'success'})

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=400)

@login_required
@require_POST
def save_volume_log(request):
    try:
        data = json.loads(request.body)

        VolumeLog.objects.create(
            user=request.user,
            volume=data.get("volume")
        )

        return JsonResponse({"status": "success"})

    except Exception as e:
        return JsonResponse(
            {"status": "error", "message": str(e)},
            status=400
        )
    
# _LATIN_TO_PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')

def convert_birth_to_jalali_view(user):
    """
    تبدیل تاریخ تولد کاربر به تاریخ شمسی با اعداد فارسی
    """
    try:
        if not user.birth_date:
            return '-'

        jalali_date = jdatetime.fromgregorian(date=user.birth_date)
        jalali_full = jalali_date.strftime('%Y/%m/%d')
        # jalali_full_persian = jalali_full.translate(_LATIN_TO_PERSIAN_DIGITS)
        return jalali_full

    except Exception:
        return '-'


def calculate_age_view(user):
    """
    محاسبه سن کاربر بر اساس تاریخ تولد
    """
    try:
        if not user.birth_date:
            return '-'

        today = date.today()
        age_years = today.year - user.birth_date.year
        if (today.month, today.day) < (user.birth_date.month, user.birth_date.day):
            age_years -= 1
        return age_years

    except Exception:
        return '-'

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
def home_view(request):
    return render(request, 'index.html')

def temp_home_view(request):
    return render(request, 'temp_home.html')

def taninyar(request):
    return render(request, 'taninyar.html')
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
def login_or_signup(request):
    if request.user.is_authenticated:
        return redirect('home')

    if request.method == 'POST' and 'username' in request.POST:
        username_form = usernameEntryForm(request.POST)
        if username_form.is_valid():
            username = username_form.cleaned_data['username']
            request.session['pending_username'] = username

            if CustomUser.objects.filter(username=username).exists():
                user = CustomUser.objects.get(username=username)
                login(request, user)
                messages.success(request, f"خوش آمدید {username}")
                return redirect('home')
            else:
                messages.info(request, "لطفاً اطلاعات خود را تکمیل کنید.")
                return redirect('complete_profile')
    else:
        username_form = usernameEntryForm()

    return render(request, 'username_entry.html', {'form': username_form})


###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
def complete_profile(request):
    if request.user.is_authenticated:
        return redirect('home')

    username = request.session.get('pending_username')
    if not username:
        messages.error(request, "شماره موبایل یافت نشد. دوباره شروع کنید.")
        return redirect('login_or_signup')

    if request.method == 'POST':
        form = ParticipantInfoForm(request.POST)
        if form.is_valid():
            # ساخت کاربر با تمام فیلدهای فرم
            user = CustomUser(
                username=username,
                birth_date=form.cleaned_data.get('birth_date'),
                gender=form.cleaned_data.get('gender'),
                hand=form.cleaned_data.get('hand'),
                marriage=form.cleaned_data.get('marriage'),
                education=form.cleaned_data.get('education'),
                smoking=form.cleaned_data.get('smoking'),
                alcohol=form.cleaned_data.get('alcohol'),
                caffeine=form.cleaned_data.get('caffeine'),
                substance=form.cleaned_data.get('substance'),
                supplement=form.cleaned_data.get('supplement'),
                trauma=form.cleaned_data.get('trauma'),
                tbi=form.cleaned_data.get('tbi'),
                seizure=form.cleaned_data.get('seizure'),
                sleep=form.cleaned_data.get('sleep'),
                sleep_hours=form.cleaned_data.get('sleep_hours'),
                mental_disorders=form.cleaned_data.get('mental_disorders', []),  # لیست چندانتخابی
                disorder=form.cleaned_data.get('disorder', ''),
                drug=form.cleaned_data.get('drug', ''),
                notes=form.cleaned_data.get('notes', ''),
            )
            user.set_unusable_password()  # چون با شماره موبایل وارد می‌شود
            user.save()

            login(request, user)
            messages.success(request, "ثبت‌نام با موفقیت انجام شد! خوش آمدید.")

            # پاک کردن سشن
            if 'pending_username' in request.session:
                del request.session['pending_username']

            return redirect('home')
    else:
        form = ParticipantInfoForm()

    return render(request, 'complete_profile.html', {
        'form': form,
        'username': username,
    })

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 

@login_required(login_url='login_or_signup')
def respond_questionnaire(request, pk):
    questionnaire = get_object_or_404(Questionnaire, pk=pk, is_active=True)
    questions = questionnaire.questions.all().prefetch_related('choices')
    if request.method == 'POST' and 'submit_final' in request.POST:
        answers_data = json.loads(request.POST.get('answers_data', '[]'))
        response = Response.objects.create(
            questionnaire=questionnaire,
            respondent=request.user,
            is_completed=True,
            completed_at=timezone.now()
        )
        for ans in answers_data:
            Answer.objects.create(
                response=response,
                question_id=ans['question_id'],
                choice_id=ans.get('choice_id'),
                text_answer=ans.get('text_answer') or '',
                scale_value=ans.get('scale_value'),
                RT=ans.get('rt')
            )
        

        attributes = Attribute.objects.filter(
            questions__questionnaire=questionnaire
        ).distinct()
        
        for attribute in attributes:
            answers = response.answers.filter(question__attribute=attribute)
            num_questions = answers.count()
            if num_questions > 0:
                raw_score = sum(
                    (ans.choice.value if ans.choice else ans.scale_value or 0) 
                    for ans in answers if ans.question.question_type in ['MC', 'SC']  # فقط برای انواع امتیازدار
                )
                average_score = raw_score / num_questions
                sum_rt = sum(ans.RT or 0 for ans in answers)
                average_rt = sum_rt / num_questions
            else:
                raw_score = 0
                average_score = 0
                sum_rt = 0
                average_rt = 0
            
            Result.objects.create(
                user=request.user,
                questionnaire=questionnaire,
                response=response,
                attribute=attribute,
                raw_score=raw_score,
                num_questions=num_questions,
                average_score=average_score,
                sum_rt=sum_rt,
                average_rt=average_rt
            )
        
        messages.success(request, 'پاسخ‌های شما با موفقیت ثبت شد. خوش آمدید!')
        next_url = request.session.pop('next_url', None)  # pop برای پاک کردن سشن
        if next_url:
            return redirect(next_url)
        return redirect('home')
    return render(request, 'respond.html', {
        'questionnaire': questionnaire,
        'questions': questions,
    })

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 

@login_required(login_url='login_or_signup')
@questionnaires_required([1,2,3])
def rating_view(request):
    user = request.user
    RATING_PRACTICE_TRIALS = 10
    PRACTICE_FILES_RAW = [
        '0-practice/1.mp3',
        '0-practice/2.mp3',
        '0-practice/3.mp3',
        '0-practice/4.mp3',
        '0-practice/5.mp3',
        '0-practice/6.mp3',
        '0-practice/7.mp3',
        '0-practice/8.mp3',
        '0-practice/9.mp3',
        '0-practice/10.mp3',
    ]
    practice_files = [build_audio_url(f) for f in PRACTICE_FILES_RAW[:RATING_PRACTICE_TRIALS]]
    rating_practice_count = RatingPractice.objects.filter(user=user).count()
    progress_percentage = (rating_practice_count / RATING_PRACTICE_TRIALS) * 100
    if rating_practice_count < RATING_PRACTICE_TRIALS:
        remaining_files = practice_files[rating_practice_count:]
        context = {
            'current_trial': rating_practice_count + 1,
            'count':rating_practice_count,
            'total_trials': RATING_PRACTICE_TRIALS,
            'progress_percentage': progress_percentage,
            'remaining_practice_files': json.dumps(remaining_files),
        }
        return render(request, 'rating_1.html', context)

    # --- مرحله ۵: رتبه‌بندی نهایی همه صداها (لیست ثابت مشخص‌شده) ---
    MAIN_RATING_FILES_RAW = [
        '1-HP-HA/110.mp3','1-HP-HA/200.mp3','1-HP-HA/201.mp3','1-HP-HA/202.mp3','1-HP-HA/205.mp3','1-HP-HA/215.mp3','1-HP-HA/220.mp3','1-HP-HA/311.mp3','1-HP-HA/352.mp3','1-HP-HA/353.mp3','1-HP-HA/355.mp3','1-HP-HA/360.mp3','1-HP-HA/363.mp3','1-HP-HA/365.mp3','1-HP-HA/366.mp3','1-HP-HA/367.mp3','1-HP-HA/378.mp3','1-HP-HA/415.mp3','1-HP-HA/716.mp3','1-HP-HA/717.mp3','1-HP-HA/808.mp3','1-HP-HA/815.mp3','1-HP-HA/817.mp3',

        '2-HP-MA/109.mp3','2-HP-MA/111.mp3','2-HP-MA/112.mp3','2-HP-MA/150.mp3','2-HP-MA/151.mp3','2-HP-MA/206.mp3','2-HP-MA/221.mp3','2-HP-MA/224.mp3','2-HP-MA/226.mp3','2-HP-MA/230.mp3','2-HP-MA/254.mp3','2-HP-MA/270.mp3','2-HP-MA/351.mp3','2-HP-MA/400.mp3','2-HP-MA/601.mp3','2-HP-MA/721.mp3','2-HP-MA/725.mp3','2-HP-MA/726.mp3','2-HP-MA/802.mp3','2-HP-MA/810.mp3','2-HP-MA/811.mp3','2-HP-MA/813.mp3','2-HP-MA/816.mp3','2-HP-MA/820.mp3','2-HP-MA/826.mp3',

        '3-HP-LA/172.mp3','3-HP-LA/809.mp3','3-HP-LA/812.mp3',

        '4-MP-HA/114.mp3','4-MP-HA/204.mp3','4-MP-HA/210.mp3','4-MP-HA/216.mp3','4-MP-HA/610.mp3','4-MP-HA/704.mp3','4-MP-HA/710.mp3','4-MP-HA/715.mp3',

        '5-MP-MA/102.mp3','5-MP-MA/104.mp3','5-MP-MA/107.mp3','5-MP-MA/111.mp3','5-MP-MA/113.mp3','5-MP-MA/120.mp3','5-MP-MA/130.mp3','5-MP-MA/132.mp3','5-MP-MA/152.mp3','5-MP-MA/170.mp3','5-MP-MA/225.mp3','5-MP-MA/245.mp3','5-MP-MA/246.mp3','5-MP-MA/251.mp3','5-MP-MA/252.mp3','5-MP-MA/320.mp3','5-MP-MA/322.mp3','5-MP-MA/358.mp3','5-MP-MA/361.mp3','5-MP-MA/364.mp3','5-MP-MA/368.mp3','5-MP-MA/370.mp3','5-MP-MA/373.mp3','5-MP-MA/374.mp3','5-MP-MA/375.mp3','5-MP-MA/376.mp3','5-MP-MA/382.mp3','5-MP-MA/403.mp3','5-MP-MA/410.mp3','5-MP-MA/425.mp3','5-MP-MA/500.mp3','5-MP-MA/627.mp3','5-MP-MA/698.mp3','5-MP-MA/700.mp3','5-MP-MA/701.mp3','5-MP-MA/702.mp3','5-MP-MA/705.mp3','5-MP-MA/706.mp3','5-MP-MA/720.mp3','5-MP-MA/722.mp3','5-MP-MA/723.mp3','5-MP-MA/724.mp3','5-MP-MA/728.mp3','5-MP-MA/729.mp3',

        '6-MP-LA/171.mp3','6-MP-LA/262.mp3','6-MP-LA/377.mp3','6-MP-LA/602.mp3','6-MP-LA/708.mp3',

        '7-LP-HA/105.mp3','7-LP-HA/106.mp3','7-LP-HA/115.mp3','7-LP-HA/116.mp3','7-LP-HA/133.mp3','7-LP-HA/134.mp3','7-LP-HA/244.mp3','7-LP-HA/255.mp3','7-LP-HA/260.mp3','7-LP-HA/261.mp3','7-LP-HA/275.mp3','7-LP-HA/276.mp3','7-LP-HA/277.mp3','7-LP-HA/278.mp3','7-LP-HA/279.mp3','7-LP-HA/281.mp3','7-LP-HA/282.mp3','7-LP-HA/283.mp3','7-LP-HA/284.mp3','7-LP-HA/285.mp3','7-LP-HA/286.mp3','7-LP-HA/288.mp3','7-LP-HA/289.mp3','7-LP-HA/290.mp3','7-LP-HA/292.mp3','7-LP-HA/296.mp3','7-LP-HA/310.mp3','7-LP-HA/312.mp3','7-LP-HA/319.mp3','7-LP-HA/380.mp3','7-LP-HA/420.mp3','7-LP-HA/422.mp3','7-LP-HA/423.mp3','7-LP-HA/424.mp3','7-LP-HA/501.mp3','7-LP-HA/502.mp3','7-LP-HA/600.mp3','7-LP-HA/624.mp3','7-LP-HA/625.mp3','7-LP-HA/626.mp3','7-LP-HA/699.mp3','7-LP-HA/709.mp3','7-LP-HA/711.mp3','7-LP-HA/712.mp3','7-LP-HA/713.mp3','7-LP-HA/714.mp3','7-LP-HA/719.mp3','7-LP-HA/730.mp3','7-LP-HA/732.mp3','7-LP-HA/910.mp3',

        '8-LP-MA/241.mp3','8-LP-MA/242.mp3','8-LP-MA/243.mp3','8-LP-MA/250.mp3','8-LP-MA/280.mp3','8-LP-MA/293.mp3','8-LP-MA/295.mp3','8-LP-MA/611.mp3','8-LP-MA/703.mp3',

    ]

    # حذف تکراری‌ها
    MAIN_RATING_FILES_RAW = list(set(MAIN_RATING_FILES_RAW))
    # تبدیل به URL کامل
    main_rating_files = [build_audio_url(f) for f in MAIN_RATING_FILES_RAW]
    # تعداد کل محرک‌ها
    TOTAL_MAIN_RATING_TRIALS = len(main_rating_files)
    # تعداد رتبه‌بندی‌های تکمیل‌شده (هر دو valence و arousal پر باشند)
    rating_main_done = RatingResponse.objects.filter(
        user=user
    ).exclude(
        valence__isnull=True
    ).exclude(
        arousal__isnull=True
    ).count()
    progress_percentage = (rating_main_done / TOTAL_MAIN_RATING_TRIALS) * 100 if TOTAL_MAIN_RATING_TRIALS > 0 else 100
    if rating_main_done < TOTAL_MAIN_RATING_TRIALS:
        completed_stimuli_urls = set(
            RatingResponse.objects.filter(
                user=user,
                valence__isnull=False,
                arousal__isnull=False
            ).values_list('stimulus_file', flat=True)
        )
        remaining_files = [f for f in main_rating_files if f not in completed_stimuli_urls]
        random.shuffle(remaining_files)
        context = {
            'current_trial': rating_main_done + 1,
            'count':rating_main_done,
            'total_trials': TOTAL_MAIN_RATING_TRIALS,
            'progress_percentage': progress_percentage,
            'remaining_main_files': json.dumps(remaining_files),
        }
        return render(request, 'rating_2.html', context)
    # --- پایان آزمون ---
    return redirect('/final/')

@csrf_exempt
def rating_save_response(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'فقط POST'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON نامعتبر'}, status=400)

    user = request.user

    
    # مرحله ۱: تمرین تشخیص توالی

    if data.get('is_rating_practice'):
        RatingPractice.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus')),
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            valence_delay_number = data.get('valence_delay_number', 0),
            valence_input_method = data.get('valence_input_method'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
            arousal_delay_number = data.get('arousal_delay_number', 0),
            arousal_input_method = data.get('arousal_input_method'),
        )

    elif data.get('is_rerating'):
        RatingResponse.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus_number')),
            stimulus_file=data['stimulus_file'],
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            valence_delay_number = data.get('valence_delay_number', 0),
            valence_input_method = data.get('valence_input_method'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
            arousal_delay_number = data.get('arousal_delay_number', 0),
            arousal_input_method = data.get('arousal_input_method'),
        )

    else:
        return JsonResponse({'status': 'error', 'message': 'نوع داده نامعتبر'}, status=400)

    return JsonResponse({'status': 'success'})

###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
def extract_stimulus_number(url: Optional[str]) -> Optional[int]:
    """استخراج شماره stimulus از URL فایل صوتی (مثل 102 از 102.mp3)"""
    if not url:
        return None
    try:
        filename = url.split('/')[-1]
        number_str = filename.split('.')[0]
        return int(number_str)
    except (IndexError, ValueError):
        return None


def get_cues_mapping() -> Dict[str, str]:
    """ساخت mapping بین فایل‌های cue و sequence مورد انتظار"""
    CUE_CATEGORIES = {
        '1': ['CUE/1/1.mp3'],
        '2': ['CUE/2/2.mp3'],
        '3': ['CUE/3/3.mp3'],
    }

    POSSIBLE_SEQUENCES = ['Neutral-Neutral', 'Negative-Neutral', 'Neutral-Negative']
    sequences_shuffled = POSSIBLE_SEQUENCES.copy()
    random.shuffle(sequences_shuffled)

    category_to_sequence = dict(zip(CUE_CATEGORIES.keys(), sequences_shuffled))
    
    cues_mapping = {}
    for category, sequence in category_to_sequence.items():
        for cue_file in CUE_CATEGORIES[category]:
            cues_mapping[cue_file] = sequence

    return {build_audio_url(key): value for key, value in cues_mapping.items()}


def get_stimuli_lists() -> Tuple[List[str], List[str]]:
    """لیست صداهای خنثی و منفی + shuffle"""
    neutral_files = [
        # '4-MP-HA/114.mp3',
        # '4-MP-HA/204.mp3',
        # '4-MP-HA/210.mp3',
        # '4-MP-HA/216.mp3',
        # '4-MP-HA/610.mp3',
        # '4-MP-HA/704.mp3',
        # '4-MP-HA/710.mp3',
        # '4-MP-HA/715.mp3',
        '5-MP-MA/102.mp3',
        # '5-MP-MA/104.mp3',
        # '5-MP-MA/107.mp3',
        # '5-MP-MA/111.mp3',
        # '5-MP-MA/113.mp3',
        # '5-MP-MA/120.mp3',
        # '5-MP-MA/130.mp3',
        # '5-MP-MA/132.mp3',
        '5-MP-MA/152.mp3',
        '5-MP-MA/170.mp3',
        # '5-MP-MA/225.mp3',
        # '5-MP-MA/245.mp3',
        '5-MP-MA/246.mp3',
        # '5-MP-MA/251.mp3',
        # '5-MP-MA/252.mp3',
        '5-MP-MA/320.mp3',
        '5-MP-MA/322.mp3',
        '5-MP-MA/358.mp3',
        '5-MP-MA/361.mp3',
        '5-MP-MA/364.mp3',
        '5-MP-MA/368.mp3',
        '5-MP-MA/370.mp3',
        '5-MP-MA/373.mp3',
        '5-MP-MA/374.mp3',
        '5-MP-MA/375.mp3',
        '5-MP-MA/376.mp3',
        '5-MP-MA/382.mp3',
        '5-MP-MA/403.mp3',
        '5-MP-MA/410.mp3',
        '5-MP-MA/425.mp3',
        # '5-MP-MA/500.mp3',
        # '5-MP-MA/627.mp3',
        '5-MP-MA/698.mp3',
        # '5-MP-MA/700.mp3',
        '5-MP-MA/701.mp3',
        # '5-MP-MA/702.mp3',
        '5-MP-MA/705.mp3',
        # '5-MP-MA/706.mp3',
        # '5-MP-MA/720.mp3',
        '5-MP-MA/722.mp3',
        # '5-MP-MA/723.mp3',
        '5-MP-MA/724.mp3',
        # '5-MP-MA/728.mp3',
        # '5-MP-MA/729.mp3',
    ]

    negative_files = [
        # '7-LP-HA/105.mp3',
        '7-LP-HA/106.mp3',
        '7-LP-HA/115.mp3',
        '7-LP-HA/116.mp3',
        '7-LP-HA/133.mp3',
        # '7-LP-HA/134.mp3',
        '7-LP-HA/244.mp3',
        '7-LP-HA/255.mp3',
        '7-LP-HA/260.mp3',
        '7-LP-HA/261.mp3',
        '7-LP-HA/275.mp3',
        '7-LP-HA/276.mp3',
        '7-LP-HA/277.mp3',
        '7-LP-HA/278.mp3',
        '7-LP-HA/279.mp3',
        # '7-LP-HA/281.mp3',
        '7-LP-HA/282.mp3',
        '7-LP-HA/283.mp3',
        '7-LP-HA/284.mp3',
        '7-LP-HA/285.mp3',
        '7-LP-HA/286.mp3',
        '7-LP-HA/288.mp3',
        '7-LP-HA/289.mp3',
        '7-LP-HA/290.mp3',
        '7-LP-HA/292.mp3',
        '7-LP-HA/296.mp3',
        '7-LP-HA/310.mp3',
        # '7-LP-HA/312.mp3',
        # '7-LP-HA/319.mp3',
        '7-LP-HA/380.mp3',
        '7-LP-HA/420.mp3',
        '7-LP-HA/422.mp3',
        '7-LP-HA/423.mp3',
        '7-LP-HA/424.mp3',
        '7-LP-HA/501.mp3',
        '7-LP-HA/502.mp3',
        '7-LP-HA/600.mp3',
        '7-LP-HA/624.mp3',
        '7-LP-HA/625.mp3',
        '7-LP-HA/626.mp3',
        '7-LP-HA/699.mp3',
        # '7-LP-HA/709.mp3',
        '7-LP-HA/711.mp3',
        '7-LP-HA/712.mp3',
        '7-LP-HA/713.mp3',
        '7-LP-HA/714.mp3',
        # '7-LP-HA/719.mp3',
        '7-LP-HA/730.mp3',
        '7-LP-HA/732.mp3',
        # '7-LP-HA/910.mp3',
        '8-LP-MA/241.mp3',
        '8-LP-MA/242.mp3',
        # '8-LP-MA/243.mp3',
        # '8-LP-MA/250.mp3',
        '8-LP-MA/280.mp3',
        '8-LP-MA/293.mp3',
        '8-LP-MA/295.mp3',
        '8-LP-MA/611.mp3',
        # '8-LP-MA/703.mp3',
    ]

    neutral_files = list(set(neutral_files))
    negative_files = list(set(negative_files))
    random.shuffle(neutral_files)
    random.shuffle(negative_files)

    return neutral_files, negative_files


def build_audio_url(filename: str) -> str:
    return f"/static/sounds/{filename}"

# متغیرهای مشترک برای همه مراحل
CUE_URLS = list(get_cues_mapping().keys())

# لیست همه صداهای استفاده‌شده در آزمون اصلی (برای مرحله ۵)
def get_used_stimuli_urls(user):
    stimuli = set()
    for resp in PCMMainResponse.objects.filter(user=user):
        if resp.stimulus1:
            stimuli.add(resp.stimulus1)
        if resp.stimulus2:
            stimuli.add(resp.stimulus2)
    return list(stimuli)

# SEQUENCES = ['Neutral-Neutral', 'Negative-Neutral', 'Neutral-Negative']
# def get_or_create_cue_mapping(user):
#     # ابتدا سعی می‌کنیم mapping موجود را بگیریم
#     try:
#         return PCMCueMapping.objects.get(user=user).mapping
#     except PCMCueMapping.DoesNotExist:
#         pass

#     # ساخت یک generator تصادفی محلی و deterministically بر اساس user
#     rng = random.Random(user.id or user.pk)

#     seqs = SEQUENCES[:]
#     rng.shuffle(seqs)

#     mapping = {}
#     for i, cue_url in enumerate(CUE_URLS):
#         if i < len(seqs):
#             mapping[cue_url] = seqs[i]
#         else:
#             mapping[cue_url] = rng.choice(SEQUENCES)

#     obj, created = PCMCueMapping.objects.get_or_create(
#         user=user,
#         defaults={'mapping': mapping}
#     )
#     return obj.mapping


# def get_sequence_order(user, total_trials: int) -> List[str]:
#     rng = random.Random(user.id)   # ← اینجا هم محلی

#     possible_sequences = ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"]
#     trials_per_seq = total_trials // 3
#     remainder = total_trials % 3

#     sequence_order = []
#     for _ in range(trials_per_seq):
#         sequence_order.extend(possible_sequences)

#     extra_sequences = possible_sequences[:remainder]
#     sequence_order.extend(extra_sequences)

#     rng.shuffle(sequence_order)
#     return sequence_order



SEQUENCES = ['Negative-Neutral', 'Neutral-Negative', 'Neutral-Neutral']
def get_or_create_cue_mapping(user):
    try:
        return PCMCueMapping.objects.get(user=user).mapping
    except PCMCueMapping.DoesNotExist:
        pass

    # تخصیص ثابت و بدون رندم برای همه کاربران
    mapping = {
        "/static/sounds/CUE/1/1.mp3": "Negative-Neutral",
        "/static/sounds/CUE/2/2.mp3": "Neutral-Negative",
        "/static/sounds/CUE/3/3.mp3": "Neutral-Neutral",
    }
    # اگر CUE_URLS از جای دیگری می‌آید و ممکن است ترتیب یا تعدادش فرق کند:
    obj, created = PCMCueMapping.objects.get_or_create(
        user=user,
        defaults={'mapping': mapping}
    )
    return obj.mapping

def get_sequence_order(user, total_trials: int) -> List[str]:
    possible_sequences = ["Negative-Neutral", "Neutral-Negative", "Neutral-Neutral"]
    trials_per_seq = total_trials // 3
    remainder = total_trials % 3
    sequence_order = []
    for _ in range(trials_per_seq):
        sequence_order.extend(possible_sequences)
    sequence_order.extend(possible_sequences[:remainder])
    return sequence_order

def normalize_cue_to_full(cue, cues_mapping) -> Optional[str]:
    """
    هر فرمتی از cue (عدد، نام فایل، یا مسیر کامل) را
    به مسیر کامل موجود در cues_mapping تبدیل می‌کند.
    """
    if cue is None:
        return None

    cue = str(cue).strip()

    # ۱. اگر از قبل مسیر کامل است
    if cue in cues_mapping:
        return cue

    # ۲. اگر فقط عدد است (مثل "1" یا 1)
    if cue.isdigit():
        candidate = f"/static/sounds/CUE/{cue}/{cue}.mp3"
        if candidate in cues_mapping:
            return candidate

    # ۳. اگر فقط نام فایل است (مثل "1.mp3")
    if cue.endswith('.mp3'):
        number = cue.split('.')[0]
        if number.isdigit():
            candidate = f"/static/sounds/CUE/{number}/{number}.mp3"
            if candidate in cues_mapping:
                return candidate

    # ۴. جستجوی آخرین بخش مسیر
    for full in cues_mapping:
        if full.endswith(f"/{cue}") or full.endswith(f"/{cue}.mp3"):
            return full

    return None


@login_required(login_url='login_or_signup')
@questionnaires_required([1, 2, 3])
def pcm_view(request):
    user = request.user
    cues_mapping = get_or_create_cue_mapping(user)
    neutral_raw, negative_raw = get_stimuli_lists()
    NEUTRAL_URLS = [build_audio_url(f) for f in neutral_raw]
    NEGATIVE_URLS = [build_audio_url(f) for f in negative_raw]

    # --- مرحله 1: تمرین رتبه‌بندی خوشایندی ---
    VALENCE_PRACTICE_TRIALS = 10
    valence_practice_responses = PCMValencePracticeResponse.objects.filter(user=user)
    valence_practice_count = valence_practice_responses.count()
    RESPONSE_TIMEOUT=3000
    progress_percentage = (valence_practice_count / VALENCE_PRACTICE_TRIALS) * 100

    if valence_practice_count < VALENCE_PRACTICE_TRIALS:
        # محاسبه تعداد باقی‌مانده
        remain_trials = VALENCE_PRACTICE_TRIALS - valence_practice_count

        possible_sequences = ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"]

        # شمارش توالی‌های استفاده‌شده تا الان
        used_sequences = [
            f"{r.category_stim1}-{r.category_stim2}"
            for r in valence_practice_responses
            if r.category_stim1 and r.category_stim2
        ]
        counts = Counter(used_sequences)

        # هدف: توزیع تقریباً برابر بین ۳ توالی در کل ۴ تریال
        # مثلاً: 2 + 1 + 1 یا 1 + 2 + 1 و غیره
        target_per_seq = VALENCE_PRACTICE_TRIALS // len(possible_sequences)  # 1
        remainder_total = VALENCE_PRACTICE_TRIALS % len(possible_sequences)  # 1

        remaining_per_seq = {}
        for i, seq in enumerate(possible_sequences):
            target = target_per_seq + (1 if i < remainder_total else 0)
            remaining_per_seq[seq] = max(0, target - counts.get(seq, 0))

        # ساخت لیست توالی‌های باقی‌مانده
        sequence_order = []
        for seq, rem in remaining_per_seq.items():
            sequence_order.extend([seq] * rem)

        # اگر به دلایلی مجموع باقی‌مانده با remain_trials برابر نبود (ایمنی)
        if len(sequence_order) < remain_trials:
            # پر کردن باقی‌مانده با توزیع متعادل
            extra_needed = remain_trials - len(sequence_order)
            for _ in range(extra_needed):
                sequence_order.append(random.choice(possible_sequences))

        # shuffle برای ترتیب تصادفی
        random.shuffle(sequence_order)

        context = {

            'current_trial': valence_practice_count,  # تعداد انجام‌شده (شروع از 0)
            'total_trials': VALENCE_PRACTICE_TRIALS,
            'progress_percentage': round(progress_percentage, 1),
            'cue_urls': json.dumps(CUE_URLS),
            'neutral_urls': json.dumps(NEUTRAL_URLS),
            'negative_urls': json.dumps(NEGATIVE_URLS),
            'cues_mapping': json.dumps(cues_mapping),
            "RESPONSE_TIMEOUT":RESPONSE_TIMEOUT,
            # مهم: ارسال لیست توالی‌های باقی‌مانده به کلاینت
            'remaining_sequences': json.dumps(sequence_order),
        }
        return render(request, '1_valence_practice.html', context)
    

    # --- مرحله 2: تمرین تشخیص توالی ---
    PRACTICE_TRIALS = 30
    CATCH_TRIALS_PER_BLOCK = 6
    TOTAL_PER_BLOCK = PRACTICE_TRIALS + CATCH_TRIALS_PER_BLOCK  # 36
    SEQ_THRESHOLD = 0.80
    MAX_BLOCKS = 3

    # پیدا کردن آخرین بلاک استفاده‌شده
    last_practice = (
        PCMSequencePracticeResponse.objects
        .filter(user=user, is_active=True)
        .order_by('-block', '-trial')
        .first()
    )
    last_catch = (
        PCMSequenceCatchResponse.objects
        .filter(user=user, is_active=True)
        .order_by('-block', '-trial')
        .first()
    )

    max_block_practice = last_practice.block if last_practice and last_practice.block else 0
    max_block_catch = last_catch.block if last_catch and last_catch.block else 0
    current_block = max(max_block_practice, max_block_catch, 1)

    def is_block_fully_done(block_num):
        p_count = PCMSequencePracticeResponse.objects.filter(
            user=user, block=block_num, is_active=True
        ).count()
        c_count = PCMSequenceCatchResponse.objects.filter(
            user=user, block=block_num, is_active=True
        ).count()
        return p_count >= PRACTICE_TRIALS and c_count >= CATCH_TRIALS_PER_BLOCK
    
    show_retry_modal = False
    while current_block <= MAX_BLOCKS and is_block_fully_done(current_block):
        # دقت فقط روی کش‌ها محاسبه می‌شود
        c_correct = PCMSequenceCatchResponse.objects.filter(
            user=user, block=current_block, is_active=True, is_correct=True
        ).count()
        accuracy = c_correct / CATCH_TRIALS_PER_BLOCK if CATCH_TRIALS_PER_BLOCK > 0 else 0

        if accuracy >= SEQ_THRESHOLD:
            # این بلاک قبول شده → برو مرحله بعد
            return redirect('/experiment/pcm/')
        else:
            # این بلاک رد شده → برو بلاک بعدی
            show_retry_modal = True
            current_block += 1

    if current_block > MAX_BLOCKS:
        text = "متاسفانه با توجه به نتایج کسب‌شده حائز شرکت در ادامه آزمون نبودید"
        return render(request, 'failed.html', {'text': text})

    # ------------------------------------------------------------------
    # حالا current_block آماده است
    # ------------------------------------------------------------------
    practice_responses = PCMSequencePracticeResponse.objects.filter(
        user=user, block=current_block, is_active=True
    )
    practice_count = practice_responses.count()
    practice_correct = practice_responses.filter(is_correct=True).count()

    catch_responses = PCMSequenceCatchResponse.objects.filter(
        user=user, block=current_block, is_active=True
    )
    catch_count = catch_responses.count()
    catch_correct = catch_responses.filter(is_correct=True).count()

    feedback = FeedbackSettings.objects.first()

    # تعداد کل انجام‌شده در این بلاک (برای progress)
    completed_in_block = practice_count + catch_count
    progress_percentage = (completed_in_block / TOTAL_PER_BLOCK) * 100

    # ========== اگر هنوز تمرین تمام نشده ==========
    if practice_count < PRACTICE_TRIALS:
        remain_trials = PRACTICE_TRIALS - practice_count

        cue_list = list(cues_mapping.keys())
        # اطمینان از اینکه دقیقاً ۳ نشانه داریم
        if len(cue_list) != 3:
            # در صورت نیاز می‌توانید لاگ یا هندلینگ اضافه کنید
            pass

        # شمارش استفاده‌شده تا الان (به ازای هر cue)
        used_per_cue = Counter()
        used_consistent_per_cue = Counter()
        used_inconsistent_seqs_per_cue = defaultdict(Counter)  # cue -> Counter of actual sequences that were inconsistent

        for r in practice_responses:
            if r.cue:
                used_per_cue[r.cue] += 1
                if r.is_consistent:
                    used_consistent_per_cue[r.cue] += 1
                else:
                    # r.category_stim1 و r.category_stim2 را به صورت "Neutral-Negative" در نظر می‌گیریم
                    actual = f"{r.category_stim1}-{r.category_stim2}" if r.category_stim1 and r.category_stim2 else None
                    if actual:
                        used_inconsistent_seqs_per_cue[r.cue][actual] += 1

        remaining_plan = []

        for cue in cue_list:
            mapped = cues_mapping[cue]
            other_seqs = [s for s in ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"] if s != mapped]

            # هدف نهایی به ازای هر cue: ۱۰ تریال
            # ۸ consistent + ۱ از other_seqs[0] + ۱ از other_seqs[1]
            still_need_total = max(0, 10 - used_per_cue[cue])
            still_need_consistent = max(0, 8 - used_consistent_per_cue[cue])
            still_need_incons = {
                other_seqs[0]: max(0, 1 - used_inconsistent_seqs_per_cue[cue][other_seqs[0]]),
                other_seqs[1]: max(0, 1 - used_inconsistent_seqs_per_cue[cue][other_seqs[1]]),
            }

            # اول consistentهای باقی‌مانده
            for _ in range(still_need_consistent):
                remaining_plan.append({
                    "cue": cue,
                    "expected_seq": mapped,
                    "is_consistent": True,
                })

            # بعد inconsistentها
            for seq, need in still_need_incons.items():
                for _ in range(need):
                    remaining_plan.append({
                        "cue": cue,
                        "expected_seq": seq,
                        "is_consistent": False,
                    })

            # اگر به هر دلیلی هنوز کم آمد (مثلاً داده‌های قبلی ناقص بود)
            current_for_this_cue = still_need_consistent + sum(still_need_incons.values())
            while current_for_this_cue < still_need_total:
                remaining_plan.append({
                    "cue": cue,
                    "expected_seq": mapped,
                    "is_consistent": True,
                })
                current_for_this_cue += 1

        # اگر مجموع remaining_plan از remain_trials بیشتر شد، فقط به اندازه remain_trials نگه می‌داریم
        # (نباید اتفاق بیفتد مگر اینکه داده‌های قبلی نامتعادل باشد)
        if len(remaining_plan) > remain_trials:
            random.shuffle(remaining_plan)
            remaining_plan = remaining_plan[:remain_trials]
        elif len(remaining_plan) < remain_trials:
            # پر کردن با consistent تصادفی (ایمنی)
            for _ in range(remain_trials - len(remaining_plan)):
                cue = random.choice(cue_list)
                remaining_plan.append({
                    "cue": cue,
                    "expected_seq": cues_mapping[cue],
                    "is_consistent": True,
                })

        random.shuffle(remaining_plan)

        # قانون ۹ تای اول (فقط اگر از اول بلاک شروع کرده‌ایم)
        if practice_count == 0:
            cons = [t for t in remaining_plan if t["is_consistent"]]
            incons = [t for t in remaining_plan if not t["is_consistent"]]
            random.shuffle(cons)
            random.shuffle(incons)
            first_6 = cons[:6]
            rest = cons[6:] + incons
            random.shuffle(rest)
            remaining_plan = first_6 + rest

        remaining_sequences = [t["expected_seq"] for t in remaining_plan]
        remaining_cues = [t["cue"] for t in remaining_plan]
        remaining_consistent = [t["is_consistent"] for t in remaining_plan]

        # --- پلان catch از قبل (دقیقاً ۲ بار از هر نشانه) ---
        catch_plan = []
        for cue in cue_list:
            catch_plan.extend([cue] * 2)  # دقیقاً ۲ بار هر cue
        random.shuffle(catch_plan)

        # کم کردن cueهایی که قبلاً ثبت شده‌اند
        used_cues = [r.cue for r in catch_responses]
        used_counter = Counter(used_cues)
        final_catch_cues = []
        for cue in catch_plan:
            if used_counter[cue] > 0:
                used_counter[cue] -= 1
            else:
                final_catch_cues.append(cue)

        # اگر هنوز کم بود (نادر)
        while len(final_catch_cues) < CATCH_TRIALS_PER_BLOCK:
            # ترجیحاً از cueهایی که کمتر استفاده شده‌اند
            least_used = min(cue_list, key=lambda c: used_counter[c])
            final_catch_cues.append(least_used)
            used_counter[least_used] += 1
        final_catch_cues = final_catch_cues[:CATCH_TRIALS_PER_BLOCK]

        context = {
            'current_trial': completed_in_block,          # تعداد کل انجام‌شده
            'total_trials': TOTAL_PER_BLOCK,             # همیشه 36
            'trial_number_for_save': practice_count,
            'progress_percentage': round(progress_percentage, 1),
            'cue_urls': json.dumps(CUE_URLS),
            'neutral_urls': json.dumps(NEUTRAL_URLS),
            'negative_urls': json.dumps(NEGATIVE_URLS),
            'cues_mapping': json.dumps(cues_mapping),
            'remaining_sequences': json.dumps(remaining_sequences),
            'remaining_cues': json.dumps(remaining_cues),
            'remaining_consistent': json.dumps(remaining_consistent),
            'catch_cues_plan': json.dumps(final_catch_cues),   # پلان کش از قبل
            'current_block': current_block,
            'is_catch_stage': False,
            'practice_trials_done': practice_count,
            'catch_trials_done': catch_count,

            'feedback_mode': feedback.feedback_mode if feedback else 'always',
            'feedback_first_n': feedback.feedback_first_n if feedback else 5,
            'feedback_until_correct': feedback.feedback_until_correct if feedback else 5,
            'feedback_correct_consecutive': feedback.feedback_correct_consecutive if feedback else False,
            'correct_so_far': practice_correct,
            'show_retry_modal': show_retry_modal,
        }
        return render(request, '2_seq_practice.html', context)

    # ========== مرحله Catch (۶ تریال) - فقط وقتی تمرین تمام شده و صفحه رفرش شده ==========
    if catch_count < CATCH_TRIALS_PER_BLOCK:
        remain_catch = CATCH_TRIALS_PER_BLOCK - catch_count
        cue_list = list(cues_mapping.keys())

        # شمارش دقیق با نرمال‌سازی
        used_cues = []
        for r in catch_responses:
            full = normalize_cue_to_full(r.cue, cues_mapping)
            if full:
                used_cues.append(full)
        used_counter = Counter(used_cues)

        remaining_cues = []
        for cue in cue_list:
            used = used_counter.get(cue, 0)
            still_need = max(0, 2 - used)
            remaining_cues.extend([cue] * still_need)

        # ایمنی
        if len(remaining_cues) < remain_catch:
            for cue in cue_list:
                if used_counter.get(cue, 0) < 2:
                    remaining_cues.append(cue)
                    used_counter[cue] = used_counter.get(cue, 0) + 1
                    if len(remaining_cues) >= remain_catch:
                        break
        elif len(remaining_cues) > remain_catch:
            random.shuffle(remaining_cues)
            remaining_cues = remaining_cues[:remain_catch]

        random.shuffle(remaining_cues)

        context = {
            'current_trial': completed_in_block,
            'total_trials': TOTAL_PER_BLOCK,            
            'trial_number_for_save': catch_count,
            'progress_percentage': round(progress_percentage, 1),
            'cue_urls': json.dumps(CUE_URLS),
            'neutral_urls': json.dumps(NEUTRAL_URLS),
            'negative_urls': json.dumps(NEGATIVE_URLS),
            'cues_mapping': json.dumps(cues_mapping),
            'remaining_sequences': json.dumps([]),
            'remaining_cues': json.dumps(remaining_cues),
            'remaining_consistent': json.dumps([]),
            'catch_cues_plan': json.dumps([]),          
            'current_block': current_block,
            'is_catch_stage': True,
            'practice_trials_done': practice_count,
            'catch_trials_done': catch_count,

            'feedback_mode': feedback.feedback_mode if feedback else 'always',
            'feedback_first_n': feedback.feedback_first_n if feedback else 5,
            'feedback_until_correct': feedback.feedback_until_correct if feedback else 5,
            'feedback_correct_consecutive': feedback.feedback_correct_consecutive if feedback else False,
            'correct_so_far': catch_correct,
            'show_retry_modal': show_retry_modal,
        }
        return render(request, '2_seq_practice.html', context)


    # --- مرحله ۳: آزمون اصلی PCM ---
    NUM_BLOCKS = 3
    CATCH_TRIALS_PER_BLOCK = 6
    MAIN_TRIALS_PER_BLOCK = 14

    # محاسبه بلاک فعلی و پیشرفت کلی
    current_block = None
    all_catch_sequences = {}  # {block_num: [ {cue, expected_seq}, ... ]}
    all_main_trials = {}      # {block_num: [ {actual_seq, cue, expected_seq}, ... ]}

    total_completed = 0
    total_trials_all = NUM_BLOCKS * (CATCH_TRIALS_PER_BLOCK + MAIN_TRIALS_PER_BLOCK)

    # --- تعریف تمام mismatchهای ممکن (۶ ترکیب) برای inconsistent ---
    ALL_MISMATCHES = [
        {"expected_seq": "Neutral-Neutral",  "actual_seq": "Neutral-Negative"},
        {"expected_seq": "Neutral-Neutral",  "actual_seq": "Negative-Neutral"},
        {"expected_seq": "Neutral-Negative", "actual_seq": "Neutral-Neutral"},
        {"expected_seq": "Neutral-Negative", "actual_seq": "Negative-Neutral"},
        {"expected_seq": "Negative-Neutral", "actual_seq": "Neutral-Neutral"},
        {"expected_seq": "Negative-Neutral", "actual_seq": "Neutral-Negative"},
    ]

    # جمع‌آوری mismatchهایی که قبلاً در همه بلاک‌ها استفاده شده‌اند
    used_mismatches = set()
    for r in PCMMainResponse.objects.filter(user=user, is_consistent=False):
        if r.expected_sequence and r.category_stim1 and r.category_stim2:
            actual = f"{r.category_stim1}-{r.category_stim2}"
            used_mismatches.add((r.expected_sequence, actual))

    remaining_mismatches = [
        m for m in ALL_MISMATCHES
        if (m["expected_seq"], m["actual_seq"]) not in used_mismatches
    ]
    random.shuffle(remaining_mismatches)
    mismatch_idx = 0


    try: 
        last_response=PCMMainResponse.objects.filter(user=user).order_by("created_at").last() 
        last_trial=last_response.trial 
        last_block = last_response.block 
    except: 
        last_trial=0 
        last_block=0

    for block_num in range(1, NUM_BLOCKS + 1):
        catch_count = PCMCatchResponse.objects.filter(user=user, block=block_num).count()
        main_count = PCMMainResponse.objects.filter(user=user, block=block_num).count()

        completed_in_block = catch_count + main_count
        total_completed += completed_in_block

        # اگر این بلاک ناتمام است → بلاک فعلی
        if catch_count < CATCH_TRIALS_PER_BLOCK or main_count < MAIN_TRIALS_PER_BLOCK:
            if current_block is None:
                current_block = block_num

        # --- ساخت ترایال‌های catch برای این بلاک (اگر نیاز باشد) ---
        # فقط نشانه (cue) ارائه می‌شود و کاربر توالی مورد انتظار را مشخص می‌کند
        if catch_count < CATCH_TRIALS_PER_BLOCK:
            remain_catch = CATCH_TRIALS_PER_BLOCK - catch_count
            cue_list = list(cues_mapping.keys())

            # شمارش دقیق cueهای استفاده‌شده در این بلاک با نرمال‌سازی
            used_cues = []
            for r in PCMCatchResponse.objects.filter(user=user, block=block_num):
                full = normalize_cue_to_full(r.cue, cues_mapping)
                if full:
                    used_cues.append(full)
            used_counter = Counter(used_cues)

            # ساخت لیست باقی‌مانده: حداکثر ۲ تا از هر نشانه
            remaining_cues = []
            for cue in cue_list:
                used = used_counter.get(cue, 0)
                still_need = max(0, 2 - used)
                remaining_cues.extend([cue] * still_need)

            # ایمنی در برابر داده‌های ناقص یا بیش از حد
            if len(remaining_cues) < remain_catch:
                # اگر به هر دلیلی کمتر بود، از نشانه‌هایی که هنوز کمتر از ۲ دارند پر کن
                for cue in cue_list:
                    if used_counter.get(cue, 0) < 2:
                        remaining_cues.append(cue)
                        used_counter[cue] = used_counter.get(cue, 0) + 1
                        if len(remaining_cues) >= remain_catch:
                            break
            elif len(remaining_cues) > remain_catch:
                random.shuffle(remaining_cues)
                remaining_cues = remaining_cues[:remain_catch]

            random.shuffle(remaining_cues)

            # تبدیل به فرمت مورد نیاز (با expected_seq)
            catch_trials = []
            for cue in remaining_cues:
                catch_trials.append({
                    'cue': cue,
                    'expected_seq': cues_mapping.get(cue),
                })

            all_catch_sequences[block_num] = catch_trials
            
        # --- ساخت توالی‌های main برای این بلاک (اگر نیاز باشد) ---
        if main_count < MAIN_TRIALS_PER_BLOCK:
            remain_main = MAIN_TRIALS_PER_BLOCK - main_count

            # تعداد inconsistent باقی‌مانده در این بلاک (هدف: ۲ تا در هر بلاک)
            used_inconsistent_in_block = PCMMainResponse.objects.filter(
                user=user, block=block_num, is_consistent=False
            ).count()
            remain_inconsistent = max(0, 2 - used_inconsistent_in_block)
            remain_consistent = remain_main - remain_inconsistent

            final_trials = []

            # --- inconsistentها از لیست سراسری (۶ ترکیب متعادل در ۳ بلاک) ---
            for _ in range(remain_inconsistent):
                if mismatch_idx < len(remaining_mismatches):
                    m = remaining_mismatches[mismatch_idx]
                    mismatch_idx += 1
                    expected_seq = m["expected_seq"]
                    actual_seq = m["actual_seq"]
                else:
                    # fallback (نباید اتفاق بیفتد)
                    expected_seq = random.choice(["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"])
                    possibles = [s for s in ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"] if s != expected_seq]
                    actual_seq = random.choice(possibles)

                cue_candidates = [c for c, exp in cues_mapping.items() if exp == expected_seq]
                cue = random.choice(cue_candidates) if cue_candidates else random.choice(CUE_URLS)

                final_trials.append({
                    'actual_seq': actual_seq,
                    'cue': cue,
                    'expected_seq': expected_seq,
                })

            # --- consistentها با تعادل بین ۳ توالی ---
            ALL_POSSIBLE_SEQUENCES = ["Neutral-Neutral", "Negative-Neutral", "Neutral-Negative"]

            cons_counts = Counter([
                f"{r.category_stim1}-{r.category_stim2}"
                for r in PCMMainResponse.objects.filter(user=user, block=block_num, is_consistent=True)
                if r.category_stim1 and r.category_stim2
            ])

            for _ in range(remain_consistent):
                weights = [
                    max(0, (remain_consistent // 3) - cons_counts.get(seq, 0))
                    for seq in ALL_POSSIBLE_SEQUENCES
                ]
                if sum(weights) == 0:
                    seq = random.choice(ALL_POSSIBLE_SEQUENCES)
                else:
                    seq = random.choices(ALL_POSSIBLE_SEQUENCES, weights=weights, k=1)[0]

                cue_candidates = [c for c, exp in cues_mapping.items() if exp == seq]
                cue = random.choice(cue_candidates) if cue_candidates else random.choice(CUE_URLS)

                final_trials.append({
                    'actual_seq': seq,
                    'cue': cue,
                    'expected_seq': seq,
                })
                cons_counts[seq] += 1

            random.shuffle(final_trials)
            all_main_trials[block_num] = final_trials

    progress_percentage = (total_completed / total_trials_all) * 100 if total_trials_all > 0 else 0

    # اگر همه بلاک‌ها تمام شد → به مرحله بعدی برو
    if current_block is None:
        # ادامه کد مراحل بعدی (rating practice و ...)
        pass
    else:
        
        context = {
            'current_block': current_block,
            'total_blocks': NUM_BLOCKS,
            'catch_trials_per_block': CATCH_TRIALS_PER_BLOCK,
            'trials_per_block': MAIN_TRIALS_PER_BLOCK,
            'progress_percentage': round(progress_percentage, 1),
            'completed': total_completed,
            'trials': total_trials_all,

            'cue_urls': json.dumps(CUE_URLS),
            'neutral_urls': json.dumps(NEUTRAL_URLS),
            'negative_urls': json.dumps(NEGATIVE_URLS),
            'cues_mapping': json.dumps(cues_mapping),

            'last_trial':last_trial,
            'last_block':last_block,
            'next_block':last_block + 1,
            # مهم: تمام داده‌های همه بلاک‌ها
            'all_catch_sequences': json.dumps(all_catch_sequences),
            'all_main_trials': json.dumps(all_main_trials),
        }
        return render(request, '3_pcm_main.html', context)
    

    # --- مرحله 4: تمرین رتبه بندی خوشایندی و برانگیختگی---
    RATING_PRACTICE_TRIALS = 10
    PRACTICE_FILES_RAW = [
        '0-practice/1.mp3',
        '0-practice/2.mp3',
        '0-practice/3.mp3',
        '0-practice/4.mp3',
        '0-practice/5.mp3',
        '0-practice/6.mp3',
        '0-practice/7.mp3',
        '0-practice/8.mp3',
        '0-practice/9.mp3',
        '0-practice/10.mp3',
    ]
    practice_files = [build_audio_url(f) for f in PRACTICE_FILES_RAW[:RATING_PRACTICE_TRIALS]]
    rating_practice_count = RatingPracticeResponse.objects.filter(user=user).count()
    progress_percentage = (rating_practice_count / RATING_PRACTICE_TRIALS) * 100
    if rating_practice_count < RATING_PRACTICE_TRIALS:
        remaining_files = practice_files[rating_practice_count:]
        context = {
            'current_trial': rating_practice_count + 1,
            'count':rating_practice_count,
            'total_trials': RATING_PRACTICE_TRIALS,
            'progress_percentage': progress_percentage,
            'remaining_practice_files': json.dumps(remaining_files),
        }
        return render(request, '4_rating_practice.html', context)

    # --- مرحله ۵: رتبه‌بندی  همه صداهای ارائه شده (خوشایندی و برانگیختگی) ---
    MAIN_RATING_FILES_RAW = [
        '5-MP-MA/102.mp3',
        '5-MP-MA/152.mp3',
        '5-MP-MA/170.mp3',
        '5-MP-MA/246.mp3',
        '5-MP-MA/320.mp3',
        '5-MP-MA/322.mp3',
        '5-MP-MA/358.mp3',
        '5-MP-MA/361.mp3',
        '5-MP-MA/364.mp3',
        '5-MP-MA/368.mp3',
        '5-MP-MA/370.mp3',
        '5-MP-MA/373.mp3',
        '5-MP-MA/374.mp3',
        '5-MP-MA/375.mp3',
        '5-MP-MA/376.mp3',
        '5-MP-MA/382.mp3',
        '5-MP-MA/403.mp3',
        '5-MP-MA/410.mp3',
        '5-MP-MA/425.mp3',
        '5-MP-MA/698.mp3',
        '5-MP-MA/701.mp3',
        '5-MP-MA/705.mp3',
        '5-MP-MA/722.mp3',
        '5-MP-MA/724.mp3',
        '7-LP-HA/106.mp3',
        '7-LP-HA/115.mp3',
        '7-LP-HA/116.mp3',
        '7-LP-HA/133.mp3',
        '7-LP-HA/244.mp3',
        '7-LP-HA/255.mp3',
        '7-LP-HA/260.mp3',
        '7-LP-HA/261.mp3',
        '7-LP-HA/275.mp3',
        '7-LP-HA/276.mp3',
        '7-LP-HA/277.mp3',
        '7-LP-HA/278.mp3',
        '7-LP-HA/279.mp3',
        '7-LP-HA/282.mp3',
        '7-LP-HA/283.mp3',
        '7-LP-HA/284.mp3',
        '7-LP-HA/285.mp3',
        '7-LP-HA/286.mp3',
        '7-LP-HA/288.mp3',
        '7-LP-HA/289.mp3',
        '7-LP-HA/290.mp3',
        '7-LP-HA/292.mp3',
        '7-LP-HA/296.mp3',
        '7-LP-HA/310.mp3',
        '7-LP-HA/380.mp3',
        '7-LP-HA/420.mp3',
        '7-LP-HA/422.mp3',
        '7-LP-HA/423.mp3',
        '7-LP-HA/424.mp3',
        '7-LP-HA/501.mp3',
        '7-LP-HA/502.mp3',
        '7-LP-HA/600.mp3',
        '7-LP-HA/624.mp3',
        '7-LP-HA/625.mp3',
        '7-LP-HA/626.mp3',
        '7-LP-HA/699.mp3',
        '7-LP-HA/711.mp3',
        '7-LP-HA/712.mp3',
        '7-LP-HA/713.mp3',
        '7-LP-HA/714.mp3',
        '7-LP-HA/730.mp3',
        '7-LP-HA/732.mp3',
        '8-LP-MA/241.mp3',
        '8-LP-MA/242.mp3',
        '8-LP-MA/280.mp3',
        '8-LP-MA/293.mp3',
        '8-LP-MA/295.mp3',
        '8-LP-MA/611.mp3',
    ]

    # حذف تکراری‌ها
    MAIN_RATING_FILES_RAW = list(set(MAIN_RATING_FILES_RAW))
    # تبدیل به URL کامل
    main_rating_files = [build_audio_url(f) for f in MAIN_RATING_FILES_RAW]
    # تعداد کل محرک‌ها
    TOTAL_MAIN_RATING_TRIALS = len(main_rating_files)
    # تعداد رتبه‌بندی‌های تکمیل‌شده (هر دو valence و arousal پر باشند)
    rating_main_done = RatingMainResponse.objects.filter(
        user=user
    ).exclude(
        valence__isnull=True
    ).exclude(
        arousal__isnull=True
    ).count()

    progress_percentage = (rating_main_done / TOTAL_MAIN_RATING_TRIALS) * 100 if TOTAL_MAIN_RATING_TRIALS > 0 else 100
    if rating_main_done < TOTAL_MAIN_RATING_TRIALS:
        completed_stimuli_urls = set(
            RatingMainResponse.objects.filter(
                user=user,
                valence__isnull=False,
                arousal__isnull=False
            ).values_list('stimulus_file', flat=True)
        )

        remaining_files = [f for f in main_rating_files if f not in completed_stimuli_urls]
        random.shuffle(remaining_files)

        context = {
            'current_trial': rating_main_done + 1,
            'count':rating_main_done,
            'total_trials': TOTAL_MAIN_RATING_TRIALS,
            'progress_percentage': progress_percentage,
            'remaining_main_files': json.dumps(remaining_files),
        }
        return render(request, '5_rating_main.html', context)

    # --- پایان آزمون ---
    return redirect('/final/')


@csrf_exempt
def pcm_save_response(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'فقط POST'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON نامعتبر'}, status=400)

    user = request.user
    # مرحله 1: تمرین رتبه‌بندی خوشایندی
    if data.get('is_valence_practice'):
            PCMValencePracticeResponse.objects.create(
                user=user,
                trial=data['trial'],
                cue=extract_stimulus_number(data['cue']),
                stimulus1=extract_stimulus_number(data.get('stimulus1')),
                stimulus2=extract_stimulus_number(data.get('stimulus2')),
                category_stim1=data.get('category_stim1'),
                category_stim2=data.get('category_stim2'),
                valence_stim1=data.get('valence_stim1'),
                valence_rt_stim1=data.get('valence_rt_stim1') or data.get('rt_stim1'),
                valence_delay_number_stim1=data.get('valence_delay_number_stim1', 0),
                valence_input_method_stim1=data.get('valence_input_method_stim1'),
                valence_stim2=data.get('valence_stim2'),
                valence_rt_stim2=data.get('valence_rt_stim2') or data.get('rt_stim2'),
                valence_delay_number_stim2=data.get('valence_delay_number_stim2', 0),
                valence_input_method_stim2=data.get('valence_input_method_stim2'),
                valence_sequence=data.get('valence_sequence'),
                valence_rt_sequence=data.get('valence_rt_sequence') or data.get('rt_sequence'),
                valence_delay_number_sequence=data.get('valence_delay_number_sequence', 0),
                valence_input_method_sequence=data.get('valence_input_method_sequence'),
            )
    # مرحله 2: تمرین تشخیص توالی
    elif data.get('is_catch'):
        PCMSequenceCatchResponse.objects.create(
            user=request.user,
            block=data.get('block', 1),
            trial=data['trial'],
            cue=extract_stimulus_number(data['cue']),
            user_response=data['user_response'],
            response_rt=data.get('response_rt'),
            delay_number=data.get('delay_number', 0),
            response_input_method=data.get('response_input_method'),
            is_correct=data.get('is_correct'),
        )
    
    elif data.get('is_seq_practice'):
        
        PCMSequencePracticeResponse.objects.create(
            user=user,
            trial=data['trial'] ,
            block=data.get('block', 1),
            cue=extract_stimulus_number(data['cue']),
            stimulus1=extract_stimulus_number(data.get('stimulus1')),
            stimulus2=extract_stimulus_number(data.get('stimulus2')),
            category_stim1=data.get('category_stim1'),
            category_stim2=data.get('category_stim2'),
            expected_sequence=data.get('expected_sequence'),
            user_response=data['user_response'],
            response_rt=data['response_rt'],
            delay_number=data['delay_number'],
            response_input_method=data['response_input_method'],
            is_correct=data['is_correct'],
            is_consistent=data.get('is_consistent', True),
        )

    # مرحله ۳: آزمون اصلی
    elif data.get('is_catch_pcm'):
        PCMCatchResponse.objects.create(
            user=user,
            block=data.get('block', None),
            trial=data['trial'],
            cue=extract_stimulus_number(data['cue']),
            user_response=data.get('user_response'),
            response_rt=data['response_rt'],
            delay_number=data.get('delay_number', 0),
            response_input_method=data.get('response_input_method'),
            is_correct=data.get('is_correct')
        )

    # در create برای main، اضافه کردن category_stim1 و category_stim2
    elif 'block' in data and 'trial' in data and not data.get('is_catch'):
        PCMMainResponse.objects.create(
            user=user,
            block=data['block'],
            trial=data['trial'],
            cue=extract_stimulus_number(data['cue']),
            stimulus1=extract_stimulus_number(data.get('stimulus1')),
            stimulus2=extract_stimulus_number(data.get('stimulus2')),
            expected_sequence=data.get('expected_sequence'),
            is_consistent=data.get('is_consistent', True),
            category_stim1=data.get('category_stim1'),
            category_stim2=data.get('category_stim2'),
            valence_stim1=data.get('valence_stim1'),
            valence_rt_stim1=data.get('valence_rt_stim1'),
            valence_delay_number_stim1=data.get('valence_delay_number_stim1', 0),
            valence_input_method_stim1=data.get('valence_input_method_stim1'),
            valence_stim2=data.get('valence_stim2'),
            valence_rt_stim2=data.get('valence_rt_stim2'),
            valence_delay_number_stim2=data.get('valence_delay_number_stim2', 0),
            valence_input_method_stim2=data.get('valence_input_method_stim2'),
            valence_sequence=data.get('valence_sequence'),
            valence_rt_sequence=data.get('valence_rt_sequence'),
            valence_delay_number_sequence=data.get('valence_delay_number_sequence', 0),
            valence_input_method_sequence=data.get('valence_input_method_sequence'),
        )

    # مرحله ۴: تمرین رتبه‌بندی کامل
    elif data.get('is_rating_practice'):
        RatingPracticeResponse.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus')),
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            valence_delay_number = data.get('valence_delay_number', 0),
            valence_input_method=data.get('valence_input_method'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
            arousal_delay_number = data.get('arousal_delay_number', 0),
            arousal_input_method=data.get('arousal_input_method'),
        )

    # مرحله ۵: رتبه‌بندی نهایی
    elif data.get('is_rerating'):
        RatingMainResponse.objects.create(
            user=user,
            trial=data['trial'],
            stimulus_number=extract_stimulus_number(data.get('stimulus_number')),
            stimulus_file=data['stimulus_file'],
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            valence_delay_number = data.get('valence_delay_number', 0),
            valence_input_method=data.get('valence_input_method'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
            arousal_delay_number = data.get('arousal_delay_number', 0),
            arousal_input_method=data.get('arousal_input_method'),
        )

    else:
        return JsonResponse({'status': 'error', 'message': 'نوع داده نامعتبر'}, status=400)

    return JsonResponse({'status': 'success'})


def final_view(request):
    user = request.user
    PCM_FILES_RAW = [
        '5-MP-MA/102.mp3',
        '5-MP-MA/152.mp3',
        '5-MP-MA/170.mp3',
        '5-MP-MA/246.mp3',
        '5-MP-MA/320.mp3',
        '5-MP-MA/322.mp3',
        '5-MP-MA/358.mp3',
        '5-MP-MA/361.mp3',
        '5-MP-MA/364.mp3',
        '5-MP-MA/368.mp3',
        '5-MP-MA/370.mp3',
        '5-MP-MA/373.mp3',
        '5-MP-MA/374.mp3',
        '5-MP-MA/375.mp3',
        '5-MP-MA/376.mp3',
        '5-MP-MA/382.mp3',
        '5-MP-MA/403.mp3',
        '5-MP-MA/410.mp3',
        '5-MP-MA/425.mp3',
        '5-MP-MA/698.mp3',
        '5-MP-MA/701.mp3',
        '5-MP-MA/705.mp3',
        '5-MP-MA/722.mp3',
        '5-MP-MA/724.mp3',
        '7-LP-HA/106.mp3',
        '7-LP-HA/115.mp3',
        '7-LP-HA/116.mp3',
        '7-LP-HA/133.mp3',
        '7-LP-HA/244.mp3',
        '7-LP-HA/255.mp3',
        '7-LP-HA/260.mp3',
        '7-LP-HA/261.mp3',
        '7-LP-HA/275.mp3',
        '7-LP-HA/276.mp3',
        '7-LP-HA/277.mp3',
        '7-LP-HA/278.mp3',
        '7-LP-HA/279.mp3',
        '7-LP-HA/282.mp3',
        '7-LP-HA/283.mp3',
        '7-LP-HA/284.mp3',
        '7-LP-HA/285.mp3',
        '7-LP-HA/286.mp3',
        '7-LP-HA/288.mp3',
        '7-LP-HA/289.mp3',
        '7-LP-HA/290.mp3',
        '7-LP-HA/292.mp3',
        '7-LP-HA/296.mp3',
        '7-LP-HA/310.mp3',
        '7-LP-HA/380.mp3',
        '7-LP-HA/420.mp3',
        '7-LP-HA/422.mp3',
        '7-LP-HA/423.mp3',
        '7-LP-HA/424.mp3',
        '7-LP-HA/501.mp3',
        '7-LP-HA/502.mp3',
        '7-LP-HA/600.mp3',
        '7-LP-HA/624.mp3',
        '7-LP-HA/625.mp3',
        '7-LP-HA/626.mp3',
        '7-LP-HA/699.mp3',
        '7-LP-HA/711.mp3',
        '7-LP-HA/712.mp3',
        '7-LP-HA/713.mp3',
        '7-LP-HA/714.mp3',
        '7-LP-HA/730.mp3',
        '7-LP-HA/732.mp3',
        '8-LP-MA/241.mp3',
        '8-LP-MA/242.mp3',
        '8-LP-MA/280.mp3',
        '8-LP-MA/293.mp3',
        '8-LP-MA/295.mp3',
        '8-LP-MA/611.mp3',
    ]

    # حذف تکراری‌ها
    PCM_FILES_RAW = list(set(PCM_FILES_RAW))
    main_pcm_files = [build_audio_url(f) for f in PCM_FILES_RAW]
    TOTAL_MAIN_PCM_TRIALS = len(main_pcm_files)
    rating_pcm_done = RatingMainResponse.objects.filter(
        user=user
    ).exclude(
        valence__isnull=True
    ).exclude(
        arousal__isnull=True
    ).count()
    PCM_percentage = (rating_pcm_done / TOTAL_MAIN_PCM_TRIALS) * 100 if TOTAL_MAIN_PCM_TRIALS > 0 else 100
    print(PCM_percentage)
    if PCM_percentage == 100 :
        pcm_completed = True
    else:
        pcm_completed = False

    RATING_FILES_RAW = [
        '1-HP-HA/110.mp3','1-HP-HA/200.mp3','1-HP-HA/201.mp3','1-HP-HA/202.mp3','1-HP-HA/205.mp3','1-HP-HA/215.mp3','1-HP-HA/220.mp3','1-HP-HA/311.mp3','1-HP-HA/352.mp3','1-HP-HA/353.mp3','1-HP-HA/355.mp3','1-HP-HA/360.mp3','1-HP-HA/363.mp3','1-HP-HA/365.mp3','1-HP-HA/366.mp3','1-HP-HA/367.mp3','1-HP-HA/378.mp3','1-HP-HA/415.mp3','1-HP-HA/716.mp3','1-HP-HA/717.mp3','1-HP-HA/808.mp3','1-HP-HA/815.mp3','1-HP-HA/817.mp3',
        '2-HP-MA/109.mp3','2-HP-MA/111.mp3','2-HP-MA/112.mp3','2-HP-MA/150.mp3','2-HP-MA/151.mp3','2-HP-MA/206.mp3','2-HP-MA/221.mp3','2-HP-MA/224.mp3','2-HP-MA/226.mp3','2-HP-MA/230.mp3','2-HP-MA/254.mp3','2-HP-MA/270.mp3','2-HP-MA/351.mp3','2-HP-MA/400.mp3','2-HP-MA/601.mp3','2-HP-MA/721.mp3','2-HP-MA/725.mp3','2-HP-MA/726.mp3','2-HP-MA/802.mp3','2-HP-MA/810.mp3','2-HP-MA/811.mp3','2-HP-MA/813.mp3','2-HP-MA/816.mp3','2-HP-MA/820.mp3','2-HP-MA/826.mp3',
        '3-HP-LA/172.mp3','3-HP-LA/809.mp3','3-HP-LA/812.mp3',
        '4-MP-HA/114.mp3','4-MP-HA/204.mp3','4-MP-HA/210.mp3','4-MP-HA/216.mp3','4-MP-HA/610.mp3','4-MP-HA/704.mp3','4-MP-HA/710.mp3','4-MP-HA/715.mp3',
        '5-MP-MA/102.mp3','5-MP-MA/104.mp3','5-MP-MA/107.mp3','5-MP-MA/111.mp3','5-MP-MA/113.mp3','5-MP-MA/120.mp3','5-MP-MA/130.mp3','5-MP-MA/132.mp3','5-MP-MA/152.mp3','5-MP-MA/170.mp3','5-MP-MA/225.mp3','5-MP-MA/245.mp3','5-MP-MA/246.mp3','5-MP-MA/251.mp3','5-MP-MA/252.mp3','5-MP-MA/320.mp3','5-MP-MA/322.mp3','5-MP-MA/358.mp3','5-MP-MA/361.mp3','5-MP-MA/364.mp3','5-MP-MA/368.mp3','5-MP-MA/370.mp3','5-MP-MA/373.mp3','5-MP-MA/374.mp3','5-MP-MA/375.mp3','5-MP-MA/376.mp3','5-MP-MA/382.mp3','5-MP-MA/403.mp3','5-MP-MA/410.mp3','5-MP-MA/425.mp3','5-MP-MA/500.mp3','5-MP-MA/627.mp3','5-MP-MA/698.mp3','5-MP-MA/700.mp3','5-MP-MA/701.mp3','5-MP-MA/702.mp3','5-MP-MA/705.mp3','5-MP-MA/706.mp3','5-MP-MA/720.mp3','5-MP-MA/722.mp3','5-MP-MA/723.mp3','5-MP-MA/724.mp3','5-MP-MA/728.mp3','5-MP-MA/729.mp3',
        '6-MP-LA/171.mp3','6-MP-LA/262.mp3','6-MP-LA/377.mp3','6-MP-LA/602.mp3','6-MP-LA/708.mp3',
        '7-LP-HA/105.mp3','7-LP-HA/106.mp3','7-LP-HA/115.mp3','7-LP-HA/116.mp3','7-LP-HA/133.mp3','7-LP-HA/134.mp3','7-LP-HA/244.mp3','7-LP-HA/255.mp3','7-LP-HA/260.mp3','7-LP-HA/261.mp3','7-LP-HA/275.mp3','7-LP-HA/276.mp3','7-LP-HA/277.mp3','7-LP-HA/278.mp3','7-LP-HA/279.mp3','7-LP-HA/281.mp3','7-LP-HA/282.mp3','7-LP-HA/283.mp3','7-LP-HA/284.mp3','7-LP-HA/285.mp3','7-LP-HA/286.mp3','7-LP-HA/288.mp3','7-LP-HA/289.mp3','7-LP-HA/290.mp3','7-LP-HA/292.mp3','7-LP-HA/296.mp3','7-LP-HA/310.mp3','7-LP-HA/312.mp3','7-LP-HA/319.mp3','7-LP-HA/380.mp3','7-LP-HA/420.mp3','7-LP-HA/422.mp3','7-LP-HA/423.mp3','7-LP-HA/424.mp3','7-LP-HA/501.mp3','7-LP-HA/502.mp3','7-LP-HA/600.mp3','7-LP-HA/624.mp3','7-LP-HA/625.mp3','7-LP-HA/626.mp3','7-LP-HA/699.mp3','7-LP-HA/709.mp3','7-LP-HA/711.mp3','7-LP-HA/712.mp3','7-LP-HA/713.mp3','7-LP-HA/714.mp3','7-LP-HA/719.mp3','7-LP-HA/730.mp3','7-LP-HA/732.mp3','7-LP-HA/910.mp3',
        '8-LP-MA/241.mp3','8-LP-MA/242.mp3','8-LP-MA/243.mp3','8-LP-MA/250.mp3','8-LP-MA/280.mp3','8-LP-MA/293.mp3','8-LP-MA/295.mp3','8-LP-MA/611.mp3','8-LP-MA/703.mp3',
    ]

    # حذف تکراری‌ها
    RATING_FILES_RAW = list(set(RATING_FILES_RAW))
    # تبدیل به URL کامل
    main_rating_files = [build_audio_url(f) for f in RATING_FILES_RAW]
    # تعداد کل محرک‌ها
    TOTAL_MAIN_RATING_TRIALS = len(main_rating_files)
    # تعداد رتبه‌بندی‌های تکمیل‌شده (هر دو valence و arousal پر باشند)
    rating_main_done = RatingResponse.objects.filter(
        user=user
    ).exclude(
        valence__isnull=True
    ).exclude(
        arousal__isnull=True
    ).count()
    rating_percentage = (rating_main_done / TOTAL_MAIN_RATING_TRIALS) * 100 if TOTAL_MAIN_RATING_TRIALS > 0 else 100
    if rating_percentage == 100 :
        rating_completed = True
    else:
        rating_completed = False
    return render(request, 'final_thanks.html',{
        'pcm_completed':pcm_completed,
        'rating_completed':rating_completed,
    })


def result_view(request):
    return render(request, 'result.html')


def pcm_result_view(request):
    users = CustomUser.objects.all().order_by('id')
    data = {
        'users': [],
        'rates': [],
    }

    ratingresponse = (
        RatingMainResponse.objects
        .values('stimulus_number', 'stimulus_file')
        .annotate(
            avg_valence=Avg('valence'),
            avg_valence_rt=Avg('valence_rt'),
            avg_arousal=Avg('arousal'),
            avg_arousal_rt=Avg('arousal_rt'),
            n_responses=Count('id'),
        )
        .order_by('stimulus_number')
    )
    
    for rate in ratingresponse:
        
        rate_data = {
            'stimulus': rate['stimulus_number'],
            'N': rate['n_responses'],
            'stimulus_file': rate['stimulus_file'][17:22],
            'valence': round(rate['avg_valence'] or 0, 2),
            'valence_rt': round(rate['avg_valence_rt'] or 0, 2),
            'arousal': round(rate['avg_arousal'] or 0, 2),
            'arousal_rt': round(rate['avg_arousal_rt'] or 0, 2),
        }
        data['rates'].append(rate_data)

    for user in users:
        results = Result.objects.filter(user=user)
        rating_response = RatingMainResponse.objects.filter(user=user)
        PCM_main_response = PCMMainResponse.objects.filter(user=user)

        # --- محاسبه میانگین‌های کلی (از RatingMainResponse) ---
        avg_data = rating_response.aggregate(
            avg_valence=Avg('valence'),
            avg_valence_rt=Avg('valence_rt'),
            avg_arousal=Avg('arousal'),
            avg_arousal_rt=Avg('arousal_rt'),
            n_responses=Count('id'),
        )

        # --- محاسبه میانگین‌های PCM بر اساس انتظار ---
        pcm_expected = PCM_main_response.filter(is_consistent=True).aggregate(
            n_responses=Count('id'),
            avg_valence_stim1=Avg('valence_stim1'),
            avg_valence_rt_stim1=Avg('valence_rt_stim1'),
            avg_valence_stim2=Avg('valence_stim2'),
            avg_valence_rt_stim2=Avg('valence_rt_stim2'),
            avg_valence_sequence=Avg('valence_sequence'),
            avg_valence_rt_sequence=Avg('valence_rt_sequence'),
        )

        pcm_unexpected = PCM_main_response.filter(is_consistent=False).aggregate(
            n_responses=Count('id'),
            avg_valence_stim1=Avg('valence_stim1'),
            avg_valence_rt_stim1=Avg('valence_rt_stim1'),
            avg_valence_stim2=Avg('valence_stim2'),
            avg_valence_rt_stim2=Avg('valence_rt_stim2'),
            avg_valence_sequence=Avg('valence_sequence'),
            avg_valence_rt_sequence=Avg('valence_rt_sequence'),
        )

        if PCM_main_response :
            user_data = {
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'mobile': user.username,
                'birth_date': convert_birth_to_jalali_view(user),
                'age': calculate_age_view(user),
                'gender': dict(CustomUser.GENDER_CHOICES).get(user.gender, 'نامشخص'),
                'hand': dict(CustomUser.HAND_CHOICES).get(user.hand, 'نامشخص'),
                'disorder': user.disorder,
                'drug': user.drug,

                # داده‌های RatingMainResponse
                'n_responses': avg_data['n_responses'],
                'avg_valence': round(avg_data['avg_valence'] or 0, 2),
                'avg_valence_rt': round(avg_data['avg_valence_rt'] or 0, 2),
                'avg_arousal': round(avg_data['avg_arousal'] or 0, 2),
                'avg_arousal_rt': round(avg_data['avg_arousal_rt'] or 0, 2),

                # داده‌های PCM (قابل انتظار)
                'pcm_expected_count': pcm_expected['n_responses'],
                'pcm_expected_valence_stim1': round(pcm_expected['avg_valence_stim1'] or 0, 2),
                'pcm_expected_valence_rt_stim1': round(pcm_expected['avg_valence_rt_stim1'] or 0, 2),
                'pcm_expected_valence_stim2': round(pcm_expected['avg_valence_stim2'] or 0, 2),
                'pcm_expected_valence_rt_stim2': round(pcm_expected['avg_valence_rt_stim2'] or 0, 2),
                'pcm_expected_valence_seq': round(pcm_expected['avg_valence_sequence'] or 0, 2),
                'pcm_expected_valence_rt_seq': round(pcm_expected['avg_valence_rt_sequence'] or 0, 2),

                # داده‌های PCM (غیرقابل انتظار)
                'pcm_unexpected_count': pcm_unexpected['n_responses'],
                'pcm_unexpected_valence_stim1': round(pcm_unexpected['avg_valence_stim1'] or 0, 2),
                'pcm_unexpected_valence_rt_stim1': round(pcm_unexpected['avg_valence_rt_stim1'] or 0, 2),
                'pcm_unexpected_valence_stim2': round(pcm_unexpected['avg_valence_stim2'] or 0, 2),
                'pcm_unexpected_valence_rt_stim2': round(pcm_unexpected['avg_valence_rt_stim2'] or 0, 2),
                'pcm_unexpected_valence_seq': round(pcm_unexpected['avg_valence_sequence'] or 0, 2),
                'pcm_unexpected_valence_rt_seq': round(pcm_unexpected['avg_valence_rt_sequence'] or 0, 2),

                'rating_response': rating_response,
                'results': results,
            }

            data['users'].append(user_data)

    return render(request, 'pcm_result.html', data)

def rating_result_view(request):
    users = CustomUser.objects.all().order_by('id')
    data = {
        'users': [],
        'rates': [],
    }
    ratingresponse = (
        RatingResponse.objects
        .values('stimulus', 'stimulus_file')
        .annotate(
            avg_valence=Avg('valence'),
            avg_valence_rt=Avg('valence_rt'),
            avg_arousal=Avg('arousal'),
            avg_arousal_rt=Avg('arousal_rt'),
            n_responses=Count('id'),
        )
        .order_by('stimulus')
    )
    
    for rate in ratingresponse:
        
        rate_data = {
            'stimulus': rate['stimulus'],
            'N': rate['n_responses'],
            'stimulus_file': rate['stimulus_file'][17:22],
            'valence': round(rate['avg_valence'] or 0, 2),
            'valence_rt': round(rate['avg_valence_rt'] or 0, 2),
            'arousal': round(rate['avg_arousal'] or 0, 2),
            'arousal_rt': round(rate['avg_arousal_rt'] or 0, 2),
        }
        data['rates'].append(rate_data)

    for user in users:
        results = Result.objects.filter(user=user)
        rating_response = RatingResponse.objects.filter(user=user)
        
        avg_data = rating_response.aggregate(
            avg_valence=Avg('valence'),
            avg_valence_rt=Avg('valence_rt'),
            avg_arousal=Avg('arousal'),
            avg_arousal_rt=Avg('arousal_rt'),
            n_responses=Count('id'),
        )
        if rating_response :
            user_data = {
                'name': user.get_full_name() or user.username,
                'email': user.email,
                'mobile': user.username,
                'birth_date': convert_birth_to_jalali_view(user),
                'age': calculate_age_view(user),
                'gender': dict(CustomUser.GENDER_CHOICES).get(user.gender, 'نامشخص'),
                'hand': dict(CustomUser.HAND_CHOICES).get(user.hand, 'نامشخص'),
                'disorder': user.disorder,
                'drug': user.drug,
                'n_responses': avg_data['n_responses'],
                'avg_valence': round(avg_data['avg_valence'] or 0, 2),
                'avg_valence_rt': round(avg_data['avg_valence_rt'] or 0, 2),
                'avg_arousal': round(avg_data['avg_arousal'] or 0, 2),
                'avg_arousal_rt': round(avg_data['avg_arousal_rt'] or 0, 2),
                'rating_response': rating_response,
                'results': results,
            }
            data['users'].append(user_data)

    return render(request, 'rating_result.html', data)