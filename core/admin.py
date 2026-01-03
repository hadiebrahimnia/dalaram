from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


# ثبت CustomUser با UserAdmin استاندارد
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
    list_display = ('text', 'order', 'attribute', 'questionnaire', 'question_type_display', 'required')
    list_filter = ('questionnaire__title', 'question_type', 'required')
    search_fields = ('text', 'questionnaire__title')
    list_editable = ('order',)
    inlines = [ChoiceInline]

    def question_type_display(self, obj):
        return dict(Question.QUESTION_TYPES).get(obj.question_type, obj.question_type)
    question_type_display.short_description = 'نوع سؤال'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'value', 'question__order', 'question', 'questionnaire_title')
    list_filter = ('question__questionnaire__title',)
    search_fields = ('text', 'question__text')

    def questionnaire_title(self, obj):
        return obj.question.questionnaire.title
    questionnaire_title.short_description = 'پرسشنامه'


# Inline برای نمایش جواب‌ها در صفحه Response
class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'get_choice_text', 'text_answer', 'scale_value', 'RT')
    fields = ('question', 'get_choice_text', 'text_answer', 'scale_value', 'RT')

    def get_choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    get_choice_text.short_description = 'گزینه انتخاب‌شده'

    def has_add_permission(self, request, obj):
        return False


# Inline برای نمایش نتایج در صفحه Response
class ResultInline(admin.TabularInline):
    model = Result
    extra = 0
    can_delete = False
    readonly_fields = ('attribute', 'raw_score', 'num_questions', 'average_score', 'sum_rt', 'average_rt')
    fields = ('attribute', 'raw_score', 'num_questions', 'average_score', 'sum_rt', 'average_rt')

    def has_add_permission(self, request, obj):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(Response)
class ResponseAdmin(admin.ModelAdmin):
    list_display = (
        'questionnaire',
        'respondent_username',
        'started_at',
        'completed_at',
        'is_completed',
        'answers_count'
    )
    list_filter = ('is_completed', 'questionnaire', 'started_at')
    readonly_fields = ('started_at', 'completed_at', 'questionnaire', 'respondent')
    search_fields = ('questionnaire__title', 'respondent__username')
    inlines = [AnswerInline, ResultInline]
    date_hierarchy = 'started_at'

    def respondent_username(self, obj):
        return obj.respondent.username if obj.respondent else 'ناشناس (مهمان)'
    respondent_username.short_description = 'پاسخ‌دهنده'

    def answers_count(self, obj):
        return obj.answers.count()
    answers_count.short_description = 'تعداد پاسخ‌ها'

    # --- مهم: اجازه حذف Response حتی با وجود Result و Answer ---
    def has_delete_permission(self, request, obj=None):
        # فقط کاربرانی که اجازه حذف Response دارند (معمولاً staff/superuser)
        if not request.user.has_perm('core.delete_response'):
            return False
        # چون CASCADE داریم، نیازی به چک جداگانه Result نیست
        # اما اگر بخواهید احتیاط بیشتری کنید:
        return True

    # اختیاری: نمایش پیام تأیید قبل از حذف
    actions = ['delete_selected']

    def delete_queryset(self, request, queryset):
        # اجازه حذف گروهی با CASCADE
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} پاسخ با موفقیت حذف شد (همراه با جواب‌ها و نتایج مرتبط).")

    def delete_model(self, request, obj):
        # برای حذف تک‌تایی
        obj.delete()
        self.message_user(request, "پاسخ با تمام داده‌های مرتبط حذف شد.")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'choice_text', 'text_answer_short', 'scale_value', 'RT')
    list_filter = ('response__questionnaire', 'question')
    search_fields = ('question__text', 'choice__text', 'text_answer')
    readonly_fields = ('response', 'question', 'choice', 'text_answer', 'scale_value', 'RT')

    def choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    choice_text.short_description = 'گزینه'

    def text_answer_short(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + ('...' if len(obj.text_answer) > 50 else '')
        return '-'
    text_answer_short.short_description = 'پاسخ متنی'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # اجازه حذف دستی Answer (اگر لازم شد)
    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_answer')


@admin.register(Attribute)
class AttributeAdmin(admin.ModelAdmin):
    list_display = ('title', 'created_at', 'is_active')
    list_filter = ('is_active', 'created_at')
    search_fields = ('title',)
    readonly_fields = ('created_at',)


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
    )
    readonly_fields = (
        'user', 'questionnaire', 'response', 'attribute',
        'raw_score', 'num_questions', 'average_score',
        'sum_rt', 'average_rt'
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

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    # مهم: اجازه حذف دستی Result (اختیاری، اما بهتر است محدود باشد)
    def has_delete_permission(self, request, obj=None):
        # فقط superuser یا کاربران خاص اجازه حذف مستقیم Result داشته باشند
        return request.user.is_superuser
    

class RatingResponseInline(admin.TabularInline):
    model = RatingResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'stimulus',
        'valence',
        'valence_rt_formatted',
        'arousal',
        'arousal_rt_formatted',
        'created_at_formatted',
    )
    fields = readonly_fields
    ordering = ('-created_at',)

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'زمان پاسخ Valence'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'زمان پاسخ Arousal'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(RatingResponse)
class RatingResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'stimulus',
        'valence',
        'arousal',
        'valence_rt_formatted',
        'arousal_rt_formatted',
        'created_at_formatted',
        'is_complete_display',
    )
    list_filter = (
        'created_at',
        'stimulus',
        'valence',
        'arousal',
    )
    search_fields = (
        'user__username',
        'stimulus',
    )
    readonly_fields = (
        'user',
        'stimulus',
        'valence',
        'valence_rt',
        'arousal',
        'arousal_rt',
        'created_at',
        'created_at_formatted',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at',)
    list_per_page = 50

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'کاربر'
    user_username.admin_order_field = 'user__username'

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'RT Valence'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'RT Arousal'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ کامل"
        elif obj.has_valence() or obj.has_arousal():
            return "◐ ناقص"
        else:
            return "✗ خالی"
    is_complete_display.short_description = 'وضعیت پاسخ'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# نمایش پاسخ‌های رتبه‌بندی در صفحه کاربر (CustomUser)
class RatingResponseUserInline(admin.TabularInline):
    model = RatingResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'stimulus',
        'valence',
        'valence_rt_formatted',
        'arousal',
        'arousal_rt_formatted',
        'created_at_formatted',
    )
    fields = readonly_fields
    ordering = ('-created_at',)

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'RT Valence'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'RT Arousal'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# اضافه کردن Inline به UserAdmin (اصلاح‌شده با tuple)
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (RatingResponseUserInline,)



class PCMResponseInline(admin.TabularInline):
    model = PCMResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence_display',
        'valence_stim1',
        'valence_rt_stim1_formatted',
        'valence_stim2',
        'valence_rt_stim2_formatted',
        'valence_sequence',
        'valence_rt_sequence_formatted',
        'practice_response',
        'practice_correct_display',
        'created_at_formatted',
        'is_complete_display',
    )
    fields = readonly_fields
    ordering = ('-created_at', 'block', 'trial')

    def valence_rt_stim1_formatted(self, obj):
        return f"{obj.valence_rt_stim1} ms" if obj.valence_rt_stim1 is not None else '-'
    valence_rt_stim1_formatted.short_description = 'RT Stim1'

    def valence_rt_stim2_formatted(self, obj):
        return f"{obj.valence_rt_stim2} ms" if obj.valence_rt_stim2 is not None else '-'
    valence_rt_stim2_formatted.short_description = 'RT Stim2'

    def valence_rt_sequence_formatted(self, obj):
        return f"{obj.valence_rt_sequence} ms" if obj.valence_rt_sequence is not None else '-'
    valence_rt_sequence_formatted.short_description = 'RT Sequence'

    def expected_sequence_display(self, obj):
        return "بله" if obj.expected_sequence else "خیر"
    expected_sequence_display.short_description = 'توالی مورد انتظار'

    def practice_correct_display(self, obj):
        if obj.practice_correct is None:
            return '-'
        return "✓ درست" if obj.practice_correct else "✗ غلط"
    practice_correct_display.short_description = 'نتیجه آزمایشی'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ کامل"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ ناقص"
        else:
            return "✗ خالی"
    is_complete_display.short_description = 'وضعیت پاسخ'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PCMResponse)
class PCMResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence_display',
        'valence_stim1',
        'valence_stim2',
        'valence_sequence',
        'created_at_formatted',
        'is_complete_display',
    )
    list_filter = (
        'block',
        'expected_sequence',
        'created_at',
        'category_stim1',
        'category_stim2',
    )
    search_fields = (
        'user__username',
        'cue',
        'stimulus1',
        'stimulus2',
    )
    readonly_fields = (
        'user',
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence',
        'category_stim1',
        'category_stim2',
        'valence_stim1',
        'valence_rt_stim1',
        'valence_stim2',
        'valence_rt_stim2',
        'valence_sequence',
        'valence_rt_sequence',
        'created_at',
        'created_at_formatted',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at', 'block', 'trial')
    list_per_page = 50

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'کاربر'
    user_username.admin_order_field = 'user__username'

    def expected_sequence_display(self, obj):
        return "بله" if obj.expected_sequence else "خیر"
    expected_sequence_display.short_description = 'توالی مورد انتظار'
    expected_sequence_display.boolean = True

    def valence_rt_stim1_formatted(self, obj):
        return f"{obj.valence_rt_stim1} ms" if obj.valence_rt_stim1 is not None else '-'
    valence_rt_stim1_formatted.short_description = 'RT Stim1'

    def valence_rt_stim2_formatted(self, obj):
        return f"{obj.valence_rt_stim2} ms" if obj.valence_rt_stim2 is not None else '-'
    valence_rt_stim2_formatted.short_description = 'RT Stim2'

    def valence_rt_sequence_formatted(self, obj):
        return f"{obj.valence_rt_sequence} ms" if obj.valence_rt_sequence is not None else '-'
    valence_rt_sequence_formatted.short_description = 'RT Sequence'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ کامل"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ ناقص"
        else:
            return "✗ خالی"
    is_complete_display.short_description = 'وضعیت پاسخ'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser

class PCMResponseUserInline(admin.TabularInline):
    model = PCMResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'block',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'expected_sequence_display',
        'valence_stim1',
        'valence_stim2',
        'valence_sequence',
        'created_at_formatted',
        'is_complete_display',
    )
    fields = readonly_fields
    ordering = ('block', 'trial')

    # همان متدهای بالا را اینجا هم تکرار می‌کنیم (یا می‌توان از inheritance استفاده کرد، اما برای سادگی تکرار می‌کنیم)
    def expected_sequence_display(self, obj):
        return "بله" if obj.expected_sequence else "خیر"
    expected_sequence_display.short_description = 'توالی مورد انتظار'


    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'زمان ثبت'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ کامل"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ ناقص"
        else:
            return "✗ خالی"
    is_complete_display.short_description = 'وضعیت'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# اضافه کردن Inline پاسخ‌های PCM به صفحه ادمین کاربر
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (PCMResponseUserInline,)