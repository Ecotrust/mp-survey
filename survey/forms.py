from django import forms
from django.forms import ModelForm
from .models import SurveyResponse, SurveyQuestion, SurveyAnswer, SurveyQuestionOption


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
                elif question.question_type == 'single_choice':
                    # TODO: calculate appropriate format of 'initial_answer'
                    choices = question.get_choices()

                    self.fields[field_name] = forms.ChoiceField(
                        label=question.text,
                        required=question.is_required,
                        choices=choices,
                        initial=initial_answer[0] if initial_answer else None,
                        widget=forms.Select(attrs={'class': 'form-control'})
                    )
                elif question.question_type == 'multiple_choice':
                    # TODO: calculate appropriate format of 'initial_answer'
                    choices = question.get_choices()
                    
                    self.fields[field_name] = forms.MultipleChoiceField(
                        label=question.text,
                        required=question.is_required,
                        choices=choices,
                        initial=[opt[0] for opt in initial_answer] if initial_answer else [],
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
                answer, created = SurveyAnswer.objects.get_or_create(
                    response=survey_response,
                    question=question,
                )
                
                # Handle different data types
                if question.question_type == 'text':
                    answer.text_answer = answer_value
                elif question.question_type == 'number':
                    answer.numeric_answer = int(answer_value)
                    answer.text_answer = str(answer_value)
                elif question.question_type == 'single_choice':
                    # answer_value is the option_id
                    answer_choice = SurveyQuestionOption.objects.filter(id=answer_value, question=question).first()
                    if answer_choice:
                        answer.selected_options = [{"option_id": answer_choice.id, "text": answer_choice.text}]
                        answer.text_answer = answer_choice.text
                elif question.question_type == 'multiple_choice':
                    # answer_value is a list of option_ids
                    answer.selected_options = []
                    for option_id in answer_value:
                        answer_choice = SurveyQuestionOption.objects.filter(id=int(option_id), question=question).first()
                        if answer_choice:
                            answer.selected_options.append({"option_id": answer_choice.id, "text": answer_choice.text})
                # elif question.question_type == 'boolean':
                #     answer_value = str(answer_value)
                # elif question.question_type == 'date':
                #     if answer_value:
                #         answer_value = answer_value.isoformat()

                answer.save()
        
        return survey_response
