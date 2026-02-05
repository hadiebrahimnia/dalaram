# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *

# ------------------- CustomUser -------------------
admin.site.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    # فیلدهایی که در لیست کاربران نمایش داده می‌شوند
    list_display = (
        "username",
        "first_name",
        "last_name",
        "gender",
        "hand",
        "birth_date",
        "is_staff",
        "is_active",
    )
    list_filter = ("is_staff", "is_active", "gender", "hand")

    # فیلدهایی که در فرم ویرایش کاربر نمایش داده می‌شوند
    fieldsets = (
        (None, {"fields": ("username", "password")}),
        (("اطلاعات شخصی"), {
            "fields": (
                "first_name",
                "last_name",
                "birth_date",
                "gender",
                "hand",
                "disorder",
                "drug",
            )
        }),
        (("دسترسی‌ها"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (("تاریخ‌ها"), {"fields": ("last_login", "date_joined")}),
    )

    # فیلدهایی که در فرم ایجاد کاربر جدید نمایش داده می‌شوند
    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "username",
                "password1",
                "password2",
                "first_name",
                "last_name",
                "birth_date",
                "gender",
                "hand",
                "disorder",
                "drug",
                "is_active",
                "is_staff",
                "is_superuser",
            ),
        }),
    )

    search_fields = ("username", "first_name", "last_name")
    ordering = ("username",)

admin.site.register(PCMCueMapping)

# ------------------- Questionnaire & Related -------------------
@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active', 'questions_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'تعداد سوالات'


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1
    fields = ('text', 'value')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text_short', 'questionnaire', 'attribute', 'order', 'question_type_display', 'required')
    list_filter = ('questionnaire', 'attribute', 'question_type', 'required')
    search_fields = ('text', 'questionnaire__title')
    list_editable = ('order',)
    inlines = [ChoiceInline]

    def text_short(self, obj):
        return obj.text[:60] + ('...' if len(obj.text) > 60 else '')
    text_short.short_description = 'متن سوال'

    def question_type_display(self, obj):
        return dict(Question.QUESTION_TYPES).get(obj.question_type, obj.question_type)
    question_type_display.short_description = 'نوع سوال'


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)


# ------------------- Response & Results -------------------
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'choice_text', 'text_answer', 'scale_value', 'RT')
    fields = readonly_fields

    def choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    choice_text.short_description = 'گزینه انتخاب‌شده'


class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    can_delete = False
    readonly_fields = ('attribute', 'raw_score', 'average_score','sum_rt','average_rt')
    fields = readonly_fields


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'respondent_username', 'started_at', 'completed_at', 'is_completed')
    list_filter = ('is_completed', 'questionnaire', 'started_at')
    search_fields = ('questionnaire__title', 'respondent__username')
    readonly_fields = ('started_at', 'completed_at')
    inlines = [AnswerInline, ResultInline]
    date_hierarchy = 'started_at'

    def respondent_username(self, obj):
        return obj.respondent.username if obj.respondent else 'ناشناس'
    respondent_username.short_description = 'کاربر'


# ------------------- مرحله ۰: Rating اصلی (Valence + Arousal) -------------------
@admin.register(RatingPractice)
class RatingPracticeAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'trial', 'stimulus_short', 'valence', 'arousal', 'v_rt', 'a_rt', 'complete', 'created_at')
    list_filter = ('trial', 'created_at')
    search_fields = ('user__username', 'stimulus')
    readonly_fields = ('user', 'trial', 'stimulus', 'valence', 'arousal', 'created_at')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def stimulus_short(self, obj): return obj.stimulus[-40:] if obj.stimulus else '-'
    def v_rt(self, obj): return f"{obj.valence_rt} ms" if obj.valence_rt else '-'
    def a_rt(self, obj): return f"{obj.arousal_rt} ms" if obj.arousal_rt else '-'
    def complete(self, obj): return "✓" if (obj.valence and obj.arousal) else "◐"


@admin.register(RatingResponse)
class RatingResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'stimulus', 'stimulus_file_short', 'valence', 'arousal', 'v_rt', 'a_rt', 'created_at')
    list_filter = ('valence', 'arousal', 'created_at')
    search_fields = ('user__username', 'stimulus_', 'stimulus_file')
    readonly_fields = ('user', 'stimulus_file', 'stimulus', 'valence', 'arousal', 'created_at')
    ordering = ('-created_at',)

    def user_username(self, obj): return obj.user.username
    def stimulus_file_short(self, obj): return obj.stimulus_file[-60:] + '...' if len(obj.stimulus_file) > 60 else obj.stimulus_file
    def v_rt(self, obj): return f"{obj.valence_rt} ms" if obj.valence_rt else '-'
    def a_rt(self, obj): return f"{obj.arousal_rt} ms" if obj.arousal_rt else '-'
    


# ------------------- مرحله ۱: تمرین تشخیص توالی -------------------
class PCMSequencePracticeResponseInline(admin.TabularInline):
    model = PCMSequencePracticeResponse
    extra = 0
    can_delete = False
    readonly_fields = ('trial', 'cue_short', 'stimulus1_short', 'stimulus2_short','category_stim1','category_stim2', 'user_response', 'is_correct_display', 'created_at')
    fields = readonly_fields
    ordering = ('trial',)

    def cue_short(self, obj): return obj.cue[-30:]
    def stimulus1_short(self, obj): return obj.stimulus1[-30:] if obj.stimulus1 else '-'
    def stimulus2_short(self, obj): return obj.stimulus2[-30:] if obj.stimulus2 else '-'
    def is_correct_display(self, obj): return "✓" if obj.is_correct else "✗" if obj.is_correct is False else "-"


@admin.register(PCMSequencePracticeResponse)
class PCMSequencePracticeResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'trial', 'cue_short','category_stim2','category_stim1', 'user_response', 'is_correct_display', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'cue', 'user_response')
    readonly_fields = ('user', 'trial', 'cue', 'stimulus1', 'stimulus2','category_stim1','category_stim2', 'user_response', 'is_correct', 'created_at')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def cue_short(self, obj): return obj.cue[-40:]
    def is_correct_display(self, obj): return "✓ درست" if obj.is_correct else "✗ غلط" if obj.is_correct is False else "—"


# ------------------- مرحله ۲: تمرین رتبه‌بندی خوشایندی -------------------
@admin.register(PCMValencePracticeResponse)
class PCMValencePracticeResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'trial', 'cue_short','stimulus1','stimulus2','category_stim1','category_stim2', 'v1', 'v2', 'v_seq', 'rt1', 'rt2', 'rt_seq', 'created_at')
    list_filter = ('trial', 'created_at')
    search_fields = ('user__username', 'cue')
    readonly_fields = ('user', 'trial', 'cue', 'stimulus1', 'stimulus2', 'valence_stim1', 'valence_stim2', 'valence_sequence', 'created_at')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def cue_short(self, obj): return obj.cue[-30:]
    def v1(self, obj): return obj.valence_stim1 or '-'
    def v2(self, obj): return obj.valence_stim2 or '-'
    def v_seq(self, obj): return obj.valence_sequence or '-'
    def rt1(self, obj): return f"{obj.valence_rt_stim1} ms" if obj.valence_rt_stim1 else '-'
    def rt2(self, obj): return f"{obj.valence_rt_stim2} ms" if obj.valence_rt_stim2 else '-'
    def rt_seq(self, obj): return f"{obj.valence_rt_sequence} ms" if obj.valence_rt_sequence else '-'
    # def complete(self, obj): return "✓" if obj.is_complete() else "◐" id.complete.short_description = 'کامل'


# ------------------- مرحله ۳: آزمون اصلی PCM -------------------

class PCMCatchResponseInline(admin.TabularInline):
    model = PCMCatchResponse
    extra = 0
    can_delete = False
    readonly_fields = ('trial', 'cue_short', 'stimulus1_short', 'stimulus2_short','category_stim1','category_stim2', 'user_response', 'is_correct_display', 'created_at')
    fields = readonly_fields
    ordering = ('trial',)

    def cue_short(self, obj): return obj.cue[-30:]
    def stimulus1_short(self, obj): return obj.stimulus1[-30:] if obj.stimulus1 else '-'
    def stimulus2_short(self, obj): return obj.stimulus2[-30:] if obj.stimulus2 else '-'
    def is_correct_display(self, obj): return "✓" if obj.is_correct else "✗" if obj.is_correct is False else "-"


@admin.register(PCMCatchResponse)
class PCMCatchResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'trial','block', 'cue_short','category_stim2','category_stim1', 'user_response', 'is_correct_display', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'cue', 'user_response')
    readonly_fields = ('user', 'trial','block', 'cue', 'stimulus1', 'stimulus2','category_stim1','category_stim2', 'user_response', 'is_correct', 'created_at')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def cue_short(self, obj): return obj.cue[-40:]
    def is_correct_display(self, obj): return "✓ درست" if obj.is_correct else "✗ غلط" if obj.is_correct is False else "—"



@admin.register(PCMMainResponse)
class PCMMainResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'block', 'trial', 'cue_short', 'v1', 'v2', 'v_seq', 'consistent', 'complete', 'created_at')
    list_filter = ('block', 'is_consistent', 'created_at')
    search_fields = ('user__username', 'cue')
    readonly_fields = ('user', 'block', 'trial', 'cue', 'stimulus1', 'stimulus2', 'expected_sequence', 'is_consistent', 'created_at')
    ordering = ('user', 'block', 'trial')

    def user_username(self, obj): return obj.user.username
    def cue_short(self, obj): return obj.cue[-30:]
    def v1(self, obj): return obj.valence_stim1 or '-'
    def v2(self, obj): return obj.valence_stim2 or '-'
    def v_seq(self, obj): return obj.valence_sequence or '-'
    def consistent(self, obj): return "✓" if obj.is_consistent else "✗"
    def complete(self, obj): return "✓" if obj.is_complete() else "◐"


# ------------------- مرحله ۴: تمرین رتبه‌بندی Valence + Arousal -------------------
@admin.register(RatingPracticeResponse)
class RatingPracticeResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'trial', 'stimulus_short', 'valence', 'arousal', 'v_rt', 'a_rt', 'complete', 'created_at')
    list_filter = ('trial', 'created_at')
    search_fields = ('user__username', 'stimulus')
    readonly_fields = ('user', 'trial', 'stimulus', 'valence', 'arousal', 'created_at')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def stimulus_short(self, obj): return obj.stimulus[-40:] if obj.stimulus else '-'
    def v_rt(self, obj): return f"{obj.valence_rt} ms" if obj.valence_rt else '-'
    def a_rt(self, obj): return f"{obj.arousal_rt} ms" if obj.arousal_rt else '-'
    def complete(self, obj): return "✓" if (obj.valence and obj.arousal) else "◐"


# ------------------- مرحله ۵: رتبه‌بندی نهایی صداها -------------------
@admin.register(RatingMainResponse)
class RatingMainResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username', 'stimulus_number', 'stimulus_file_short', 'valence', 'arousal', 'v_rt', 'a_rt', 'created_at')
    list_filter = ('valence', 'arousal', 'created_at')
    search_fields = ('user__username', 'stimulus_number', 'stimulus_file')
    readonly_fields = ('user', 'stimulus_file', 'stimulus_number', 'valence', 'arousal', 'created_at')
    ordering = ('-created_at',)

    def user_username(self, obj): return obj.user.username
    def stimulus_file_short(self, obj): return obj.stimulus_file[-60:] + '...' if len(obj.stimulus_file) > 60 else obj.stimulus_file
    def v_rt(self, obj): return f"{obj.valence_rt} ms" if obj.valence_rt else '-'
    def a_rt(self, obj): return f"{obj.arousal_rt} ms" if obj.arousal_rt else '-'
    
