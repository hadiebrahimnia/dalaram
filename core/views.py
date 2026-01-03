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

@login_required(login_url='login_or_signup')
@questionnaires_required([1, 2, 3])
def pcm_view(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) if request.body else {}
        except json.JSONDecodeError:
            return JsonResponse({'status': 'error', 'message': 'JSON نامعتبر'}, status=400)

        is_practice = data.get('is_practice', False)

        if is_practice:
            practice_trial = data.get('practice_trial')
            if practice_trial is None:
                return JsonResponse({'status': 'error', 'message': 'شماره تریال تمرینی الزامی است'}, status=400)

            defaults = {
                'cue': data.get('cue'),
                'stimulus1': data.get('stimulus1'),
                'stimulus2': data.get('stimulus2'),
                'expected_sequence': data.get('expected_sequence'),
                'practice_response': data.get('user_response'),
                'practice_correct': data.get('practice_correct'),
            }

            pcm_response, created = PCMResponse.objects.update_or_create(
                user=request.user,
                block=0,
                trial=practice_trial,
                defaults=defaults
            )

        else:
            block = data.get('block')
            trial = data.get('trial')
            if block is None or trial is None:
                return JsonResponse({'status': 'error', 'message': 'block و trial الزامی هستند'}, status=400)

            defaults = {
                'cue': data.get('cue'),
                'stimulus1': data.get('stimulus1'),
                'stimulus2': data.get('stimulus2'),
                'expected_sequence': data.get('expected_sequence'),  # رشته
                'category_stim1': data.get('category_stim1'),
                'category_stim2': data.get('category_stim2'),
                'valence_stim1': data.get('valence_stim1'),
                'valence_rt_stim1': data.get('valence_rt_stim1'),
                'valence_stim2': data.get('valence_stim2'),
                'valence_rt_stim2': data.get('valence_rt_stim2'),
                'valence_sequence': data.get('valence_sequence'),
                'valence_rt_sequence': data.get('valence_rt_sequence'),
            }

            pcm_response, created = PCMResponse.objects.update_or_create(
                user=request.user,
                block=block,
                trial=trial,
                defaults=defaults
            )

        return JsonResponse({'status': 'success', 'created': created})

    if request.method != 'GET':
        return JsonResponse({'status': 'error', 'message': 'فقط GET و POST پشتیبانی می‌شود'}, status=405)

    NUM_BLOCKS = 4
    TRIALS_PER_BLOCK = 20
    PRACTICE_TRIALS = 30
    PRACTICE_SUCCESS_THRESHOLD = 0.8
    INCONSISTENT_TRIALS_RATIO = 0.2

    CUE_CATEGORIES = {
        '1': ['CUE/1/1.mp3'],
        '2': ['CUE/2/2.mp3'],
        '3': ['CUE/3/3.mp3'],
    }

    categories = list(CUE_CATEGORIES.keys())
    if len(categories) < 3:
        return JsonResponse({'error': 'حداقل ۳ کیو لازم است'}, status=500)

    POSSIBLE_SEQUENCES = [
        'Neutral-Neutral',
        'Negative-Neutral',
        'Neutral-Negative',
    ]

    sequences_shuffled = POSSIBLE_SEQUENCES.copy()
    random.shuffle(sequences_shuffled)
    category_to_sequence = dict(zip(categories, sequences_shuffled))

    cues_mapping = {}
    for category, sequence in category_to_sequence.items():
        for cue_file in CUE_CATEGORIES[category]:
            cues_mapping[cue_file] = sequence

    full_path_cues_mapping = {
        f'/static/sounds/{key}': value for key, value in cues_mapping.items()
    }

    neutral_files = [
        '5-MP-MA/102.WAV','5-MP-MA/104.WAV','5-MP-MA/107.WAV','5-MP-MA/111.WAV','5-MP-MA/113.WAV','5-MP-MA/120.WAV','5-MP-MA/130.WAV','5-MP-MA/132.WAV','5-MP-MA/152.WAV','5-MP-MA/170.WAV','5-MP-MA/225.WAV','5-MP-MA/245.WAV','5-MP-MA/246.WAV','5-MP-MA/251.WAV','5-MP-MA/252.WAV','5-MP-MA/320.WAV','5-MP-MA/322.WAV','5-MP-MA/358.WAV','5-MP-MA/361.WAV','5-MP-MA/364.WAV','5-MP-MA/368.WAV','5-MP-MA/370.WAV','5-MP-MA/373.WAV','5-MP-MA/374.WAV','5-MP-MA/375.WAV','5-MP-MA/376.WAV','5-MP-MA/382.WAV','5-MP-MA/403.WAV','5-MP-MA/410.WAV','5-MP-MA/425.WAV','5-MP-MA/500.WAV','5-MP-MA/627.WAV','5-MP-MA/698.WAV','5-MP-MA/700.WAV','5-MP-MA/701.WAV','5-MP-MA/702.WAV','5-MP-MA/705.WAV','5-MP-MA/706.WAV','5-MP-MA/720.WAV','5-MP-MA/722.WAV','5-MP-MA/723.WAV','5-MP-MA/724.WAV','5-MP-MA/728.WAV','5-MP-MA/729.WAV',
    ]

    negative_files = [
        '7-LP-HA/105.WAV','7-LP-HA/106.WAV','7-LP-HA/115.WAV','7-LP-HA/116.WAV','7-LP-HA/133.WAV','7-LP-HA/134.WAV','7-LP-HA/244.WAV','7-LP-HA/255.WAV','7-LP-HA/260.WAV','7-LP-HA/261.WAV','7-LP-HA/275.WAV','7-LP-HA/276.WAV','7-LP-HA/277.WAV','7-LP-HA/278.WAV','7-LP-HA/279.WAV','7-LP-HA/281.WAV','7-LP-HA/282.WAV','7-LP-HA/283.WAV','7-LP-HA/284.WAV','7-LP-HA/285.WAV','7-LP-HA/286.WAV','7-LP-HA/288.WAV','7-LP-HA/289.WAV','7-LP-HA/290.WAV','7-LP-HA/292.WAV','7-LP-HA/296.WAV','7-LP-HA/310.WAV','7-LP-HA/312.WAV','7-LP-HA/319.WAV','7-LP-HA/380.WAV','7-LP-HA/420.WAV','7-LP-HA/422.WAV','7-LP-HA/423.WAV','7-LP-HA/424.WAV','7-LP-HA/501.WAV','7-LP-HA/502.WAV','7-LP-HA/600.WAV','7-LP-HA/624.WAV','7-LP-HA/625.WAV','7-LP-HA/626.WAV','7-LP-HA/699.WAV','7-LP-HA/709.WAV','7-LP-HA/711.WAV','7-LP-HA/712.WAV','7-LP-HA/713.WAV','7-LP-HA/714.WAV','7-LP-HA/719.WAV','7-LP-HA/730.WAV','7-LP-HA/732.WAV','7-LP-HA/910.WAV',
        '8-LP-MA/241.WAV','8-LP-MA/242.WAV','8-LP-MA/243.WAV','8-LP-MA/250.WAV','8-LP-MA/280.WAV','8-LP-MA/293.WAV','8-LP-MA/295.WAV','8-LP-MA/611.WAV','8-LP-MA/703.WAV',
    ]

    neutral_files = list(set(neutral_files))
    negative_files = list(set(negative_files))
    random.shuffle(neutral_files)
    random.shuffle(negative_files)

    def audio_url(filename):
        return staticfiles_storage.url(f'sounds/{filename}')

    cue_urls = [audio_url(cue) for cue in cues_mapping.keys()]
    neutral_urls = [audio_url(f) for f in neutral_files]
    negative_urls = [audio_url(f) for f in negative_files]

    context = {
        'title': 'آزمایش حافظه کاری (PCM)',
        'cue_urls': json.dumps(cue_urls),
        'neutral_urls': json.dumps(neutral_urls),
        'negative_urls': json.dumps(negative_urls),
        'cues_mapping': json.dumps(full_path_cues_mapping),
        'num_blocks': NUM_BLOCKS,
        'trials_per_block': TRIALS_PER_BLOCK,
        'practice_trials': PRACTICE_TRIALS,
        'practice_success_threshold': PRACTICE_SUCCESS_THRESHOLD,
        'inconsistent_trials_ratio': INCONSISTENT_TRIALS_RATIO,
    }

    return render(request, 'pcm.html', context)