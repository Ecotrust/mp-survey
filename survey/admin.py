from django.contrib import admin

# Register your models here.

from .models import Question, QuestionOption, Survey, QuestionSurveyAssociation, SurveyResponse

admin.site.register(Question)
admin.site.register(QuestionOption)
admin.site.register(Survey)
admin.site.register(QuestionSurveyAssociation)
admin.site.register(SurveyResponse)

