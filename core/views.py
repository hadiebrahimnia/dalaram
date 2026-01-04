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

def home_view(request):
    return render(request, 'index.html')

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

@login_required(login_url='login_or_signup')
@questionnaires_required([1,2,3])
def rating_view(request):
    if request.method == 'POST':
        data = json.loads(request.body) if request.body else {}
        audio_file = data.get('audio_file')
        valence = data.get('valence')
        arousal = data.get('arousal')
        valence_rt = data.get('valence_rt')
        arousal_rt = data.get('arousal_rt')

        if audio_file:
            parts = audio_file.split('/')
            number = parts[4][:-4] 
            stimulus = f"{number}"
            rating_response, created = RatingResponse.objects.update_or_create(
                user=request.user,
                stimulus=stimulus,
                defaults={
                    'valence': valence if valence is not None else None,
                    'valence_rt': valence_rt if valence is not None else None,
                    'arousal': arousal if arousal is not None else None,
                    'arousal_rt': arousal_rt if arousal is not None else None,
                }
            )

        return JsonResponse({'status': 'success'})

    base_dir = 'sounds'
    practice_files = [
        '0-practice/1.WAV',
        # '0-practice/2.WAV',
        # '0-practice/3.WAV',
        # '0-practice/4.WAV',
        # '0-practice/5.WAV',
        # '0-practice/6.WAV',
        # '0-practice/7.WAV',
        # '0-practice/8.WAV',
        # '0-practice/9.WAV',
        # '0-practice/10.WAV',
    ]
    main_files = [
        '1-HP-HA/110.WAV','1-HP-HA/200.WAV','1-HP-HA/201.WAV','1-HP-HA/202.WAV','1-HP-HA/205.WAV','1-HP-HA/215.WAV','1-HP-HA/220.WAV','1-HP-HA/311.WAV','1-HP-HA/352.WAV','1-HP-HA/353.WAV','1-HP-HA/355.WAV','1-HP-HA/360.WAV','1-HP-HA/363.WAV','1-HP-HA/365.WAV','1-HP-HA/366.WAV','1-HP-HA/367.WAV','1-HP-HA/378.WAV','1-HP-HA/415.WAV','1-HP-HA/716.WAV','1-HP-HA/717.WAV','1-HP-HA/808.WAV','1-HP-HA/815.WAV','1-HP-HA/817.WAV',

        '2-HP-MA/109.WAV','2-HP-MA/111.WAV','2-HP-MA/112.WAV','2-HP-MA/150.WAV','2-HP-MA/151.WAV','2-HP-MA/206.WAV','2-HP-MA/221.WAV','2-HP-MA/224.WAV','2-HP-MA/226.WAV','2-HP-MA/230.WAV','2-HP-MA/254.WAV','2-HP-MA/270.WAV','2-HP-MA/351.WAV','2-HP-MA/400.WAV','2-HP-MA/601.WAV','2-HP-MA/721.WAV','2-HP-MA/725.WAV','2-HP-MA/726.WAV','2-HP-MA/802.WAV','2-HP-MA/810.WAV','2-HP-MA/811.WAV','2-HP-MA/813.WAV','2-HP-MA/816.WAV','2-HP-MA/820.WAV','2-HP-MA/826.WAV',

        '3-HP-LA/172.WAV','3-HP-LA/809.WAV','3-HP-LA/812.WAV',

        '4-MP-HA/114.WAV','4-MP-HA/204.WAV','4-MP-HA/210.WAV','4-MP-HA/216.WAV','4-MP-HA/610.WAV','4-MP-HA/704.WAV','4-MP-HA/710.WAV','4-MP-HA/715.WAV',

        '5-MP-MA/102.WAV','5-MP-MA/104.WAV','5-MP-MA/107.WAV','5-MP-MA/111.WAV','5-MP-MA/113.WAV','5-MP-MA/120.WAV','5-MP-MA/130.WAV','5-MP-MA/132.WAV','5-MP-MA/152.WAV','5-MP-MA/170.WAV','5-MP-MA/225.WAV','5-MP-MA/245.WAV','5-MP-MA/246.WAV','5-MP-MA/251.WAV','5-MP-MA/252.WAV','5-MP-MA/320.WAV','5-MP-MA/322.WAV','5-MP-MA/358.WAV','5-MP-MA/361.WAV','5-MP-MA/364.WAV','5-MP-MA/368.WAV','5-MP-MA/370.WAV','5-MP-MA/373.WAV','5-MP-MA/374.WAV','5-MP-MA/375.WAV','5-MP-MA/376.WAV','5-MP-MA/382.WAV','5-MP-MA/403.WAV','5-MP-MA/410.WAV','5-MP-MA/425.WAV','5-MP-MA/500.WAV','5-MP-MA/627.WAV','5-MP-MA/698.WAV','5-MP-MA/700.WAV','5-MP-MA/701.WAV','5-MP-MA/702.WAV','5-MP-MA/705.WAV','5-MP-MA/706.WAV','5-MP-MA/720.WAV','5-MP-MA/722.WAV','5-MP-MA/723.WAV','5-MP-MA/724.WAV','5-MP-MA/728.WAV','5-MP-MA/729.WAV',

        '6-MP-LA/171.WAV','6-MP-LA/262.WAV','6-MP-LA/377.WAV','6-MP-LA/602.WAV','6-MP-LA/708.WAV',

        '7-LP-HA/105.WAV','7-LP-HA/106.WAV','7-LP-HA/115.WAV','7-LP-HA/116.WAV','7-LP-HA/133.WAV','7-LP-HA/134.WAV','7-LP-HA/244.WAV','7-LP-HA/255.WAV','7-LP-HA/260.WAV','7-LP-HA/261.WAV','7-LP-HA/275.WAV','7-LP-HA/276.WAV','7-LP-HA/277.WAV','7-LP-HA/278.WAV','7-LP-HA/279.WAV','7-LP-HA/281.WAV','7-LP-HA/282.WAV','7-LP-HA/283.WAV','7-LP-HA/284.WAV','7-LP-HA/285.WAV','7-LP-HA/286.WAV','7-LP-HA/288.WAV','7-LP-HA/289.WAV','7-LP-HA/290.WAV','7-LP-HA/292.WAV','7-LP-HA/296.WAV','7-LP-HA/310.WAV','7-LP-HA/312.WAV','7-LP-HA/319.WAV','7-LP-HA/380.WAV','7-LP-HA/420.WAV','7-LP-HA/422.WAV','7-LP-HA/423.WAV','7-LP-HA/424.WAV','7-LP-HA/501.WAV','7-LP-HA/502.WAV','7-LP-HA/600.WAV','7-LP-HA/624.WAV','7-LP-HA/625.WAV','7-LP-HA/626.WAV','7-LP-HA/699.WAV','7-LP-HA/709.WAV','7-LP-HA/711.WAV','7-LP-HA/712.WAV','7-LP-HA/713.WAV','7-LP-HA/714.WAV','7-LP-HA/719.WAV','7-LP-HA/730.WAV','7-LP-HA/732.WAV','7-LP-HA/910.WAV',

        '8-LP-MA/241.WAV','8-LP-MA/242.WAV','8-LP-MA/243.WAV','8-LP-MA/250.WAV','8-LP-MA/280.WAV','8-LP-MA/293.WAV','8-LP-MA/295.WAV','8-LP-MA/611.WAV','8-LP-MA/703.WAV',

    ]
    main_files = list(set(main_files))

    completed_stimuli = set(
        RatingResponse.objects
        .filter(user=request.user)
        .exclude(valence__isnull=True)
        .exclude(arousal__isnull=True)
        .values_list('stimulus', flat=True)
    )

    remaining_main_files = []
    for file in main_files:
        parts = file.split('/')
        number = parts[1][:-4]
        stimulus = f"{number}"
        if stimulus not in completed_stimuli:
            remaining_main_files.append(file)

    random.shuffle(practice_files)
    random.shuffle(remaining_main_files)
    practice_files = practice_files[:10] 
    def audio_url(filename):
        return static(f'{base_dir}/{filename}')

    practice_urls = [audio_url(f) for f in practice_files]
    main_urls = [audio_url(f) for f in remaining_main_files]

    context = {
        'title': 'آزمایش رتبه‌بندی',
        'practice_files': practice_urls,
        'main_files': main_urls,
    }
    return render(request, 'rating.html', context)


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


def build_audio_url(filename: str) -> str:
    """ساخت URL کامل برای فایل صوتی در static"""
    return staticfiles_storage.url(f'sounds/{filename}')


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


class PCMProgress:
    """کلاس یکپارچه برای محاسبه وضعیت و پیشرفت کاربر"""
    
    def __init__(self, user, practice_responses, main_responses):
        self.user = user
        self.practice_responses = practice_responses
        self.main_responses = main_responses
        
        # ثابت‌ها
        self.NUM_BLOCKS = 4
        self.TRIALS_PER_BLOCK = 2
        self.PRACTICE_TRIALS = 1
        self.PRACTICE_SUCCESS_THRESHOLD = 0.8
        VALENCE_PRACTICE_TRIALS = 3 
        
        self._calculate_progress()
    
    def _calculate_progress(self):
        """محاسبه تمام متغیرهای پیشرفت"""
        # مرحله تمرینی
        self.practice_total = self.practice_responses.count()
        self.practice_correct = self.practice_responses.filter(practice_correct=True).count()
        self.practice_accuracy = (
            self.practice_correct / self.practice_total 
            if self.practice_total > 0 else 0
        )
        self.is_practice_completed = (
            self.practice_total >= self.PRACTICE_TRIALS and
            self.practice_accuracy >= self.PRACTICE_SUCCESS_THRESHOLD
        )
        
        # مرحله اصلی
        self.current_block = 1
        self.current_trial = 1
        self.completed_main_trials = 0
        self.is_main_completed = False
        
        if self.main_responses.exists():
            last_response = self.main_responses.last()
            self.completed_main_trials = (
                (last_response.block - 1) * self.TRIALS_PER_BLOCK + last_response.trial
            )
            self.current_block = last_response.block
            self.current_trial = last_response.trial + 1
            
            if self.current_trial > self.TRIALS_PER_BLOCK:
                self.current_trial = 1
                self.current_block += 1
            
            if self.current_block > self.NUM_BLOCKS:
                self.is_main_completed = True
                self.current_block = self.NUM_BLOCKS
                self.current_trial = self.TRIALS_PER_BLOCK
        else:
            self.completed_main_trials = 0
        
        self.total_main_trials = self.NUM_BLOCKS * self.TRIALS_PER_BLOCK
        
        # استراحت بین بلوک‌ها
        self.is_at_block_break = False
        self.block_break_message = ""
        if (not self.is_main_completed and 
            self.main_responses.exists() and
            self.main_responses.last().trial == self.TRIALS_PER_BLOCK and
            self.main_responses.last().block < self.NUM_BLOCKS):
            self.is_at_block_break = True
            next_block = self.main_responses.last().block + 1
            self.block_break_message = (
                f"بلوک {self.main_responses.last().block} با موفقیت به پایان رسید.<br>"
                f"هر زمان که آماده بودید، روی دکمه زیر کلیک کنید تا بلوک {next_block} آغاز شود."
            )
    
    def get_initial_stage(self) -> str:
        """تعیین وضعیت یکپارچه کاربر (سلسله مراتبی)"""
        if self.is_at_block_break:
            return 'block_break'
        
        elif self.is_main_completed:
            # بررسی Re-rating
            used_stimuli = {
                num for resp in self.main_responses
                for num in [resp.stimulus1, resp.stimulus2] if num is not None
            }
            rerating_completed = PCMReRatingResponse.objects.filter(
                user=self.user
            ).count()
            total_rerating = len(used_stimuli)
            is_rerating_completed = total_rerating > 0 and rerating_completed >= total_rerating
            
            if total_rerating > 0 and not is_rerating_completed:
                return 'rerating_intro' if rerating_completed == 0 else 'resume_rerating'
            return 'final_thanks'
        
        elif self.is_practice_completed and self.main_responses.exists():
            return 'resume_main'
        
        elif self.is_practice_completed:
            return 'main_intro'
        
        elif self.practice_total > 0:
            return 'resume_practice'
        
        else:
            return 'intro'
    
    def get_resume_message(self, rerating_urls: List[str]) -> str:
        """پیام راهنمای ادامه کار"""
        initial_stage = self.get_initial_stage()
        
        if initial_stage == 'resume_practice':
            return f"شما مرحله تمرینی را تا تریال {self.practice_total} از {self.PRACTICE_TRIALS} انجام داده‌اید."
        
        elif initial_stage == 'resume_main':
            return (
                f"شما {self.completed_main_trials} از {self.total_main_trials} تریال آزمون اصلی را انجام داده‌اید "
                f"(بلوک {self.current_block}، تریال {self.current_trial})."
            )
        
        elif initial_stage in ['rerating_intro', 'resume_rerating']:
            rerating_completed = PCMReRatingResponse.objects.filter(user=self.user).count()
            return f"شما {rerating_completed} از {len(rerating_urls)} صدای مرحله رتبه‌بندی مجدد را رتبه‌بندی کرده‌اید."
        
        return ""


@login_required(login_url='login_or_signup')
@questionnaires_required([1, 2, 3])
def pcm_view(request):
    if request.method == 'POST':
        return _handle_post_request(request)

    # داده‌های صوتی
    cues_mapping = get_cues_mapping()
    neutral_files, negative_files = get_stimuli_lists()

    cue_urls = list(cues_mapping.keys())
    neutral_urls = [build_audio_url(f) for f in neutral_files]
    negative_urls = [build_audio_url(f) for f in negative_files]

    # لیست فایل‌های re-rating (همه محرک‌های استفاده‌شده)
    all_rerating_files = neutral_files + negative_files
    rerating_urls = [build_audio_url(f) for f in all_rerating_files]
    random.shuffle(rerating_urls)

    # پیشرفت کاربر
    practice_responses = PCMPracticeResponse.objects.filter(user=request.user)
    preparation_responses = PCMPreparationResponse.objects.filter(user=request.user)
    main_responses = PCMResponse.objects.filter(user=request.user).order_by('block', 'trial')
    rerating_responses = PCMReRatingResponse.objects.filter(user=request.user)

    practice_total = practice_responses.count()
    practice_correct = practice_responses.filter(practice_correct=True).count()
    practice_accuracy = practice_correct / practice_total if practice_total > 0 else 0

    preparation_responses_count = preparation_responses.count()

    print("valence_practice_count",preparation_responses_count)

    # تنظیمات ثابت
    NUM_BLOCKS = 4
    TRIALS_PER_BLOCK = 8
    CATCH_TRIALS_PER_BLOCK = 2  # تعداد catch trial در ابتدای هر بلوک
    PRACTICE_TRIALS = 6
    PRACTICE_THRESHOLD = 0.83  # حداقل دقت برای عبور از تمرین توالی
    PREPARATION_TRIALS = 4  # تعداد تریال تمرینی رتبه‌بندی خوشایندی

    # وضعیت مرحله اصلی
    current_block = 1
    current_trial = 1
    completed_main_trials = 0
    is_main_completed = False
    is_at_block_break = False
    block_break_message = ""

    if main_responses.exists():
        last = main_responses.last()
        completed_main_trials = (last.block - 1) * TRIALS_PER_BLOCK + last.trial
        current_block = last.block
        current_trial = last.trial + 1
        if current_trial > TRIALS_PER_BLOCK:
            current_trial = 1
            current_block += 1

        if current_block > NUM_BLOCKS:
            is_main_completed = True

        # تشخیص استراحت بین بلوک‌ها
        if last.trial == TRIALS_PER_BLOCK and current_block <= NUM_BLOCKS:
            is_at_block_break = True
            block_break_message = f"بلوک {last.block} با موفقیت به پایان رسید.<br>هر زمان آماده بودید، بلوک {current_block} را شروع کنید."

    # تعیین مرحله اولیه
    if is_at_block_break:
        initial_stage = 'block_break'
    elif is_main_completed:
        rerating_completed = rerating_responses.count()
        total_rerating = len(rerating_urls)
        if total_rerating > 0 and rerating_completed < total_rerating:
            initial_stage = 'rerating_intro' if rerating_completed == 0 else 'resume_rerating'
        else:
            initial_stage = 'final_thanks'
    elif preparation_responses_count < PREPARATION_TRIALS:
        initial_stage = 'preparation_intro' if preparation_responses_count == 0 else 'resume_preparation'
    elif main_responses.exists():
        initial_stage = 'resume_main'
    elif practice_accuracy >= PRACTICE_THRESHOLD and practice_total >= PRACTICE_TRIALS:
        initial_stage = 'main_intro'
    elif practice_total > 0:
        initial_stage = 'resume_practice'
    else:
        initial_stage = 'intro'

    show_resume_screen = initial_stage in {'resume_practice', 'resume_main', 'resume_preparation', 'resume_rerating'}
    resume_message = ""
    if 'resume_practice' in initial_stage:
        resume_message = f"شما {practice_total} از {PRACTICE_TRIALS} تریال تمرینی را انجام داده‌اید."
    elif 'resume_main' in initial_stage:
        resume_message = f"شما {completed_main_trials} از {NUM_BLOCKS * TRIALS_PER_BLOCK} تریال اصلی را انجام داده‌اید (بلوک {current_block}، تریال {current_trial})."
    elif 'resume_valence_practice' in initial_stage:
        resume_message = f"شما {preparation_responses_count} از {PREPARATION_TRIALS} تریال تمرینی رتبه‌بندی را انجام داده‌اید."
    elif 'resume_rerating' in initial_stage:
        resume_message = f"شما {rerating_responses.count()} از {len(rerating_urls)} صدا را در رتبه‌بندی مجدد ارزیابی کرده‌اید."

    context = {
        'title': 'آزمایش حافظه کاری عاطفی (PCM)',

        # داده‌های صوتی
        'cue_urls': json.dumps(cue_urls),
        'neutral_urls': json.dumps(neutral_urls),
        'negative_urls': json.dumps(negative_urls),
        'cues_mapping': json.dumps(cues_mapping),

        # تنظیمات
        'NUM_BLOCKS': NUM_BLOCKS,
        'TRIALS_PER_BLOCK': TRIALS_PER_BLOCK,
        'CATCH_TRIALS_PER_BLOCK': CATCH_TRIALS_PER_BLOCK,
        'PRACTICE_TRIALS': PRACTICE_TRIALS,
        'PRACTICE_THRESHOLD': PRACTICE_THRESHOLD,
        'PREPARATION_TRIALS': PREPARATION_TRIALS,
        'INCONSISTENT_RATIO': 0.2,

        # پیشرفت
        'CURRENT_BLOCK_INIT': current_block,
        'CURRENT_TRIAL_INIT': current_trial,
        'PRACTICE_CORRECT_INIT': practice_correct,
        'PRACTICE_TOTAL_INIT': practice_total,
        'PREPARATION_COMPLETED_COUNT': preparation_responses_count,

        # وضعیت‌ها
        'IS_AT_BLOCK_BREAK': 'true' if is_at_block_break else 'false',
        'BLOCK_BREAK_MESSAGE': block_break_message,
        'HAS_RERATING': 'true' if len(rerating_urls) > 0 else 'false',
        'rerating_files': json.dumps(rerating_urls),
        'RERATING_COMPLETED_COUNT': rerating_responses.count(),
        'TOTAL_RERATING_FILES': len(rerating_urls),

        # مرحله اولیه
        'INITIAL_STAGE': initial_stage,
        'SHOW_RESUME_SCREEN': 'true' if show_resume_screen else 'false',
        'RESUME_MESSAGE': resume_message,
    }

    return render(request, 'pcm.html', context)


def _handle_post_request(request) -> JsonResponse:
    """مدیریت یکپارچه درخواست‌های POST (ذخیره پاسخ‌ها)"""
    try:
        data = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': 'JSON نامعتبر'}, 
            status=400
        )
    
    # مرحله تمرینی
    if data.get('is_practice'):
        practice_trial = data.get('practice_trial')
        if practice_trial is None:
            return JsonResponse(
                {'status': 'error', 'message': 'شماره تریال تمرینی الزامی است'}, 
                status=400
            )
        
        PCMPracticeResponse.objects.update_or_create(
            user=request.user,
            trial=practice_trial,
            defaults={
                'cue': extract_stimulus_number(data.get('cue')),
                'stimulus1': extract_stimulus_number(data.get('stimulus1')),
                'stimulus2': extract_stimulus_number(data.get('stimulus2')),
                'category_stim1': data.get('category_stim1'),
                'category_stim2': data.get('category_stim2'),
                'practice_response': data.get('user_response'),
                'practice_correct': data.get('practice_correct'),
            }
        )
        return JsonResponse({'status': 'success'})
    
    # مرحله تمرینی رتبه‌بندی 
    if data.get('is_preparation'):
        trial = data.get('trial')
        if trial is None:
            return JsonResponse({'status': 'error', 'message': 'شماره تریال الزامی است'}, status=400)
        
        PCMPreparationResponse.objects.update_or_create(
            user=request.user,
            trial=trial,
            defaults={
                'cue': extract_stimulus_number(data.get('cue')),
                'stimulus1': extract_stimulus_number(data.get('stimulus1')),
                'stimulus2': extract_stimulus_number(data.get('stimulus2')),
                'category_stim1': data.get('category_stim1'),
                'category_stim2': data.get('category_stim2'),
                'valence_stim1': data.get('valence_stim1'),
                'valence_rt_stim1': data.get('valence_rt_stim1'),
                'valence_stim2': data.get('valence_stim2'),
                'valence_rt_stim2': data.get('valence_rt_stim2'),
                'valence_sequence': data.get('valence_sequence'),
                'valence_rt_sequence': data.get('valence_rt_sequence'),
            }
        )
        return JsonResponse({'status': 'success'})
    
    # مرحله اصلی PCM
    block = data.get('block')
    trial = data.get('trial')
    if block is not None and trial is not None:
        PCMResponse.objects.update_or_create(
            user=request.user,
            block=block,
            trial=trial,
            defaults={
                'cue': extract_stimulus_number(data.get('cue')),
                'stimulus1': extract_stimulus_number(data.get('stimulus1')),
                'stimulus2': extract_stimulus_number(data.get('stimulus2')),
                'expected_sequence': data.get('expected_sequence'),
                'is_consistent': data.get('is_consistent'),
                'category_stim1': data.get('category_stim1'),
                'category_stim2': data.get('category_stim2'),
                'valence_stim1': data.get('valence_stim1'),
                'valence_rt_stim1': data.get('valence_rt_stim1'),
                'valence_stim2': data.get('valence_stim2'),
                'valence_rt_stim2': data.get('valence_rt_stim2'),
                'valence_sequence': data.get('valence_sequence'),
                'valence_rt_sequence': data.get('valence_rt_sequence'),
            }
        )
        return JsonResponse({'status': 'success'})
    
    # مرحله رتبه‌بندی مجدد
    if data.get('is_rerating'):
        stimulus_number = data.get('stimulus_number')
        if not stimulus_number:
            return JsonResponse(
                {'status': 'error', 'message': 'شماره محرک الزامی است'}, 
                status=400
            )
        
        PCMReRatingResponse.objects.update_or_create(
            user=request.user,
            stimulus_number=stimulus_number,
            defaults={
                'stimulus_file': data.get('stimulus_file'),
                'valence': data.get('valence'),
                'valence_rt': data.get('valence_rt'),
                'arousal': data.get('arousal'),
                'arousal_rt': data.get('arousal_rt'),
            }
        )
        return JsonResponse({'status': 'success'})
    
    return JsonResponse(
        {'status': 'error', 'message': 'نوع درخواست نامعتبر'}, 
        status=400
    )