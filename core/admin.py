# admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import *
from django.utils.html import format_html
from django.utils.safestring import mark_safe
import json

@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('id', 'text', 'value', 'question')
    list_filter = ('value',)
    search_fields = ('text',)

class ChoiceInline(admin.TabularInline):  # یا StackedInline
    model = Choice
    extra = 1  # تعداد فرم خالی اضافی
    fields = ('text', 'value')  # یا هر فیلدی که دارید

@admin.register(FeedbackSettings)
class PCMSettingsAdmin(admin.ModelAdmin):
    list_display = ('feedback_mode', 'feedback_first_n', 'feedback_until_correct', 'feedback_correct_consecutive')
    
    fieldsets = (
        ('تنظیمات فیدبک مرحله تمرین توالی', {
            'fields': (
                'feedback_mode',
                'feedback_first_n',
                'feedback_until_correct',
                'feedback_correct_consecutive',
            )
        }),
    )


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


# ==============================
# ادمین مخصوص PCMCueMapping
# ==============================
@admin.register(PCMCueMapping)
class PCMCueMappingAdmin(admin.ModelAdmin):
    list_display = ('user', 'mapping_preview', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__username', 'user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('user', 'mapping_pretty', 'created_at')
    ordering = ('-created_at',)

    def mapping_preview(self, obj):
        if not obj.mapping:
            return "-"
        
        lines = []
        for cue, seq in obj.mapping.items():
            # فقط عدد قبل از .mp3 رو بگیر
            cue_name = cue.split('/')[-1].replace('.mp3', '')
            
            # تبدیل Neutral-Negative به Neutral -> Negative
            pretty_seq = seq.replace('-', ' -> ')
            
            lines.append(f"<b>{cue_name}</b> → {pretty_seq}")
        
        return mark_safe("<br>".join(lines))

    mapping_preview.short_description = "نگاشت Cue → Sequence"

    def mapping_pretty(self, obj):
        if not obj.mapping:
            return "-"
        pretty = json.dumps(obj.mapping, indent=2, ensure_ascii=False)
        return format_html(
            "<pre style='direction:ltr; background:#f5f5f5; padding:12px; border-radius:6px;'>{}</pre>",
            pretty
        )
    
    mapping_pretty.short_description = "نگاشت کامل (JSON)"


class CustomUserAdmin(admin.ModelAdmin):
    list_display = (
        'username',
        'email',
        'first_name',
        'last_name',
        'is_staff',
        'cue_mapping_preview',
        'date_joined',
    )
    search_fields = ('username', 'email', 'first_name', 'last_name')
    list_filter = ('is_staff', 'is_active', 'date_joined')

    def cue_mapping_preview(self, obj):
        try:
            mapping_obj = obj.cue_mapping
        except (PCMCueMapping.DoesNotExist, AttributeError):
            try:
                mapping_obj = PCMCueMapping.objects.get(user=obj)
            except PCMCueMapping.DoesNotExist:
                return format_html('<span style="color:#999;">ندارد</span>')

        if not mapping_obj.mapping:
            return "-"

        lines = []
        for cue, seq in mapping_obj.mapping.items():
            cue_name = cue.split('/')[-1].replace('.mp3', '')
            pretty_seq = seq.replace('-', ' -> ')
            lines.append(f"<b>{cue_name}</b> → {pretty_seq}")
        
        return mark_safe("<br>".join(lines))

    cue_mapping_preview.short_description = "نگاشت Cue به Sequence"

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
    list_display = (
        'user_username',
        'trial',
        'stimulus_short',
        'stimulus',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',
        
        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'complete',
        'is_active',
        'created_at',
    )

    list_filter = (
        'trial',
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'stimulus',
    )

    readonly_fields = (
        'user',
        'trial',
        'stimulus',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',


        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'created_at',
        'is_active'
    )

    ordering = (
        'user',
        'trial',
    )

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description='محرک')
    def stimulus_short(self, obj):
        return obj.stimulus[-40:] if obj.stimulus else "-"

    @admin.display(description='کامل')
    def complete(self, obj):
        return (
            "✓"
            if obj.valence is not None and obj.arousal is not None
            else "◐"
        )


@admin.register(RatingResponse)
class RatingResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'stimulus',
        'stimulus_short',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'complete',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'stimulus',
        'stimulus_file',
    )

    readonly_fields = (
        'user',
        'trial',
        'stimulus',
        'stimulus_file',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'created_at',
        'is_active'
    )

    ordering = (
        'user',
        'trial',
        'stimulus',
    )

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description='فایل محرک')
    def stimulus_short(self, obj):
        return obj.stimulus_file[-40:] if obj.stimulus_file else "-"

    @admin.display(description='کامل')
    def complete(self, obj):
        return "✓" if obj.is_complete() else "◐"
    




# ------------------- مرحله 1: تمرین رتبه‌بندی خوشایندی -------------------
@admin.register(PCMValencePracticeResponse)
class PCMValencePracticeResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'category_stim1',
        'category_stim2',

        'valence_stim1',
        'valence_rt_stim1',
        'valence_delay_number_stim1',
        'valence_input_method_stim1',

        'valence_stim2',
        'valence_rt_stim2',
        'valence_delay_number_stim2',
        'valence_input_method_stim2',

        'valence_sequence',
        'valence_rt_sequence',
        'valence_delay_number_sequence',
        'valence_input_method_sequence',

        'is_active',
        'created_at',
    )

    list_filter = (
        'trial',
        'category_stim1',
        'category_stim2',
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'cue',
        'stimulus1',
        'stimulus2',
    )

    readonly_fields = (
        'user',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'category_stim1',
        'category_stim2',

        'valence_stim1',
        'valence_rt_stim1',
        'valence_delay_number_stim1',
        'valence_input_method_stim1',

        'valence_stim2',
        'valence_rt_stim2',
        'valence_delay_number_stim2',
        'valence_input_method_stim2',

        'valence_sequence',
        'valence_rt_sequence',
        'valence_delay_number_sequence',
        'valence_input_method_sequence',

        'created_at',
        'is_active'
    )

    ordering = ('-created_at', 'trial')

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    
# ------------------- مرحله 2: تمرین تشخیص توالی -------------------
class PCMSequencePracticeResponseInline(admin.TabularInline):
    model = PCMSequencePracticeResponse
    extra = 0
    can_delete = False
    readonly_fields = ('block','trial', 'stimulus1_short', 'stimulus2_short','category_stim1','category_stim2', 'user_response', 'delay_number','response_input_method','expected_sequence','is_consistent','is_correct_display', 'created_at')
    fields = readonly_fields
    ordering = ('trial',)

    def cue_short(self, obj): return obj.cue[-30:]
    def stimulus1_short(self, obj): return obj.stimulus1[-30:] if obj.stimulus1 else '-'
    def stimulus2_short(self, obj): return obj.stimulus2[-30:] if obj.stimulus2 else '-'
    def is_correct_display(self, obj): return "✓" if obj.is_correct else "✗" if obj.is_correct is False else "-"


@admin.register(PCMSequencePracticeResponse)
class PCMSequencePracticeResponseAdmin(admin.ModelAdmin):
    list_display = ('user_username','block', 'trial','category_stim2','category_stim1', 'user_response','response_rt' ,'delay_number','response_input_method','is_correct_display','is_consistent','expected_sequence', 'created_at')
    list_filter = ('user', 'created_at')
    search_fields = ('user__username', 'cue', 'user_response')
    readonly_fields = ('user','block', 'trial', 'cue', 'stimulus1', 'stimulus2','category_stim1','category_stim2', 'expected_sequence','is_consistent','user_response','is_correct','response_rt','delay_number','response_input_method', 'created_at','is_active')
    ordering = ('-created_at', 'trial')

    def user_username(self, obj): return obj.user.username
    def cue_short(self, obj): return obj.cue[-40:]
    def is_correct_display(self, obj): return "✓ درست" if obj.is_correct else "✗ غلط" if obj.is_correct is False else "—"


class PCMSequenceCatchResponseInline(admin.TabularInline):
    model = PCMSequenceCatchResponse
    extra = 0
    can_delete = False

    readonly_fields = (
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'created_at',
        'is_active',
    )

    fields = readonly_fields
    ordering = ('trial',)


@admin.register(PCMSequenceCatchResponse)
class PCMSequenceCatchResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'is_active',
        'created_at',
    )

    list_filter = (
        'user',
        'block',
        'is_correct',
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'cue',
        'user_response',
    )

    readonly_fields = (
        'user',
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'created_at',
        'is_active'
    )

    ordering = ('-created_at', 'trial')

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username


# ------------------- مرحله ۳: آزمون اصلی PCM -------------------

class PCMCatchResponseInline(admin.TabularInline):
    model = PCMCatchResponse
    extra = 0
    can_delete = False

    readonly_fields = (
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'created_at',
        'is_active',
    )

    fields = readonly_fields
    ordering = ('trial',)


@admin.register(PCMCatchResponse)
class PCMCatchResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'is_active',
        'created_at',
    )

    list_filter = (
        'user',
        'block',
        'is_correct',
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'cue',
        'user_response',
    )

    readonly_fields = (
        'user',
        'trial',
        'block',
        'cue',
        'user_response',
        'response_rt',
        'delay_number',
        'response_input_method',
        'is_correct',
        'created_at',
        'is_active'
    )

    ordering = ('-created_at', 'trial')

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username



@admin.register(PCMMainResponse)
class PCMMainResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence',
        'consistent',
        'category_stim1',
        'category_stim2',

        'valence_stim1',
        'valence_rt_stim1',
        'valence_delay_number_stim1',
        'valence_input_method_stim1',

        'valence_stim2',
        'valence_rt_stim2',
        'valence_delay_number_stim2',
        'valence_input_method_stim2',

        'valence_sequence',
        'valence_rt_sequence',
        'valence_delay_number_sequence',
        'valence_input_method_sequence',

        'complete',
        'is_active',
        'created_at',
    )

    list_filter = (
        'block',
        'is_consistent',
        'is_active',
        'category_stim1',
        'category_stim2',
        'created_at',
    )

    search_fields = (
        'user__username',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence',
    )

    readonly_fields = (
        'user',
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence',
        'is_consistent',

        'category_stim1',
        'category_stim2',

        'valence_stim1',
        'valence_rt_stim1',
        'valence_delay_number_stim1',
        'valence_input_method_stim1',

        'valence_stim2',
        'valence_rt_stim2',
        'valence_delay_number_stim2',
        'valence_input_method_stim2',

        'valence_sequence',
        'valence_rt_sequence',
        'valence_delay_number_sequence',
        'valence_input_method_sequence',

        'created_at',
        'is_active'
    )

    ordering = ('-created_at', 'user',)

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description='کیو')
    def cue_short(self, obj):
        return obj.cue[-30:] if obj.cue else "-"

    @admin.display(description='سازگار')
    def consistent(self, obj):
        return "✓" if obj.is_consistent else "✗"

    @admin.display(description='کامل')
    def complete(self, obj):
        return "✓" if obj.is_complete() else "◐"


# ------------------- مرحله ۴: تمرین رتبه‌بندی Valence + Arousal -------------------
@admin.register(RatingPracticeResponse)
class RatingPracticeResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'stimulus_short',
        'stimulus',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'complete',
        'is_active',
        'created_at',
    )

    list_filter = (
        'trial',
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'stimulus',
    )

    readonly_fields = (
        'user',
        'trial',
        'stimulus',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'created_at',
        'is_active'
    )

    ordering = ('-created_at', 'trial')

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description='محرک')
    def stimulus_short(self, obj):
        return obj.stimulus[-40:] if obj.stimulus else "-"

    @admin.display(description='کامل')
    def complete(self, obj):
        return (
            "✓"
            if obj.valence is not None and obj.arousal is not None
            else "◐"
        )


@admin.register(RatingMainResponse)
class RatingMainResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'stimulus_number',
        'stimulus_short',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'complete',
        'is_active',
        'created_at',
    )

    list_filter = (
        'is_active',
        'created_at',
    )

    search_fields = (
        'user__username',
        'stimulus_number',
        'stimulus_file',
    )

    readonly_fields = (
        'user',
        'trial',
        'stimulus_file',
        'stimulus_number',

        'valence',
        'valence_rt',
        'valence_delay_number',
        'valence_input_method',

        'arousal',
        'arousal_rt',
        'arousal_delay_number',
        'arousal_input_method',

        'created_at',
        'is_active',
    )

    ordering = (
        'user',
        'trial',
        'stimulus_number',
    )

    @admin.display(description='کاربر')
    def user_username(self, obj):
        return obj.user.username

    @admin.display(description='محرک')
    def stimulus_short(self, obj):
        return obj.stimulus_file[-40:] if obj.stimulus_file else "-"

    @admin.display(description='کامل')
    def complete(self, obj):
        return (
            "✓"
            if obj.valence is not None and obj.arousal is not None
            else "◐"
        )

# -------------------  دستگاه شرکت کننده-------------------
@admin.register(DeviceLog)
class DeviceLogAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'stage',
        'device_type',
        'os',
        'browser',
        'screen_width',
        'screen_height',
        'is_touch',
        'audio_volume',
        'created_at',
    )
    
    list_filter = (
        'device_type',
        'os',
        'browser',
        'is_touch',
        'stage',
        'created_at',
    )
    
    search_fields = (
        'user__username',
        'user__email',
        'stage',
        'device_type',
        'os',
        'browser',
    )
    
    readonly_fields = (
        'user',
        'stage',
        'device_type',
        'os',
        'browser',
        'screen_width',
        'screen_height',
        'is_touch',
        'audio_volume',
        'created_at',
    )
    
    ordering = ('-created_at',)
    
    list_per_page = 50

    # برای اینکه کسی نتواند دستی رکورد جدید بسازد یا ویرایش کند
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False



admin.site.register(VolumeLog)
