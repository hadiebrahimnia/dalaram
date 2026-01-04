from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *


# Register CustomUser with standard UserAdmin
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
        ('Advanced info', {
            'fields': ('created_at',),
            'classes': ('collapse',),
        }),
    )

    def questions_count(self, obj):
        return obj.questions.count()
    questions_count.short_description = 'Number of Questions'


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 1
    fields = ('text', 'value')
    verbose_name = 'Choice'
    verbose_name_plural = 'Choices'


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'order', 'attribute', 'questionnaire', 'question_type_display', 'required')
    list_filter = ('questionnaire__title', 'question_type', 'required')
    search_fields = ('text', 'questionnaire__title')
    list_editable = ('order',)
    inlines = [ChoiceInline]

    def question_type_display(self, obj):
        return dict(Question.QUESTION_TYPES).get(obj.question_type, obj.question_type)
    question_type_display.short_description = 'Question Type'


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ('text', 'value', 'question__order', 'question', 'questionnaire_title')
    list_filter = ('question__questionnaire__title',)
    search_fields = ('text', 'question__text')

    def questionnaire_title(self, obj):
        return obj.question.questionnaire.title
    questionnaire_title.short_description = 'Questionnaire'


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0
    readonly_fields = ('question', 'get_choice_text', 'text_answer', 'scale_value', 'RT')
    fields = ('question', 'get_choice_text', 'text_answer', 'scale_value', 'RT')

    def get_choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    get_choice_text.short_description = 'Selected Choice'

    def has_add_permission(self, request, obj):
        return False


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
        return obj.respondent.username if obj.respondent else 'Anonymous (Guest)'
    respondent_username.short_description = 'Respondent'

    def answers_count(self, obj):
        return obj.answers.count()
    answers_count.short_description = 'Number of Answers'

    def has_delete_permission(self, request, obj=None):
        return request.user.has_perm('core.delete_response')

    actions = ['delete_selected']

    def delete_queryset(self, request, queryset):
        count = queryset.count()
        queryset.delete()
        self.message_user(request, f"{count} responses deleted successfully (including related answers and results).")

    def delete_model(self, request, obj):
        obj.delete()
        self.message_user(request, "Response and all related data deleted.")


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('response', 'question', 'choice_text', 'text_answer_short', 'scale_value', 'RT')
    list_filter = ('response__questionnaire', 'question')
    search_fields = ('question__text', 'choice__text', 'text_answer')
    readonly_fields = ('response', 'question', 'choice', 'text_answer', 'scale_value', 'RT')

    def choice_text(self, obj):
        return obj.choice.text if obj.choice else '-'
    choice_text.short_description = 'Choice'

    def text_answer_short(self, obj):
        if obj.text_answer:
            return obj.text_answer[:50] + ('...' if len(obj.text_answer) > 50 else '')
        return '-'
    text_answer_short.short_description = 'Text Answer'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

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
        return obj.user.username if obj.user else 'Unknown'
    respondent_username.short_description = 'User'

    def response_started_at(self, obj):
        return obj.response.started_at
    response_started_at.short_description = 'Start Time'
    response_started_at.admin_order_field = 'response__started_at'

    def average_rt_formatted(self, obj):
        return f"{obj.average_rt:.2f} sec" if obj.average_rt else '-'
    average_rt_formatted.short_description = 'Avg RT'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ------------------- Rating Responses -------------------

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
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

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
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif obj.has_valence() or obj.has_arousal():
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


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
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Add Rating responses inline to CustomUser admin
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (RatingResponseUserInline,)


# ------------------- PCM Main Responses -------------------

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
        'valence_stim1',
        'valence_rt_stim1_formatted',
        'valence_stim2',
        'valence_rt_stim2_formatted',
        'valence_sequence',
        'valence_rt_sequence_formatted',
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

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

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
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'

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
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

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
        'valence_stim1',
        'valence_stim2',
        'valence_sequence',
        'created_at_formatted',
        'is_complete_display',
    )
    fields = readonly_fields
    ordering = ('block', 'trial')

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif (obj.valence_stim1 or obj.valence_stim2 or obj.valence_sequence):
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Add PCM main responses inline to CustomUser admin
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (PCMResponseUserInline,)


# ------------------- PCM Practice Responses -------------------

class PCMPracticeResponseUserInline(admin.TabularInline):
    model = PCMPracticeResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'category_stim1',
        'category_stim2',
        'practice_response',
        'practice_correct',
        'created_at_formatted',
    )
    fields = readonly_fields
    ordering = ('-created_at', 'trial')

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Add PCM practice responses inline to CustomUser admin
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (PCMPracticeResponseUserInline,)


@admin.register(PCMPracticeResponse)
class PCMPracticeResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'trial',
        'cue_short',
        'stimulus1_short',
        'stimulus2_short',
        'practice_response',
        'practice_correct',
        'created_at_formatted',
    )
    list_filter = (
        'practice_correct',
        'created_at',
        'trial',
    )
    search_fields = (
        'user__username',
        'cue',
        'stimulus1',
        'stimulus2',
        'practice_response',
    )
    readonly_fields = (
        'user',
        'trial',
        'cue',
        'stimulus1',
        'stimulus2',
        'category_stim1',
        'category_stim2',
        'practice_response',
        'practice_correct',
        'created_at',
        'created_at_formatted',
    )
    date_hierarchy = 'created_at'
    ordering = ('-created_at', 'trial')
    list_per_page = 50

    def user_username(self, obj):
        return obj.user.username
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'

    def cue_short(self, obj):
        return obj.cue[:50] + '...' if len(obj.cue) > 50 else obj.cue
    cue_short.short_description = 'Cue'

    def stimulus1_short(self, obj):
        if not obj.stimulus1:
            return '-'
        return obj.stimulus1[:40] + '...' if len(obj.stimulus1) > 40 else obj.stimulus1
    stimulus1_short.short_description = 'Stimulus 1'

    def stimulus2_short(self, obj):
        if not obj.stimulus2:
            return '-'
        return obj.stimulus2[:40] + '...' if len(obj.stimulus2) > 40 else obj.stimulus2
    stimulus2_short.short_description = 'Stimulus 2'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


# ------------------- PCM Re-Rating Responses -------------------

class PCMReRatingResponseInline(admin.TabularInline):
    model = PCMReRatingResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'stimulus_file',
        'stimulus_number',
        'valence',
        'valence_rt_formatted',
        'arousal',
        'arousal_rt_formatted',
        'created_at_formatted',
        'is_complete_display',
    )
    fields = readonly_fields
    ordering = ('-created_at',)

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif obj.valence is not None or obj.arousal is not None:
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(PCMReRatingResponse)
class PCMReRatingResponseAdmin(admin.ModelAdmin):
    list_display = (
        'user_username',
        'stimulus_number',
        'stimulus_file_short',
        'valence',
        'arousal',
        'valence_rt_formatted',
        'arousal_rt_formatted',
        'created_at_formatted',
        'is_complete_display',
    )
    list_filter = (
        'created_at',
        'valence',
        'arousal',
        'stimulus_number',
    )
    search_fields = (
        'user__username',
        'stimulus_file',
        'stimulus_number',
    )
    readonly_fields = (
        'user',
        'stimulus_file',
        'stimulus_number',
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
    user_username.short_description = 'User'
    user_username.admin_order_field = 'user__username'

    def stimulus_file_short(self, obj):
        return obj.stimulus_file[:60] + '...' if len(obj.stimulus_file) > 60 else obj.stimulus_file
    stimulus_file_short.short_description = 'Stimulus File'

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif obj.valence is not None or obj.arousal is not None:
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser


class PCMReRatingResponseUserInline(admin.TabularInline):
    model = PCMReRatingResponse
    extra = 0
    can_delete = False
    readonly_fields = (
        'stimulus_file',
        'stimulus_number',
        'valence',
        'valence_rt_formatted',
        'arousal',
        'arousal_rt_formatted',
        'created_at_formatted',
        'is_complete_display',
    )
    fields = readonly_fields
    ordering = ('-created_at',)

    def valence_rt_formatted(self, obj):
        return f"{obj.valence_rt} ms" if obj.valence_rt is not None else '-'
    valence_rt_formatted.short_description = 'Valence RT'

    def arousal_rt_formatted(self, obj):
        return f"{obj.arousal_rt} ms" if obj.arousal_rt is not None else '-'
    arousal_rt_formatted.short_description = 'Arousal RT'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime("%Y-%m-%d %H:%M:%S")
    created_at_formatted.short_description = 'Created At'

    def is_complete_display(self, obj):
        if obj.is_complete():
            return "✓ Complete"
        elif obj.valence is not None or obj.arousal is not None:
            return "◐ Partial"
        else:
            return "✗ Empty"
    is_complete_display.short_description = 'Status'

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False


# Add PCM Re-Rating responses inline to CustomUser admin
current_inlines = getattr(UserAdmin, 'inlines', ())
UserAdmin.inlines = current_inlines + (PCMReRatingResponseUserInline,)