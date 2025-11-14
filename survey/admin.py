from django.contrib import admin
import nested_admin
from .models import (
    SurveyQuestionOption, ScenarioQuestionOption, PlanningUnitQuestionOption, 
    Survey, Scenario, SurveyQuestion, ScenarioQuestion, PlanningUnitQuestion, 
    SurveyResponse, SurveyLayerGroup, SurveyLayerOrder
)

class SurveyQuestionOptionsInline(nested_admin.NestedTabularInline):
    model = SurveyQuestionOption
    extra = 2
    classes = ['collapse', 'show']

class ScenarioQuestionOptionsInline(nested_admin.NestedTabularInline):
    model = ScenarioQuestionOption
    extra = 2
    classes = ['collapse', 'show']

class PlanningUnitQuestionOptionsInline(nested_admin.NestedTabularInline):
    model = PlanningUnitQuestionOption
    extra = 2
    classes = ['collapse', 'show']
    
class LayerOrderInline(nested_admin.NestedTabularInline):
    model = SurveyLayerOrder
    extra = 3
    classes = ['collapse', 'show']

class LayerGroupsInline(nested_admin.NestedStackedInline):
    model = SurveyLayerGroup
    extra = 1
    classes = ['collapse', 'show']
    inlines = [LayerOrderInline]

class SurveyQuestionsInline(nested_admin.NestedStackedInline):
    model = SurveyQuestion
    extra = 3
    classes = ['collapse', 'show']
    inlines = [SurveyQuestionOptionsInline]

class ScenarioQuestionsInline(nested_admin.NestedStackedInline):
    model = ScenarioQuestion
    extra = 3
    classes = ['collapse', 'show']
    inlines = [ScenarioQuestionOptionsInline]

class PlanningUnitQuestionsInline(nested_admin.NestedStackedInline):
    model = PlanningUnitQuestion
    extra = 3
    classes = ['collapse', 'show']
    inlines = [PlanningUnitQuestionOptionsInline]

class ScenarioInline(nested_admin.NestedStackedInline):
    model = Scenario
    extra = 0
    max_num = 1
    classes = ['collapse', 'show']
    inlines = [ScenarioQuestionsInline, PlanningUnitQuestionsInline]

class SurveyAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    inlines = [LayerGroupsInline, SurveyQuestionsInline, ScenarioInline]



# admin.site.register(SurveyQuestion)
# admin.site.register(Scenario)
# admin.site.register(ScenarioQuestion)
# admin.site.register(PlanningUnitQuestion)
# admin.site.register(QuestionOption)
# admin.site.register(Survey)
# admin.site.register(QuestionSurveyAssociation)
admin.site.register(SurveyResponse)

admin.site.register(Survey, SurveyAdmin)
