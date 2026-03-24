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

# This admin action allows exporting a single survey response as a GeoJSON file, which includes the user's answers 
# and the spatial data for any selected planning units in spatial scenarios. It checks that exactly one response is 
# selected, converts it to GeoJSON format using the 'response_as_geojson' method, and returns it as a downloadable file.
@admin.action(description="Export a response as GeoJSON")
def export_as_geojson(self, request, queryset):
    import json
    from django.http import HttpResponse

    if queryset.count() != 1:
        self.message_user(request, "Please select exactly one response to export.")
        return

    for survey_response in queryset:
        geojson = survey_response.response_as_geojson()
    response = HttpResponse(json.dumps(geojson), content_type='application/geo+json')
    filename = f"survey_{survey_response.survey_id}_user_{survey_response.user_id}.geojson"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

class SurveyResponseAdmin(admin.ModelAdmin):
    list_display = ('survey', 'user')
    search_fields = ('survey__name', 'user__username')
    ordering = ('-survey',)
    actions = [export_as_geojson]


# admin.site.register(SurveyQuestion)
# admin.site.register(Scenario)
# admin.site.register(ScenarioQuestion)
# admin.site.register(PlanningUnitQuestion)
# admin.site.register(QuestionOption)
# admin.site.register(Survey)
# admin.site.register(QuestionSurveyAssociation)
admin.site.register(PlanningUnitFamily, PlanningUnitFamilyAdmin)
admin.site.register(SurveyResponse, SurveyResponseAdmin)

admin.site.register(Survey, SurveyAdmin)
