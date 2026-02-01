"""
URL configuration for dalaram project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from core.views import *
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('temp_home', temp_home_view, name='temp_home'),
    path('taninyar/', taninyar, name='taninyar'),
    path('', home_view, name='home'),

    path('login/', login_or_signup, name='login_or_signup'),
    path(
        'logout/',
        auth_views.LogoutView.as_view(next_page='login_or_signup'),  # یا نام url دلخواه
        name='logout',
    ),
    path('complete-profile/', complete_profile, name='complete_profile'),
    path('experiment/rating/', rating_view, name='rating'),
    path('rating/save/', rating_save_response, name='rating_save'),
    path('experiment/pcm/', pcm_view, name='pcm'),
    path('pcm/save/', pcm_save_response, name='pcm_save'),

    path('questionnaire/<int:pk>/respond/', respond_questionnaire, name='respond_questionnaire'),
]
