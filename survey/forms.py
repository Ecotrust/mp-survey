from dal import autocomplete
from django import forms
from django.core.cache import cache
from django.forms import ModelForm, Form
from tempfile import NamedTemporaryFile
from django.core.management import call_command
from django.core.management.base import CommandError
from layers.models import Layer
from .models import (
    SurveyResponse, SurveyQuestion, SurveyAnswer, SurveyQuestionOption,
    PlanningUnitQuestion, ScenarioAnswer, ScenarioQuestionOption, 
    PlanningUnitAnswer, PlanningUnitQuestionOption, CoinAssignment, 
    PlanningUnit, PlanningUnitFamily, SurveyLayerOrder,
)

def populate_question_fields(instance, question, field_name, initial_answer=None):
    # Create field based on question type
    if question.question_type == 'text':
        instance.fields[field_name] = forms.CharField(
            label=question.text,
            required=question.is_required,
            initial=initial_answer,
            widget=forms.TextInput(attrs={'class': 'form-control'})
        )
    # elif question.question_type == 'textarea':
    #     instance.fields[field_name] = forms.CharField(
    #         label=question.text,
    #         required=question.is_required,
    #         initial=answer.value if answer else '',
    #         widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    #     )
    elif question.question_type == 'number':
        instance.fields[field_name] = forms.IntegerField(
            label=question.text,
            required=question.is_required,
            initial=initial_answer,
            widget=forms.NumberInput(attrs={'class': 'form-control'})
        )
    # elif question.question_type == 'email':
    #     instance.fields[field_name] = forms.EmailField(
    #         label=question.text,
    #         required=question.is_required,
    #         widget=forms.EmailInput(attrs={'class': 'form-control'})
    #     )

    # selected_options format:
    #   [
    #       {"option_id": 1, "text": "Option 1"}, 
    #       {"option_id": 2, "text": "Option 2"}
    #   ]
    elif question.question_type == 'single_choice':
        # TODO: calculate appropriate format of 'initial_answer'
        choices = question.get_choices()

        instance.fields[field_name] = forms.ChoiceField(
            label=question.text,
            required=question.is_required,
            choices=choices,
            initial=initial_answer[0] if initial_answer else None,
            widget=forms.Select(attrs={'class': 'form-control'})
        )
    elif question.question_type == 'multiple_choice':
        # TODO: calculate appropriate format of 'initial_answer'
        choices = question.get_choices()
        
        instance.fields[field_name] = forms.MultipleChoiceField(
            label=question.text,
            required=question.is_required,
            choices=choices,
            initial=[opt[0] for opt in initial_answer] if initial_answer else [],
            widget=forms.CheckboxSelectMultiple()
        )
    # elif question.question_type == 'boolean':
    #     instance.fields[field_name] = forms.BooleanField(
    #         label=question.text,
    #         required=question.is_required,
    #         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    #     )
    # elif question.question_type == 'date':
    #     instance.fields[field_name] = forms.DateField(
    #         label=question.text,
    #         required=question.is_required,
    #         widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
    #     )
    
    # Add help text if available
    if question.help_text:
        instance.fields[field_name].help_text = question.help_text
            
    # return fields

def save_related_answer(question, answer, answer_value, choiceModel):
    # Handle different data types
    if question.question_type == 'text':
        answer.text_answer = answer_value
    elif question.question_type == 'number':
        answer.numeric_answer = int(answer_value)
        answer.text_answer = str(answer_value)
    elif question.question_type == 'single_choice':
        # answer_value is the option_id
        answer_choice = choiceModel.objects.filter(id=answer_value, question=question).first()
        if answer_choice:
            answer.selected_options = [{"option_id": answer_choice.id, "text": answer_choice.text}]
            answer.text_answer = answer_choice.text
    elif question.question_type == 'multiple_choice':
        # answer_value is a list of option_ids
        answer.selected_options = []
        for option_id in answer_value:
            answer_choice = choiceModel.objects.filter(id=int(option_id), question=question).first()
            if answer_choice:
                answer.selected_options.append({"option_id": answer_choice.id, "text": answer_choice.text})
    # elif question.question_type == 'boolean':
    #     answer_value = str(answer_value)
    # elif question.question_type == 'date':
    #     if answer_value:
    #         answer_value = answer_value.isoformat()

    answer.save()

class SurveyResponseForm(ModelForm):
    """
    Dynamic form that generates fields based on SurveyQuestions
    associated with a SurveyResponse's survey.
    """
    
    class Meta:
        model = SurveyResponse
        fields = []  # We'll add fields dynamically
    
    def __init__(self, *args, **kwargs):
        survey = kwargs.pop('survey', None)
        super().__init__(*args, **kwargs)
        
        if survey:
            # Get all questions for this survey
            questions = SurveyQuestion.objects.filter(survey=survey).order_by('order')

            # fields = {}
            for question in questions:
                field_name = f'question_{question.id}'
                answer = SurveyAnswer.objects.filter(response=self.instance, question=question).first()
                initial_answer = answer.value if answer else None

                populate_question_fields(self, question, field_name, initial_answer)
    
    def save_answers(self, survey_response):
        """
        Save the form data as SurveyAnswer objects
        """
        survey = survey_response.survey
        questions = SurveyQuestion.objects.filter(survey=survey)
        
        for question in questions:
            field_name = f'question_{question.id}'
            if field_name in self.cleaned_data:
                answer_value = self.cleaned_data[field_name]
                answer, created = SurveyAnswer.objects.get_or_create(
                    response=survey_response,
                    question=question,
                )

                save_related_answer(question, answer, answer_value, SurveyQuestionOption)
                
        return survey_response

class ScenarioForm(Form):
    """
    Dynamic form that generates fields based on ScenarioQuestions
    associated with a Scenario.
    """
    
    class Meta:
        fields = []  # We'll add fields dynamically
    
    def __init__(self, *args, **kwargs):
        scenario = kwargs.pop('scenario', None)
        response = kwargs.pop('response', None)
        super().__init__(*args, **kwargs)
        
        if scenario:
            # Get all questions for this scenario
            questions = scenario.scenario_questions_scenario.all().order_by('order')

            # fields = {}
            for question in questions:
                field_name = f'scenario_{scenario.id}_question_{question.id}'
                answer = ScenarioAnswer.objects.filter(response=response, question=question).first()
                initial_answer = answer.value if answer else None

                populate_question_fields(self, question, field_name, initial_answer)

                # self.fields = populate_fields(questions, answerModel=ScenarioAnswer)

    def save_answers(self, response, scenario):
        """
        Save the form data as ScenarioAnswer objects
        """
        # Save scenario questions
        scenario_questions = scenario.scenario_questions_scenario.all()
        
        for question in scenario_questions:
            field_name = f'scenario_{scenario.id}_question_{question.id}'
            if field_name in self.cleaned_data:
                answer_value = self.cleaned_data[field_name]
                answer, created = ScenarioAnswer.objects.get_or_create(
                    response=response,
                    question=question,
                )

                save_related_answer(question, answer, answer_value, ScenarioQuestionOption)

        return response
    
class PlanningUnitForm(Form):
    """
    Dynamic form that generates fields based on PlanningUnitQuestions
    associated with a Scenario.
    """
    
    class Meta:
        fields = []  # We'll add fields dynamically
    
    def __init__(self, *args, **kwargs):
        scenario = kwargs.pop('scenario', None)
        response = kwargs.pop('response', None)
        unit_id = kwargs.pop('unit_id', None)
        super().__init__(*args, **kwargs)
        
        if scenario:
            if scenario.is_weighted:
                available_coins = response.scenario_status(scenario.id)['coins_available']
                allocated_coins = 0
                if unit_id is not None:
                    existing_assignment = CoinAssignment.objects.filter(
                        response=response,
                        scenario=scenario,
                        planning_unit__pk=unit_id
                    )
                    if len(existing_assignment) > 0:
                        allocated_coins = existing_assignment[0].coins_assigned
                self.fields['scenario_{}_coin_assignment'.format(scenario.id)] = forms.IntegerField(
                    label='Assign Coins (Available: {})'.format(available_coins),
                    min_value=0,
                    max_value=available_coins+allocated_coins,
                    initial=allocated_coins
                )

            self.fields['scenario_{}_planning_unit_ids'.format(scenario.id)] = forms.CharField(
                widget=forms.HiddenInput(),
                label='',
                initial=unit_id if unit_id is not None else ''
            )
                
            pu_questions = PlanningUnitQuestion.objects.filter(scenario=scenario).order_by('order')
            for question in pu_questions:
                field_name = f'scenario_{scenario.id}_pu_question_{question.id}'
                if unit_id is not None:
                    answer = PlanningUnitAnswer.objects.filter(response=response, question=question, planning_unit__pk=unit_id).first()
                    initial_answer = answer.value if answer else None
                else:
                    initial_answer = None

                populate_question_fields(self, question, field_name, initial_answer)

    def save_answers(self, response, scenario):
        """
        Save the form data as PlanningUnitAnswer objects
        """
        # Save planning unit questions
        pu_questions = PlanningUnitQuestion.objects.filter(scenario=scenario)

        pu_field_name = f'scenario_{scenario.id}_planning_unit_ids'
        selected_planning_units = [PlanningUnit.objects.get(pk=x) for x in self.cleaned_data[pu_field_name].split(',')]
        
        for question in pu_questions:
            field_name = f'scenario_{scenario.id}_pu_question_{question.id}'
            if field_name in self.cleaned_data:
                answer_value = self.cleaned_data[field_name]

                for pu in selected_planning_units:
                    answer, created = PlanningUnitAnswer.objects.get_or_create(
                        response=response,
                        question=question,
                        planning_unit=pu
                    )

                    save_related_answer(question, answer, answer_value, PlanningUnitQuestionOption)
        # Update/Create CoinAssignments
        for pu in selected_planning_units:
            coin_field_name = f'scenario_{scenario.id}_coin_assignment'
            if coin_field_name in self.cleaned_data:
                coins_assigned = self.cleaned_data[coin_field_name]
                coin_assignment, created = CoinAssignment.objects.get_or_create(
                    response=response,
                    scenario=scenario,
                    planning_unit=pu
                )
                coin_assignment.coins_assigned = coins_assigned
                coin_assignment.save()

        return response
    
class PlanningUnitFamilyForm(ModelForm):
    planning_units_count = forms.CharField(
        label='Planning Units Count',
        required=False,
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'})
    )
    planning_units = forms.FileField(
        label='planning units file',
        required=False,
        help_text='Upload a file containing planning units (zipped shapefile or GeoJSON).'
    )

    class Meta:
        model = PlanningUnitFamily
        fields = ['name', 'description', 'planning_units_count', 'planning_units'] # hold off on 'remote_raster' URL for now
        # exclude = ['remote_raster']  # Exclude the planning_units field for custom handling

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            planning_unit_count = self.instance.planning_units_family.count()
            self.fields['planning_units_count'] = forms.CharField(
                label='Planning Units Count',
                required=False,
                initial='{} planning units'.format(planning_unit_count),
                widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control-plaintext'})
            )

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk:
            if not cleaned_data.get('planning_units'):
                raise forms.ValidationError("You must upload a file when creating a new Planning Unit Family.")
            if PlanningUnitFamily.objects.filter(name=cleaned_data.get('name')).exists():
                raise forms.ValidationError(f"A Planning Unit Family with the name '{cleaned_data.get('name')}' already exists.")
            try:
                suffix = cleaned_data['planning_units'].name.split('.')[-1].lower()
                with NamedTemporaryFile(delete=True, suffix=f'.{suffix}') as temp_file:
                    for chunk in cleaned_data['planning_units'].chunks():
                        temp_file.write(chunk)
                    temp_file.flush()
                    input_file = temp_file.name
                    try:
                        call_command('import_planning_units', input_file, '--family-name', cleaned_data.get('name'))
                    except CommandError as e:
                        raise forms.ValidationError(f"Import failed: {str(e)}")
            except Exception as e:
                raise forms.ValidationError(f"An error occurred during import: {str(e)}")
        return cleaned_data

class SurveyLayerOrderForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        ordered_layers = cache.get('all_layers_qs')
        if not ordered_layers:
            ordered_layers = Layer.all_objects.all().order_by('name')
            cache.set('all_layers_qs', ordered_layers, 60*60)  # Cache for 1 hour
        self.fields['layer'].queryset = ordered_layers

    layer = forms.ModelChoiceField(
        queryset=None,
        widget=autocomplete.ModelSelect2()
    )

    class Meta:
        model = SurveyLayerOrder
        fields =  ['auto_show', 'order', 'layer',]
