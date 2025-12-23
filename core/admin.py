from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *

admin.site.register(CustomUser, UserAdmin)


@admin.register(Questionnaire)
class QuestionnaireAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active', 'questions_count')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title', 'description')
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'is_active')
        }),
        ('اطلاعات پیشرفته', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'تعداد سؤالات'


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1
    fields = ('text', 'value')
    verbose_name = 'گزینه'
    verbose_name_plural = 'گزینه‌ها'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'questionnaire', 'question_type_display', 'order', 'required')
    list_filter = ('questionnaire__title', 'question_type', 'required')
    search_fields = ('text', 'questionnaire__title')
    list_editable = ('order',)
    inlines = [ChoiceInline]

    def question_type_display(self, obj):
        return dict(Question.QUESTION_TYPES).get(obj.question_type, obj.question_type)
    question_type_display.short_description = 'نوع سؤال'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'value', 'question', 'questionnaire_title')
    list_filter = ('question__questionnaire__title',)
    search_fields = ('text', 'question__text')

    def questionnaire_title(self, obj):
        return obj.question.questionnaire.title
    questionnaire_title.short_description = 'پرسشنامه'


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'get_choice_text', 'text_answer', 'scale_value')
    fields = ('question', 'get_choice_text', 'text_answer', 'scale_value')

    def get_choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    get_choice_text.short_description = 'گزینه انتخاب‌شده'

    def has_add_permission(self, request, obj):
        return False  # جلوگیری از اضافه کردن دستی جواب در ادمین


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'choice_text', 'text_answer_short', 'scale_value')
    list_filter = ('response__questionnaire', 'question')
    search_fields = ('question__text', 'choice__text', 'text_answer')
    readonly_fields = ('response', 'question', 'choice', 'text_answer', 'scale_value')

    def choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    choice_text.short_description = 'گزینه'

    def text_answer_short(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + ('...' if len(obj.text_answer) > 50 else '')
        return '-'
    text_answer_short.short_description = 'پاسخ متنی'

    def has_add_permission(self, request, obj=None):
        return False  # جواب‌ها فقط از طریق فرم پاسخ‌دهی اضافه شوند

    def has_change_permission(self, request, obj=None):
        return False  # جلوگیری از ویرایش دستی جواب‌ها
    
@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active',)
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)
    fieldsets = (
        (None, {
            'fields': ('title', 'is_active')
        }),
        ('اطلاعات پیشرفته', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

# Inline برای نمایش نتایج در صفحه Response
class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    can_delete = False
    fields = ('attribute', 'raw_score', 'num_questions', 'average_score', 'sum_rt', 'average_rt')
    readonly_fields = ('attribute', 'raw_score', 'num_questions', 'average_score', 'sum_rt', 'average_rt')

    def has_add_permission(self, request, obj):
        return False  # نتایج فقط به صورت خودکار محاسبه و ذخیره می‌شوند

    def has_change_permission(self, request, obj=None):
        return False  # جلوگیری از ویرایش دستی نتایج

@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = ('questionnaire', 'respondent_username', 'started_at', 'completed_at', 'is_completed', 'answers_count')
    list_filter = ('is_completed', 'questionnaire', 'started_at')
    readonly_fields = ('started_at', 'completed_at', 'questionnaire', 'respondent')
    search_fields = ('questionnaire__title', 'respondent__username')
    inlines = [AnswerInline, ResultInline]  # اضافه کردن ResultInline
    date_hierarchy = 'started_at'

    def respondent_username(self, obj):
        return obj.respondent.username if obj.respondent else 'ناشناس (مهمان)'
    respondent_username.short_description = 'پاسخ‌دهنده'

    def answers_count(self, obj):
        return obj.answers.count()
    answers_count.short_description = 'تعداد پاسخ‌ها'


# ادمین اختصاصی برای مدل Result
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = (
        'questionnaire',
        'respondent_username',
        'attribute',
        'raw_score',
        'num_questions',
        'average_score',
        'sum_rt',
        'average_rt_formatted',
        'response_started_at'
    )
    list_filter = (
        'questionnaire',
        'attribute',
        'response__is_completed',
        'response__started_at'
    )
    search_fields = (
        'questionnaire__title',
        'user__username',
        'attribute__title',
        'response__respondent__username'
    )
    readonly_fields = (
        'user', 'questionnaire', 'response', 'attribute',
        'raw_score', 'num_questions', 'average_score',
        'sum_rt', 'average_rt'
    )
    fieldsets = (
        ('اطلاعات کلی', {
            'fields': ('user', 'questionnaire', 'response', 'attribute')
        }),
        ('نمرات و آمار', {
            'fields': (
                'raw_score', 'num_questions', 'average_score',
                'sum_rt', 'average_rt'
            )
        }),
    )

    def respondent_username(self, obj):
        return obj.user.username if obj.user else 'نامشخص'
    respondent_username.short_description = 'کاربر'

    def response_started_at(self, obj):
        return obj.response.started_at
    response_started_at.short_description = 'زمان شروع آزمون'
    response_started_at.admin_order_field = 'response__started_at'

    def average_rt_formatted(self, obj):
        return f"{obj.average_rt:.2f} ثانیه" if obj.average_rt else '-'
    average_rt_formatted.short_description = 'میانگین RT'

    # جلوگیری از اضافه کردن یا ویرایش دستی نتایج
    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        # اختیاری: اگر بخواهید اجازه حذف دستی بدهید، True برگردانید
        return False