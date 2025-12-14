from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from .forms import ParticipantForm
from .models import Participant

def home_view(request):
    if request.method == 'POST':
        form = ParticipantForm(request.POST)
        if form.is_valid():
            participant = form.save()
            request.session['participant_id'] = participant.id 
            return redirect('quiz')
    else:
        form = ParticipantForm()
    
    return render(request, 'index.html', {'form': form})


def quiz_view(request):
    participant_id = request.session.get('participant_id')
    if not participant_id:
        return redirect('home')  # اگر ثبت نشده، برگردان به خانه
    
    participant = get_object_or_404(Participant, id=participant_id)
    
    # اینجا منطق آزمون را پیاده کنید (نمایش سوالات، امتیازدهی و ...)
    return render(request, 'quiz.html', {'participant': participant})
