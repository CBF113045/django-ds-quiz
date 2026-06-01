from django.contrib import admin
from .models import Question, WrongQuestion

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'content')

    search_fields = ('content',)

@admin.register(WrongQuestion)
class WrongQuestionAdmin(admin.ModelAdmin):
    list_display = ('user', 'question')
