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
import datetime
from django.db.models import Avg, Count


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
            user = CustomUser.objects.create(
                username=username,
                birth_date=form.cleaned_data['birth_date'],
                gender=form.cleaned_data['gender'],
                hand=form.cleaned_data['hand'],
                disorder=form.cleaned_data['disorder'],
                drug=form.cleaned_data['drug'],
            )
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
        'username': username
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
        '1-HP-HA/110.WAV','1-HP-HA/200.WAV','1-HP-HA/201.WAV','1-HP-HA/202.WAV','1-HP-HA/205.WAV','1-HP-HA/215.WAV','1-HP-HA/220.WAV','1-HP-HA/311.WAV','1-HP-HA/352.WAV','1-HP-HA/353.WAV','1-HP-HA/355.WAV','1-HP-HA/360.WAV','1-HP-HA/363.WAV','1-HP-HA/365.WAV','1-HP-HA/366.WAV','1-HP-HA/367.WAV','1-HP-HA/378.WAV','1-HP-HA/415.WAV','1-HP-HA/716.WAV','1-HP-HA/717.WAV','1-HP-HA/808.WAV','1-HP-HA/815.WAV','1-HP-HA/817.WAV',

        '2-HP-MA/109.WAV','2-HP-MA/111.WAV','2-HP-MA/112.WAV','2-HP-MA/150.WAV','2-HP-MA/151.WAV','2-HP-MA/206.WAV','2-HP-MA/221.WAV','2-HP-MA/224.WAV','2-HP-MA/226.WAV','2-HP-MA/230.WAV','2-HP-MA/254.WAV','2-HP-MA/270.WAV','2-HP-MA/351.WAV','2-HP-MA/400.WAV','2-HP-MA/601.WAV','2-HP-MA/721.WAV','2-HP-MA/725.WAV','2-HP-MA/726.WAV','2-HP-MA/802.WAV','2-HP-MA/810.WAV','2-HP-MA/811.WAV','2-HP-MA/813.WAV','2-HP-MA/816.WAV','2-HP-MA/820.WAV','2-HP-MA/826.WAV',

        '3-HP-LA/172.WAV','3-HP-LA/809.WAV','3-HP-LA/812.WAV',

        '4-MP-HA/114.WAV','4-MP-HA/204.WAV','4-MP-HA/210.WAV','4-MP-HA/216.WAV','4-MP-HA/610.WAV','4-MP-HA/704.WAV','4-MP-HA/710.WAV','4-MP-HA/715.WAV',

        '5-MP-MA/102.WAV','5-MP-MA/104.WAV','5-MP-MA/107.WAV','5-MP-MA/111.WAV','5-MP-MA/113.WAV','5-MP-MA/120.WAV','5-MP-MA/130.WAV','5-MP-MA/132.WAV','5-MP-MA/152.WAV','5-MP-MA/170.WAV','5-MP-MA/225.WAV','5-MP-MA/245.WAV','5-MP-MA/246.WAV','5-MP-MA/251.WAV','5-MP-MA/252.WAV','5-MP-MA/320.WAV','5-MP-MA/322.WAV','5-MP-MA/358.WAV','5-MP-MA/361.WAV','5-MP-MA/364.WAV','5-MP-MA/368.WAV','5-MP-MA/370.WAV','5-MP-MA/373.WAV','5-MP-MA/374.WAV','5-MP-MA/375.WAV','5-MP-MA/376.WAV','5-MP-MA/382.WAV','5-MP-MA/403.WAV','5-MP-MA/410.WAV','5-MP-MA/425.WAV','5-MP-MA/500.WAV','5-MP-MA/627.WAV','5-MP-MA/698.WAV','5-MP-MA/700.WAV','5-MP-MA/701.WAV','5-MP-MA/702.WAV','5-MP-MA/705.WAV','5-MP-MA/706.WAV','5-MP-MA/720.WAV','5-MP-MA/722.WAV','5-MP-MA/723.WAV','5-MP-MA/724.WAV','5-MP-MA/728.WAV','5-MP-MA/729.WAV',

        '6-MP-LA/171.WAV','6-MP-LA/262.WAV','6-MP-LA/377.WAV','6-MP-LA/602.WAV','6-MP-LA/708.WAV',

        '7-LP-HA/105.WAV','7-LP-HA/106.WAV','7-LP-HA/115.WAV','7-LP-HA/116.WAV','7-LP-HA/133.WAV','7-LP-HA/134.WAV','7-LP-HA/244.WAV','7-LP-HA/255.WAV','7-LP-HA/260.WAV','7-LP-HA/261.WAV','7-LP-HA/275.WAV','7-LP-HA/276.WAV','7-LP-HA/277.WAV','7-LP-HA/278.WAV','7-LP-HA/279.WAV','7-LP-HA/281.WAV','7-LP-HA/282.WAV','7-LP-HA/283.WAV','7-LP-HA/284.WAV','7-LP-HA/285.WAV','7-LP-HA/286.WAV','7-LP-HA/288.WAV','7-LP-HA/289.WAV','7-LP-HA/290.WAV','7-LP-HA/292.WAV','7-LP-HA/296.WAV','7-LP-HA/310.WAV','7-LP-HA/312.WAV','7-LP-HA/319.WAV','7-LP-HA/380.WAV','7-LP-HA/420.WAV','7-LP-HA/422.WAV','7-LP-HA/423.WAV','7-LP-HA/424.WAV','7-LP-HA/501.WAV','7-LP-HA/502.WAV','7-LP-HA/600.WAV','7-LP-HA/624.WAV','7-LP-HA/625.WAV','7-LP-HA/626.WAV','7-LP-HA/699.WAV','7-LP-HA/709.WAV','7-LP-HA/711.WAV','7-LP-HA/712.WAV','7-LP-HA/713.WAV','7-LP-HA/714.WAV','7-LP-HA/719.WAV','7-LP-HA/730.WAV','7-LP-HA/732.WAV','7-LP-HA/910.WAV',

        '8-LP-MA/241.WAV','8-LP-MA/242.WAV','8-LP-MA/243.WAV','8-LP-MA/250.WAV','8-LP-MA/280.WAV','8-LP-MA/293.WAV','8-LP-MA/295.WAV','8-LP-MA/611.WAV','8-LP-MA/703.WAV',

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
    return render(request, 'final_thanks.html')

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
        print("Here")
        RatingPractice.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus')),
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
        )

    elif data.get('is_rerating'):
        RatingResponse.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus_number')),
            stimulus_file=data['stimulus_file'],
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
        )

    else:
        return JsonResponse({'status': 'error', 'message': 'نوع داده نامعتبر'}, status=400)

    return JsonResponse({'status': 'success'})




###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
###################################################################################################### 
def extract_stimulus_number(url: Optional[str]) -> Optional[int]:
    """استخراج شماره stimulus از URL فایل صوتی (مثل 102 از 102.WAV)"""
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
        '5-MP-MA/102.WAV','5-MP-MA/104.WAV','5-MP-MA/107.WAV','5-MP-MA/111.WAV','5-MP-MA/113.WAV',
        '5-MP-MA/120.WAV','5-MP-MA/130.WAV','5-MP-MA/132.WAV','5-MP-MA/152.WAV','5-MP-MA/170.WAV',
        '5-MP-MA/225.WAV','5-MP-MA/245.WAV','5-MP-MA/246.WAV','5-MP-MA/251.WAV','5-MP-MA/252.WAV',
        '5-MP-MA/320.WAV','5-MP-MA/322.WAV','5-MP-MA/358.WAV','5-MP-MA/361.WAV','5-MP-MA/364.WAV',
        '5-MP-MA/368.WAV','5-MP-MA/370.WAV','5-MP-MA/373.WAV','5-MP-MA/374.WAV','5-MP-MA/375.WAV',
        '5-MP-MA/376.WAV','5-MP-MA/382.WAV','5-MP-MA/403.WAV','5-MP-MA/410.WAV','5-MP-MA/425.WAV',
        '5-MP-MA/500.WAV','5-MP-MA/627.WAV','5-MP-MA/698.WAV','5-MP-MA/700.WAV','5-MP-MA/701.WAV',
        '5-MP-MA/702.WAV','5-MP-MA/705.WAV','5-MP-MA/706.WAV','5-MP-MA/720.WAV','5-MP-MA/722.WAV',
        '5-MP-MA/723.WAV','5-MP-MA/724.WAV','5-MP-MA/728.WAV','5-MP-MA/729.WAV',
    ]

    negative_files = [
        '7-LP-HA/105.WAV','7-LP-HA/106.WAV','7-LP-HA/115.WAV','7-LP-HA/116.WAV','7-LP-HA/133.WAV',
        '7-LP-HA/134.WAV','7-LP-HA/244.WAV','7-LP-HA/255.WAV','7-LP-HA/260.WAV','7-LP-HA/261.WAV',
        '7-LP-HA/275.WAV','7-LP-HA/276.WAV','7-LP-HA/277.WAV','7-LP-HA/278.WAV','7-LP-HA/279.WAV',
        '7-LP-HA/281.WAV','7-LP-HA/282.WAV','7-LP-HA/283.WAV','7-LP-HA/284.WAV','7-LP-HA/285.WAV',
        '7-LP-HA/286.WAV','7-LP-HA/288.WAV','7-LP-HA/289.WAV','7-LP-HA/290.WAV','7-LP-HA/292.WAV',
        '7-LP-HA/296.WAV','7-LP-HA/310.WAV','7-LP-HA/312.WAV','7-LP-HA/319.WAV','7-LP-HA/380.WAV',
        '7-LP-HA/420.WAV','7-LP-HA/422.WAV','7-LP-HA/423.WAV','7-LP-HA/424.WAV','7-LP-HA/501.WAV',
        '7-LP-HA/502.WAV','7-LP-HA/600.WAV','7-LP-HA/624.WAV','7-LP-HA/625.WAV','7-LP-HA/626.WAV',
        '7-LP-HA/699.WAV','7-LP-HA/709.WAV','7-LP-HA/711.WAV','7-LP-HA/712.WAV','7-LP-HA/713.WAV',
        '7-LP-HA/714.WAV','7-LP-HA/719.WAV','7-LP-HA/730.WAV','7-LP-HA/732.WAV','7-LP-HA/910.WAV',
        '8-LP-MA/241.WAV','8-LP-MA/242.WAV','8-LP-MA/243.WAV','8-LP-MA/250.WAV','8-LP-MA/280.WAV',
        '8-LP-MA/293.WAV','8-LP-MA/295.WAV','8-LP-MA/611.WAV','8-LP-MA/703.WAV',
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

SEQUENCES = ['Neutral-Neutral', 'Negative-Neutral', 'Neutral-Negative']
def get_or_create_cue_mapping(user):
    # ابتدا سعی می‌کنیم mapping موجود را بگیریم
    try:
        return PCMCueMapping.objects.get(user=user).mapping
    except PCMCueMapping.DoesNotExist:
        pass

    # اگر وجود نداشت، mapping جدید می‌سازیم
    random.seed(user.id or user.pk)  # اگر id هنوز نباشد pk هم کار می‌کند

    seqs = SEQUENCES[:]
    random.shuffle(seqs)

    mapping = {}
    for i, cue_url in enumerate(CUE_URLS):
        # اگر تعداد cue بیشتر از ۳ باشد، از random.choice استفاده می‌کنیم
        if i < len(seqs):
            mapping[cue_url] = seqs[i]
        else:
            mapping[cue_url] = random.choice(SEQUENCES)

    # حالا با defaults ایجاد می‌کنیم تا فیلد mapping حتما پر باشد
    obj, created = PCMCueMapping.objects.get_or_create(
        user=user,
        defaults={'mapping': mapping}
    )
    return obj.mapping


def get_sequence_order(user, total_trials: int) -> List[str]:
    """ساخت لیست متعادل و تصادفی توالی‌ها با seed بر اساس user.id"""
    random.seed(user.id)  # برای تکرارپذیری در refreshها

    possible_sequences = ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"]
    trials_per_seq = total_trials // 3
    remainder = total_trials % 3

    sequence_order = []
    for _ in range(trials_per_seq):
        sequence_order.extend(possible_sequences)

    # اضافه کردن باقی‌مانده
    extra_sequences = possible_sequences[:remainder]
    sequence_order.extend(extra_sequences)

    # shuffle کردن لیست
    random.shuffle(sequence_order)
    return sequence_order

@login_required(login_url='login_or_signup')
@questionnaires_required([1, 2, 3])
def pcm_view(request):
    user = request.user
    cues_mapping = get_or_create_cue_mapping(user)
    neutral_raw, negative_raw = get_stimuli_lists()
    NEUTRAL_URLS = [build_audio_url(f) for f in neutral_raw]
    NEGATIVE_URLS = [build_audio_url(f) for f in negative_raw]

    # --- مرحله ۱: تمرین تشخیص توالی ---
    SEQ_TRIALS = 2  # تعداد کل مرحله تمرینی
    SEQ_THRESHOLD = 0.83  # درصد پاسخ درست برای گذر از مرحله 
    
    seq_responses = PCMSequencePracticeResponse.objects.filter(user=user)
    seq_count = seq_responses.count()  # تعداد پاسخ های ثبت شده 
    progress_percentage = (seq_count / SEQ_TRIALS) * 100

    if seq_count < SEQ_TRIALS:  # تغییر به < برای جلوگیری از >= که قبلاً بود
        # محاسبه تعداد باقی‌مانده و ساخت لیست متعادل و تصادفی برای توالی‌های باقی‌مانده
        remain_trials = SEQ_TRIALS - seq_count
        possible_sequences = ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"]
        
        # شمارش تعداد استفاده‌شده از هر توالی تا حالا (برای حفظ تعادل کلی)
        used_sequences = [
            f"{r.category_stim1}-{r.category_stim2}" 
            for r in seq_responses if r.category_stim1 and r.category_stim2
        ]
        counts = Counter(used_sequences)
        
        # محاسبه تعداد هدف کلی برای هر توالی (برای کل SEQ_TRIALS)
        target_per_seq = SEQ_TRIALS // len(possible_sequences)
        remainder_total = SEQ_TRIALS % len(possible_sequences)
        
        # محاسبه تعداد باقی‌مانده برای هر توالی بر اساس هدف - استفاده‌شده
        remaining_per_seq = {}
        for i, seq in enumerate(possible_sequences):
            target = target_per_seq + (1 if i < remainder_total else 0)
            remaining_per_seq[seq] = max(0, target - counts.get(seq, 0))
        
        # ساخت لیست remaining_sequences بر اساس تعداد باقی‌مانده هر توالی
        sequence_order = []
        for seq, rem in remaining_per_seq.items():
            sequence_order.extend([seq] * rem)
        
        # اگر مجموع باقی‌مانده برابر remain_trials نبود (به دلیل خطا)، تنظیم کنیم
        if len(sequence_order) != remain_trials:
            # این نباید اتفاق بیفتد، اما برای ایمنی
            trials_per_seq = remain_trials // len(possible_sequences)
            remainder = remain_trials % len(possible_sequences)
            sequence_order = []
            for i in range(trials_per_seq):
                sequence_order.extend(possible_sequences)
            for i in range(remainder):
                sequence_order.append(possible_sequences[i])
        
        # shuffle تصادفی لیست
        random.shuffle(sequence_order)
        
        context = {
            'current_trial': seq_count,
            'total_trials': SEQ_TRIALS,
            'progress_percentage': progress_percentage,
            'cue_urls': json.dumps(CUE_URLS),
            'neutral_urls': json.dumps(NEUTRAL_URLS),
            'negative_urls': json.dumps(NEGATIVE_URLS),
            'cues_mapping': json.dumps(cues_mapping),
            'remaining_sequences': json.dumps(sequence_order),  # لیست باقی‌مانده متعادل و shuffle‌شده
        }
        return render(request, '1_seq_practice.html', context)
    else:
        seq_correct = seq_responses.filter(is_correct=True).count()  # محاسبه پاسخ درست 
        seq_accuracy = seq_correct / seq_count if seq_count > 0 else 0
        if seq_accuracy >= SEQ_THRESHOLD:
            pass
        else:
            text = "متاسفانه با توجه نتایج کسب شده حائز شرکت در ادامه آزمون نبودید "
            context = {
                'text': text,
            }
            return render(request, 'final_thanks.html', context)
        

    # --- مرحله ۲: تمرین رتبه‌بندی خوشایندی ---
    VALENCE_PRACTICE_TRIALS = 2
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
        return render(request, '2_valence_practice.html', context)

    # --- مرحله ۳: آزمون اصلی PCM ---
    NUM_BLOCKS = 3
    CATCH_TRIALS_PER_BLOCK = 2
    MAIN_TRIALS_PER_BLOCK = 10

    # محاسبه بلاک فعلی و پیشرفت کلی
    current_block = None
    all_catch_sequences = {}  # {block_num: [sequences]}
    all_main_trials = {}      # {block_num: [trials dict]}

    total_completed = 0
    total_trials_all = NUM_BLOCKS * (CATCH_TRIALS_PER_BLOCK + MAIN_TRIALS_PER_BLOCK)

    for block_num in range(1, NUM_BLOCKS + 1):
        catch_count = PCMCatchResponse.objects.filter(user=user, block=block_num).count()
        main_count = PCMMainResponse.objects.filter(user=user, block=block_num).count()

        completed_in_block = catch_count + main_count
        total_completed += completed_in_block

        # اگر این بلاک ناتمام است → بلاک فعلی
        if catch_count < CATCH_TRIALS_PER_BLOCK or main_count < MAIN_TRIALS_PER_BLOCK:
            if current_block is None:
                current_block = block_num

        # --- ساخت توالی‌های catch برای این بلاک (اگر نیاز باشد) ---
        if catch_count < CATCH_TRIALS_PER_BLOCK:
            remain_catch = CATCH_TRIALS_PER_BLOCK - catch_count
            possible_sequences = ["Neutral-Neutral", "Neutral-Negative", "Negative-Neutral"]

            used = [f"{r.category_stim1}-{r.category_stim2}" for r in PCMCatchResponse.objects.filter(user=user, block=block_num) if r.category_stim1 and r.category_stim2]
            counts = Counter(used)

            target_per_seq = CATCH_TRIALS_PER_BLOCK // 3
            remainder = CATCH_TRIALS_PER_BLOCK % 3

            remaining_per_seq = {}
            for i, seq in enumerate(possible_sequences):
                target = target_per_seq + (1 if i < remainder else 0)
                remaining_per_seq[seq] = max(0, target - counts.get(seq, 0))

            sequence_order = []
            for seq, rem in remaining_per_seq.items():
                sequence_order.extend([seq] * rem)

            if len(sequence_order) != remain_catch:
                sequence_order = possible_sequences * (remain_catch // 3) + possible_sequences[:remain_catch % 3]

            random.shuffle(sequence_order)
            all_catch_sequences[block_num] = sequence_order

        # --- ساخت توالی‌های main برای این بلاک (اگر نیاز باشد) ---
        if main_count < MAIN_TRIALS_PER_BLOCK:
            remain_main = MAIN_TRIALS_PER_BLOCK - main_count

            # تمام توالی‌های ممکن
            ALL_POSSIBLE_SEQUENCES = ["Neutral-Neutral", "Negative-Neutral", "Neutral-Negative"]

            # شمارش پاسخ‌های قبلی در این بلاک
            used_seqs = [
                f"{r.category_stim1}-{r.category_stim2}"
                for r in PCMMainResponse.objects.filter(user=user, block=block_num)
                if r.category_stim1 and r.category_stim2
            ]
            used_consistent = sum(1 for s in used_seqs if s in ALL_POSSIBLE_SEQUENCES[:3])  # فقط ۳ تای اصلی
            used_inconsistent = len(used_seqs) - used_consistent

            # هدف: 75% consistent — 25% inconsistent (می‌توانید تغییر دهید)
            target_consistent = int(MAIN_TRIALS_PER_BLOCK * 0.75)
            target_inconsistent = MAIN_TRIALS_PER_BLOCK - target_consistent

            remain_consistent = max(0, target_consistent - used_consistent)
            remain_inconsistent = max(0, target_inconsistent - used_inconsistent)

            # ساخت لیست نوع trialها
            trial_types = (
                [{'type': 'consistent'}] * remain_consistent +
                [{'type': 'inconsistent'}] * remain_inconsistent
            )

            # اگر هنوز کم بود → تصادفی پر کنیم
            if len(trial_types) < remain_main:
                extra = remain_main - len(trial_types)
                trial_types += [
                    {'type': 'consistent' if random.random() < 0.75 else 'inconsistent'}
                    for _ in range(extra)
                ]

            random.shuffle(trial_types)

            # حالا برای هر trial نوع → cue و sequence واقعی بسازیم
            final_trials = []
            
            # کمک برای تعادل در consistentها
            cons_counts = Counter([
                f"{r.category_stim1}-{r.category_stim2}"
                for r in PCMMainResponse.objects.filter(user=user, block=block_num)
                if r.is_consistent
            ])

            for item in trial_types:
                if item['type'] == 'inconsistent':
                    # انتخاب cue تصادفی
                    cue = random.choice(CUE_URLS)
                    
                    # توالی منتظره (consistent) برای این cue
                    expected_seq = cues_mapping[cue]
                    
                    # دو توالی دیگر = inconsistentهای ممکن
                    possible_inconsistents = [s for s in ALL_POSSIBLE_SEQUENCES if s != expected_seq]
                    
                    # انتخاب یکی از دو inconsistent به صورت تصادفی
                    # اگر می‌خواهید دقیق‌تر 50-50 باشد، می‌توانید از weights یا Counter استفاده کنید
                    actual_seq = random.choice(possible_inconsistents)
                    
                    final_trials.append({
                        'actual_seq': actual_seq,
                        'cue': cue,
                        'expected_seq': expected_seq,   # برای لاگ/دیباگ مفید است
                    })

                else:  # consistent
                    # انتخاب توالی consistent با وزن‌دهی برای تعادل
                    weights = [
                        max(0, (remain_consistent // 3) - cons_counts.get(seq, 0))
                        for seq in ALL_POSSIBLE_SEQUENCES
                    ]
                    
                    if sum(weights) == 0:
                        # اگر همه استفاده شده، تصادفی
                        seq = random.choice(ALL_POSSIBLE_SEQUENCES)
                    else:
                        seq = random.choices(ALL_POSSIBLE_SEQUENCES, weights=weights, k=1)[0]
                    
                    # cueهایی که این توالی را انتظار دارند
                    cue_candidates = [c for c, exp in cues_mapping.items() if exp == seq]
                    cue = random.choice(cue_candidates) if cue_candidates else random.choice(CUE_URLS)
                    
                    final_trials.append({
                        'actual_seq': seq,
                        'cue': cue,
                        'expected_seq': seq,  # چون consistent است
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
            'perior_block': current_block-1,
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

            # مهم: تمام داده‌های همه بلاک‌ها
            'all_catch_sequences': json.dumps(all_catch_sequences),
            'all_main_trials': json.dumps(all_main_trials),
        }
        return render(request, '3_pcm_main.html', context)
    

    # --- مرحله 4: تمرین رتبه بندی خوشایندی و برانگیختگی---
    RATING_PRACTICE_TRIALS = 2
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
        '5-MP-MA/102.WAV',
        '5-MP-MA/104.WAV',
        '5-MP-MA/107.WAV',
        '5-MP-MA/111.WAV',
        '5-MP-MA/113.WAV',
        # '5-MP-MA/120.WAV','5-MP-MA/130.WAV','5-MP-MA/132.WAV','5-MP-MA/152.WAV','5-MP-MA/170.WAV','5-MP-MA/225.WAV','5-MP-MA/245.WAV','5-MP-MA/246.WAV','5-MP-MA/251.WAV','5-MP-MA/252.WAV','5-MP-MA/320.WAV','5-MP-MA/322.WAV','5-MP-MA/358.WAV','5-MP-MA/361.WAV','5-MP-MA/364.WAV','5-MP-MA/368.WAV','5-MP-MA/370.WAV','5-MP-MA/373.WAV','5-MP-MA/374.WAV','5-MP-MA/375.WAV','5-MP-MA/376.WAV','5-MP-MA/382.WAV','5-MP-MA/403.WAV','5-MP-MA/410.WAV','5-MP-MA/425.WAV','5-MP-MA/500.WAV','5-MP-MA/627.WAV','5-MP-MA/698.WAV','5-MP-MA/700.WAV','5-MP-MA/701.WAV','5-MP-MA/702.WAV','5-MP-MA/705.WAV','5-MP-MA/706.WAV','5-MP-MA/720.WAV','5-MP-MA/722.WAV','5-MP-MA/723.WAV','5-MP-MA/724.WAV','5-MP-MA/728.WAV','5-MP-MA/729.WAV',

        # '6-MP-LA/171.WAV','6-MP-LA/262.WAV','6-MP-LA/377.WAV','6-MP-LA/602.WAV','6-MP-LA/708.WAV',

        # '7-LP-HA/105.WAV','7-LP-HA/106.WAV','7-LP-HA/115.WAV','7-LP-HA/116.WAV','7-LP-HA/133.WAV','7-LP-HA/134.WAV','7-LP-HA/244.WAV','7-LP-HA/255.WAV','7-LP-HA/260.WAV','7-LP-HA/261.WAV','7-LP-HA/275.WAV','7-LP-HA/276.WAV','7-LP-HA/277.WAV','7-LP-HA/278.WAV','7-LP-HA/279.WAV','7-LP-HA/281.WAV','7-LP-HA/282.WAV','7-LP-HA/283.WAV','7-LP-HA/284.WAV','7-LP-HA/285.WAV','7-LP-HA/286.WAV','7-LP-HA/288.WAV','7-LP-HA/289.WAV','7-LP-HA/290.WAV','7-LP-HA/292.WAV','7-LP-HA/296.WAV','7-LP-HA/310.WAV','7-LP-HA/312.WAV','7-LP-HA/319.WAV','7-LP-HA/380.WAV','7-LP-HA/420.WAV','7-LP-HA/422.WAV','7-LP-HA/423.WAV','7-LP-HA/424.WAV','7-LP-HA/501.WAV','7-LP-HA/502.WAV','7-LP-HA/600.WAV','7-LP-HA/624.WAV','7-LP-HA/625.WAV','7-LP-HA/626.WAV','7-LP-HA/699.WAV','7-LP-HA/709.WAV','7-LP-HA/711.WAV','7-LP-HA/712.WAV','7-LP-HA/713.WAV','7-LP-HA/714.WAV','7-LP-HA/719.WAV','7-LP-HA/730.WAV','7-LP-HA/732.WAV','7-LP-HA/910.WAV',

        # '8-LP-MA/241.WAV','8-LP-MA/242.WAV','8-LP-MA/243.WAV','8-LP-MA/250.WAV','8-LP-MA/280.WAV','8-LP-MA/293.WAV','8-LP-MA/295.WAV','8-LP-MA/611.WAV','8-LP-MA/703.WAV',
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
    return render(request, 'final_thanks.html')


@csrf_exempt
def pcm_save_response(request):
    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'فقط POST'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'JSON نامعتبر'}, status=400)

    user = request.user
    # مرحله ۱: تمرین تشخیص توالی
    if data.get('is_seq_practice'):
        
        PCMSequencePracticeResponse.objects.create(
            user=user,
            trial=data['trial'] ,
            cue=extract_stimulus_number(data['cue']),
            stimulus1=extract_stimulus_number(data.get('stimulus1')),
            stimulus2=extract_stimulus_number(data.get('stimulus2')),
            category_stim1=data.get('category_stim1'),
            category_stim2=data.get('category_stim2'),
            user_response=data['user_response'],
            is_correct=data['is_correct'],
        )

    # مرحله ۲: تمرین رتبه‌بندی خوشایندی
    elif data.get('is_valence_practice'):
        PCMValencePracticeResponse.objects.create(
            user=user,
            trial=data['trial'],
            cue=extract_stimulus_number(data['cue']),
            stimulus1=extract_stimulus_number(data.get('stimulus1')),
            stimulus2=extract_stimulus_number(data.get('stimulus2')),
            category_stim1=data.get('category_stim1'),
            category_stim2=data.get('category_stim2'),
            valence_stim1=data.get('valence_stim1'),
            valence_rt_stim1=data.get('rt_stim1'),
            valence_stim2=data.get('valence_stim2'),
            valence_rt_stim2=data.get('rt_stim2'),
            valence_sequence=data.get('valence_sequence'),
            valence_rt_sequence=data.get('rt_sequence'),
        )

    # مرحله ۳: آزمون اصلی
    elif data.get('is_catch'):
        PCMCatchResponse.objects.create(
            user=user,
            block=data.get('block', None),
            trial=data['trial'],
            cue=extract_stimulus_number(data['cue']),
            stimulus1=extract_stimulus_number(data.get('stimulus1')),
            stimulus2=extract_stimulus_number(data.get('stimulus2')),
            category_stim1=data.get('category_stim1'),
            category_stim2=data.get('category_stim2'),
            user_response=data.get('user_response'),
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
            valence_stim2=data.get('valence_stim2'),
            valence_rt_stim2=data.get('valence_rt_stim2'),
            valence_sequence=data.get('valence_sequence'),
            valence_rt_sequence=data.get('valence_rt_sequence'),
        )

    # مرحله ۴: تمرین رتبه‌بندی کامل
    elif data.get('is_rating_practice'):
        RatingPracticeResponse.objects.create(
            user=user,
            trial=data['trial'],
            stimulus=extract_stimulus_number(data.get('stimulus')),
            valence=data.get('valence'),
            valence_rt=data.get('valence_rt'),
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
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
            arousal=data.get('arousal'),
            arousal_rt=data.get('arousal_rt'),
        )

    else:
        return JsonResponse({'status': 'error', 'message': 'نوع داده نامعتبر'}, status=400)

    return JsonResponse({'status': 'success'})


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