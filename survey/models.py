from django.db import models
from django.contrib.gis.db.models import MultiPolygonField
from django.conf import settings

class QuestionOption(models.Model):
    text = models.CharField(max_length=255)
    order = models.PositiveIntegerField(help_text="Order of the option in the list.")

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"
        abstract = True

class SurveyQuestionOption(QuestionOption):
    question = models.ForeignKey(
        'SurveyQuestion',
        on_delete=models.CASCADE,
        related_name='survey_question_options_question',
        help_text="The survey question this option belongs to."
    )
    class Meta:
        verbose_name = "Survey Question Option"
        verbose_name_plural = "Survey Question Options"
        ordering = ['order']

class ScenarioQuestionOption(QuestionOption):
    question = models.ForeignKey(
        'ScenarioQuestion',
        on_delete=models.CASCADE,
        related_name='scenario_question_options_question',
        help_text="The scenario question this option belongs to."
    )
    class Meta:
        verbose_name = "Scenario Question Option"
        verbose_name_plural = "Scenario Question Options"
        ordering = ['order']

class PlanningUnitQuestionOption(QuestionOption):
    question = models.ForeignKey(
        'PlanningUnitQuestion',
        on_delete=models.CASCADE,
        related_name='planning_unit_question_options_question',
        help_text="The planning unit question this option belongs to."
    )
    class Meta:
        verbose_name = "Planning Unit Question Option"
        verbose_name_plural = "Planning Unit Question Options"
        ordering = ['order']

class Question(models.Model):
    text = models.CharField(max_length=1024)
    order = models.PositiveIntegerField(help_text="Order of the question in the survey.")
    question_type = models.CharField(
        max_length=50,
        choices=[
            ('multiple_choice', 'Multiple Choice'),
            ('single_choice', 'Single Choice'),
            ('text', 'Text'),
            ('number', 'Number'),
        ],
        help_text="Type of the question."
    )
    # options = models.ManyToManyField(
    #     QuestionOption,
    #     blank=True,
    #     related_name='%(class)s_options',
    #     help_text="Options for multiple choice or single choice questions."
    # )
    is_required = models.BooleanField(
        default=False,
        help_text="Check if this question is required."
    )
    collect_other = models.BooleanField(
        default=False,
        help_text="Check if an 'Other' option should be provided for multiple choice questions."
    )
    help_text = models.CharField(
        max_length=1024,
        blank=True,
        null=True,
        help_text="Additional help text for the question."
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"
        abstract = True

def get_question_choices(question, options_model):
    if not question.question_type in ['single_choice', 'multiple_choice']:
        return None
    return [(option.id, option.text) for option in options_model.objects.filter(question=question).order_by('order')]

class SurveyQuestion(Question):
    survey = models.ForeignKey(
        'Survey',
        on_delete=models.CASCADE,
        related_name='survey_questions_survey',
        help_text="The survey this question belongs to."
    )

    def get_choices(self):
        return get_question_choices(self, SurveyQuestionOption)

    class Meta:
        verbose_name = "Survey Question"
        verbose_name_plural = "Survey Questions"
        ordering = ['order']

class ScenarioQuestion(Question):
    scenario = models.ForeignKey(
        'Scenario',
        on_delete=models.CASCADE,
        related_name='scenario_questions_scenario',
        help_text="The scenario this question belongs to."
    )

    def get_choices(self):
        return get_question_choices(self, ScenarioQuestionOption)

    class Meta:
        verbose_name = "Scenario Question"
        verbose_name_plural = "Scenario Questions"
        ordering = ['order']

class PlanningUnitQuestion(Question):
    # planning_unit = models.ForeignKey(
    #     'PlanningUnit',
    #     on_delete=models.CASCADE,
    #     related_name='planning_unit_questions_planning_unit',
    #     help_text="The planning unit this question belongs to."
    # )
    scenario = models.ForeignKey(
        'Scenario',
        on_delete=models.CASCADE,
        related_name='planning_unit_questions_scenario',
        help_text="The scenario this question belongs to."
    )

    def get_choices(self):
        return get_question_choices(self, PlanningUnitQuestionOption)
    
    class Meta:
        verbose_name = "Planning Unit Question"
        verbose_name_plural = "Planning Unit Questions"
        ordering = ['order']

class PlanningUnitFamily(models.Model):
        name = models.CharField(max_length=255)
        description = models.TextField(blank=True, null=True)
        remote_raster = models.URLField(
            blank=True,
            null=True,
            help_text="URL to a remote raster layer for this planning unit family. Leave blank to use local vector layer."
        )

        def __str__(self):
            return self.name

        class Meta:
            verbose_name = "Planning Unit Family"
            verbose_name_plural = "Planning Unit Families"

class PlanningUnit(models.Model):
    geometry = MultiPolygonField(
        srid=settings.SERVER_SRID,
        blank=True,
        null=True,
        help_text="Geometry of the planning unit."
    )
    family = models.ManyToManyField(
        PlanningUnitFamily,
        related_name='planning_units_family',
        help_text="Select the Planning Unit Families this planning unit belongs to."
    )
    
    def __str__(self):
        return f"Planning Unit {self.id}"
    class Meta:
        verbose_name = "Planning Unit"
        verbose_name_plural = "Planning Units"

class Survey(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    allow_multiple_responses = models.BooleanField(
        default=False,
        help_text="Check if users can submit multiple responses to this survey."
    )
    groups = models.ManyToManyField(
        'mapgroups.MapGroup',
        blank=True,
        related_name='surveys_groups',
        help_text="Select groups that can access this survey."
    )
    # questions = models.ManyToManyField(
    #     Question,
    #     # through=QuestionSurveyAssociation,
    #     blank=True,
    #     related_name='surveys_questions',
    #     help_text="Select questions to include in this survey."
    # )

    def __str__(self):
        return self.title
    
    def get_scenarios(self):
        return self.scenarios_survey.all().order_by('order')

    class Meta:
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"

class Scenario(models.Model):
    name = models.CharField(max_length=255)
    order = models.PositiveIntegerField(help_text="Order of the scenario in the survey.")
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='scenarios_survey',
        help_text="The survey this scenario belongs to."
    )
    pu_family = models.ForeignKey(
        PlanningUnitFamily,
        on_delete=models.CASCADE,
        related_name='surveys_pu_family',
        blank=True,
        null=True,
        help_text="Select the Planning Unit Family this survey belongs to."
    )
    user_defined_pus = models.BooleanField(
        default=False,
        help_text="Check if this survey uses user drawings rather than pre-defined planning units."
    )
    study_bounds = MultiPolygonField(
        srid=settings.SERVER_SRID,
        blank=True,
        null=True,
        help_text="Define the study area for this survey."
    )
    selection_snapping = models.CharField(
        max_length=50,
        choices=[
            ('default', 'Default'),
            ('intersects', 'Intersection'),
            ('is_within', 'Is Within'),
        ],
        help_text="Select the snapping behavior for planning unit selection."
    )
    is_spatial = models.BooleanField(
        default=True,
        help_text="Check if user will enter spatial data."
    )
    is_weighted = models.BooleanField(
        default=True,
        help_text="Check if user will assign coins to answers."
    )
    total_coins = models.IntegerField(
        default=100,
        help_text="Total number of coins available to users for weighting selections."
    )
    require_all_coins_used = models.BooleanField(
        default=True,
        help_text="Check if users must use all coins when weighting selections."
    )
    min_coins_per_pu = models.IntegerField(
        default=1,
        help_text="Minimum number of coins that must be assigned to each planning unit."
    )
    max_coins_per_pu = models.IntegerField(
        default=100,
        help_text="Maximum number of coins that can be assigned to each planning unit."
    )
    # scenario_questions = models.ManyToManyField(
    #     ScenarioQuestion,
    #     blank=True,
    #     related_name='scenarios_scenario_questions',
    #     help_text="Select questions to include in this scenario."
    # )
    # planning_unit_questions = models.ManyToManyField(
    #     PlanningUnitQuestion,
    #     blank=True,
    #     related_name='scenarios_planning_unit_questions',
    #     help_text="Select planning unit questions to include in this scenario."
    # )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Scenario"
        verbose_name_plural = "Scenarios"

class SurveyResponse(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='survey_responses_survey',
        help_text="The survey this response belongs to."
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='survey_responses_user',
        help_text="The user who submitted this response."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status (is_complete?)
    # User Notes

    def __str__(self):
        return f"Response by {self.user} for {self.survey}"
    
    @property
    def completed(self):
        # A response is considered complete if all required questions have been answered
        required_questions = self.survey.survey_questions_survey.filter(is_required=True)
        for question in required_questions:
            if not self.survey_answers_question.filter(question=question).exists():
                return False
        for scenario in self.survey.scenarios_survey.all():
            required_scenario_questions = scenario.scenario_questions_scenario.filter(is_required=True)
            for question in required_scenario_questions:
                if not self.scenario_answers_question.filter(question=question).exists():
                    return False
            if scenario.is_spatial:
                required_pu_questions = scenario.planning_unit_questions_scenario.filter(is_required=True)
                for pu in PlanningUnit.objects.filter(family=scenario.pu_family):
                    for question in required_pu_questions:
                        if not self.planning_unit_answers_question.filter(question=question, planning_unit=pu).exists():
                            return False
        return True
    
    class Meta:
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"
        unique_together = ('survey', 'user')

def get_answer_value(answer):
    if answer is None:
        return None
    if answer.question.question_type == 'text' and answer.text_answer is not None:
        return answer.text_answer
    elif answer.question.question_type == 'number' and answer.numeric_answer is not None:
        return answer.numeric_answer
    elif answer.question.question_type in ['single_choice', 'multiple_choice'] and answer.selected_options:
        return [(x['option_id'], x['text']) for x in answer.selected_options]
    elif answer.question.question_type == 'text' and answer.other_text_answer:
        return answer.other_text_answer
    else:
        return None

class Answer(models.Model):
    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='%(class)s_response',
        help_text="The survey response this answer belongs to."
    )
    # question = models.ForeignKey(
    #     Question,
    #     on_delete=models.CASCADE,
    #     related_name='%(class)s_question',
    #     help_text="The question this answer corresponds to."
    # )
    selected_options = models.JSONField(
        blank=True,
        null=True,
        help_text="Selected options for multiple choice or single choice questions."
    )
    # selected_options = models.ManyToManyField(
    #     QuestionOption,
    #     blank=True,
    #     related_name='%(class)s_selected_options',
    #     help_text="Selected options for multiple choice or single choice questions."
    # )
    other_text_answer = models.TextField(
        blank=True,
        null=True,
        help_text="'Other' answer for multiple choice questions."
    )
    text_answer = models.TextField(
        blank=True,
        null=True,
        help_text="Text answer for text questions."
    )
    numeric_answer = models.FloatField(
        blank=True,
        null=True,
        help_text="Numeric answer for number questions."
    )
    # boolean_answer = models.NullBooleanField(
    #     blank=True,
    #     null=True,
    #     help_text="Boolean answer for yes/no questions."
    # )
    # media_answer = models.FileField(
    #     upload_to='survey_media/',
    #     blank=True,
    #     null=True,
    #     help_text="Media file answer (image, audio, video)."
    # )

    @property
    def value(self):
        return get_answer_value(self)

    def __str__(self):
        return f"Answer to {self.question} in response {self.response.id}"

    class Meta:
        verbose_name = "Answer"
        verbose_name_plural = "Answers"
        abstract = True

class SurveyAnswer(Answer):
    question = models.ForeignKey(
        SurveyQuestion,
        on_delete=models.CASCADE,
        related_name='survey_answers_question',
        help_text="The survey question this answer corresponds to."
    )
    
    class Meta:
        verbose_name = "Survey Answer"
        verbose_name_plural = "Survey Answers"

class ScenarioAnswer(Answer):
    question = models.ForeignKey(
        ScenarioQuestion,
        on_delete=models.CASCADE,
        related_name='scenario_answers_question',
        help_text="The scenario question this answer corresponds to."
    )
    
    class Meta:
        verbose_name = "Scenario Answer"
        verbose_name_plural = "Scenario Answers"

class PlanningUnitAnswer(Answer):
    question = models.ForeignKey(
        PlanningUnitQuestion,
        on_delete=models.CASCADE,
        related_name='planning_unit_answers_question',
        help_text="The planning unit question this answer corresponds to."
    )
    planning_unit = models.ForeignKey(
        PlanningUnit,
        on_delete=models.CASCADE,
        related_name='planning_unit_answers_planning_unit',
        help_text="The planning unit this answer is associated with."
    )
    # coins_assigned = models.IntegerField(
    #     default=0,
    #     help_text="Number of coins assigned to this planning unit."
    # )
    
    class Meta:
        verbose_name = "Planning Unit Answer"
        verbose_name_plural = "Planning Unit Answers"

class CoinAssignment(models.Model):
    response = models.ForeignKey(
        SurveyResponse,
        on_delete=models.CASCADE,
        related_name='coin_assignments_response',
        help_text="The survey response this coin assignment belongs to."
    )
    scenario = models.ForeignKey(
        Scenario,
        on_delete=models.CASCADE,
        related_name='coin_assignments_scenario',
        help_text="The scenario this coin assignment is associated with."
    )
    planning_unit = models.ForeignKey(
        PlanningUnit,
        on_delete=models.CASCADE,
        related_name='coin_assignments_planning_unit',
        help_text="The planning unit this coin assignment is associated with."
    )
    coins_assigned = models.IntegerField(
        default=0,
        help_text="Number of coins assigned to this planning unit."
    )

    def __str__(self):
        return f"{self.coins_assigned} coins to PU {self.planning_unit.id} in response {self.response.id}"

    class Meta:
        verbose_name = "Coin Assignment"
        verbose_name_plural = "Coin Assignments"
        unique_together = ('response', 'scenario', 'planning_unit')