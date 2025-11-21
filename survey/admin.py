from django import forms
from django.contrib import admin
import nested_admin
from .models import (
    SurveyQuestionOption, ScenarioQuestionOption, PlanningUnitQuestionOption, 
    Survey, Scenario, SurveyQuestion, ScenarioQuestion, PlanningUnitQuestion, 
    SurveyResponse, SurveyLayerGroup, SurveyLayerOrder, PlanningUnitFamily,
)
from .forms import PlanningUnitFamilyForm, SurveyLayerOrderForm

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
    extra = 1
    classes = ['collapse', 'show']
    form = SurveyLayerOrderForm

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
    exclude = ('collect_other',)

class ScenarioQuestionsInline(nested_admin.NestedStackedInline):
    model = ScenarioQuestion
    extra = 3
    classes = ['collapse', 'show']
    inlines = [ScenarioQuestionOptionsInline]
    exclude = ('collect_other',)

class PlanningUnitQuestionsInline(nested_admin.NestedStackedInline):
    model = PlanningUnitQuestion
    extra = 3
    classes = ['collapse', 'show']
    inlines = [PlanningUnitQuestionOptionsInline]
    exclude = ('collect_other',)

class ScenarioInline(nested_admin.NestedStackedInline):
    model = Scenario
    extra = 0
    max_num = 1
    classes = ['collapse', 'show']
    inlines = [ScenarioQuestionsInline, PlanningUnitQuestionsInline]

class SurveyForm(forms.ModelForm):
    class Meta:
        model = Survey
        fields = '__all__'
        exclude = ('allow_multiple_responses',)
        widgets = {
            'groups': admin.widgets.FilteredSelectMultiple('Groups', is_stacked=False),
        }

class SurveyAdmin(nested_admin.NestedModelAdmin):
    list_display = ('title', 'description', 'created_at', 'updated_at')
    search_fields = ('name', 'description')
    ordering = ('-created_at',)
    inlines = [LayerGroupsInline, SurveyQuestionsInline, ScenarioInline]
    form = SurveyForm

class PlanningUnitFamilyAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')
    form = PlanningUnitFamilyForm

    def get_fields(self, request, obj=None):
        if obj:
            fields = ('name', 'description', 'planning_units_count')
        else:
            fields = ('name', 'description', 'planning_units')
        return fields

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            # this gets saved during the clean method because we need to detect if/when there is an issue running the import script
            new_obj = PlanningUnitFamily.objects.get(name=form.cleaned_data['name'])
            new_obj.description = form.cleaned_data['description']
            new_obj.save()
        else:
            super().save_model(request, obj, form, change)



# admin.site.register(SurveyQuestion)
# admin.site.register(Scenario)
# admin.site.register(ScenarioQuestion)
# admin.site.register(PlanningUnitQuestion)
# admin.site.register(QuestionOption)
# admin.site.register(Survey)
# admin.site.register(QuestionSurveyAssociation)
admin.site.register(PlanningUnitFamily, PlanningUnitFamilyAdmin)
admin.site.register(SurveyResponse)

admin.site.register(Survey, SurveyAdmin)
