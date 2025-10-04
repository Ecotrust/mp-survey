from django import forms
from django.forms import ModelForm
from .models import SurveyResponse, SurveyQuestion, SurveyAnswer


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

            for question in questions:
                field_name = f'question_{question.id}'
                answer = SurveyAnswer.objects.filter(response=self.instance, question=question).first()
                initial_answer = answer.value if answer else None
                
                # Create field based on question type
                if question.question_type == 'text':
                    self.fields[field_name] = forms.CharField(
                        label=question.text,
                        required=question.is_required,
                        initial=initial_answer,
                        widget=forms.TextInput(attrs={'class': 'form-control'})
                    )
                # elif question.question_type == 'textarea':
                #     self.fields[field_name] = forms.CharField(
                #         label=question.text,
                #         required=question.is_required,
                #         initial=answer.value if answer else '',
                #         widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
                #     )
                elif question.question_type == 'number':
                    self.fields[field_name] = forms.IntegerField(
                        label=question.text,
                        required=question.is_required,
                        initial=initial_answer,
                        widget=forms.NumberInput(attrs={'class': 'form-control'})
                    )
                # elif question.question_type == 'email':
                #     self.fields[field_name] = forms.EmailField(
                #         label=question.text,
                #         required=question.is_required,
                #         widget=forms.EmailInput(attrs={'class': 'form-control'})
                #     )

                # selected_options format:
                #   [
                #       {"option_id": 1, "text": "Option 1"}, 
                #       {"option_id": 2, "text": "Option 2"}
                #   ]
                ### I think this translation is best performed in forms.py.
                elif question.question_type == 'single_choice':
                    # TODO: calculate appropriate format of 'initial_answer'
                    choices = question.get_choices()

                    self.fields[field_name] = forms.ChoiceField(
                        label=question.text,
                        required=question.is_required,
                        choices=choices,
                        widget=forms.Select(attrs={'class': 'form-control'})
                    )
                elif question.question_type == 'multiple_choice':
                    # TODO: calculate appropriate format of 'initial_answer'
                    choices = question.get_choices()
                    
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=question.text,
                        required=question.is_required,
                        choices=choices,
                        widget=forms.CheckboxSelectMultiple()
                    )
                # elif question.question_type == 'boolean':
                #     self.fields[field_name] = forms.BooleanField(
                #         label=question.text,
                #         required=question.is_required,
                #         widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
                #     )
                # elif question.question_type == 'date':
                #     self.fields[field_name] = forms.DateField(
                #         label=question.text,
                #         required=question.is_required,
                #         widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'})
                #     )
                
                # Add help text if available
                if question.help_text:
                    self.fields[field_name].help_text = question.help_text
    
    def save_answers(self, survey_response, survey):
        """
        Save the form data as SurveyAnswer objects
        """
        questions = SurveyQuestion.objects.filter(survey=survey)
        
        for question in questions:
            field_name = f'question_{question.id}'
            if field_name in self.cleaned_data:
                answer_value = self.cleaned_data[field_name]
                
                # Handle different data types
                if question.question_type == 'multichoice':
                    if isinstance(answer_value, list):
                        answer_value = '\n'.join(answer_value)
                elif question.question_type == 'boolean':
                    answer_value = str(answer_value)
                elif question.question_type == 'date':
                    if answer_value:
                        answer_value = answer_value.isoformat()
                
                # Create or update the answer
                answer, created = SurveyAnswer.objects.get_or_create(
                    response=survey_response,
                    question=question,
                    defaults={'answer': str(answer_value) if answer_value is not None else ''}
                )
                
                if not created:
                    answer.answer = str(answer_value) if answer_value is not None else ''
                    answer.save()
        
        return survey_response
