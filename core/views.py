from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView
from django.contrib.auth import login
from .decorators import questionnaires_required
import json
from django.utils import timezone
import os
import random
from django.templatetags.static import static


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
        
        # محاسبه و ایجاد نتایج برای هر ویژگی
        attributes = Attribute.objects.filter(ویژگی__questionnaire=questionnaire).distinct()  # ویژگی‌های مرتبط با سوالات این پرسشنامه
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
def pcm_view(request):
    context = {
        'title': 'آزمایش حافظه کاری (PCM)',
    }
    return render(request, 'pcm.html', context)



@login_required(login_url='login_or_signup')
@questionnaires_required([1,2,3])
def rating_view(request):
    base_dir = 'sounds'
    practice_files = [
        '0-practice/1.WAV',
        '0-practice/2.WAV',
        '0-practice/3.WAV',
        '0-practice/4.WAV',
        '0-practice/5.WAV',
        '0-practice/6.WAV',
        '0-practice/7.WAV',
        '0-practice/8.WAV',
        '0-practice/9.WAV',
        '0-practice/10.WAV',
    ]
    main_files = [
        'folder1/sound1.mp3',
        'folder2/happy_sound.mp3',
    ]
    random.shuffle(practice_files)
    random.shuffle(main_files)
    practice_files = practice_files[:10]
    def audio_url(filename):
        return static(f'{base_dir}/{filename}')

    practice_urls = [audio_url(f) for f in practice_files]
    main_urls = [audio_url(f) for f in main_files]

    context = {
        'title': 'آزمایش رتبه‌بندی',
        'practice_files': practice_urls,
        'main_files': main_urls,
    }
    return render(request, 'rating.html', context)