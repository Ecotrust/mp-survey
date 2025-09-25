from django.db import models
from django.contrib.gis.db.models import PolygonField
from django.conf import settings

# Create your models here.
class QuestionOption(models.Model):
    text = models.CharField(max_length=255)
    value = models.IntegerField(help_text="Numeric value associated with this option.")
    
    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Question Option"
        verbose_name_plural = "Question Options"

class Question(models.Model):
    text = models.CharField(max_length=1024)
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
    options = models.ManyToManyField(
        QuestionOption,
        blank=True,
        related_name='questions',
        help_text="Options for multiple choice or single choice questions."
    )
    is_required = models.BooleanField(
        default=False,
        help_text="Check if this question is required."
    )
    collect_other = models.BooleanField(
        default=False,
        help_text="Check if an 'Other' option should be provided for multiple choice questions."
    )

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = "Question"
        verbose_name_plural = "Questions"

class QuestionSurveyAssociation(models.Model):
    question = models.ForeignKey(
        'Question',
        on_delete=models.CASCADE,
        related_name='survey_associations',
        help_text="The question associated with the survey."
    )
    survey = models.ForeignKey(
        'Survey',
        on_delete=models.CASCADE,
        related_name='question_associations',
        help_text="The survey this question is associated with."
    )
    order = models.PositiveIntegerField(
        help_text="Order of the question in the survey."
    )

    class Meta:
        unique_together = ('question', 'survey')
        ordering = ['order']

    def __str__(self):
        return f"{self.question} in {self.survey} at position {self.order}"

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
    geometry = PolygonField(
        srid=settings.SERVER_SRID,
        blank=True,
        null=True,
        help_text="Geometry of the planning unit."
    )
    family = models.ManyToManyField(
        PlanningUnitFamily,
        related_name='planning_units',
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
    groups = models.ManyToManyField(
        'auth.Group',
        blank=True,
        related_name='surveys',
        help_text="Select groups that can access this survey."
    )
    pu_family = models.ForeignKey(
        PlanningUnitFamily,
        on_delete=models.CASCADE,
        related_name='surveys',
        blank=True,
        null=True,
        help_text="Select the Planning Unit Family this survey belongs to."
    )
    user_defined_pus = models.BooleanField(
        default=False,
        help_text="Check if this survey uses user drawings rather than pre-defined planning units."
    )
    study_bounds = PolygonField(
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
    questions = models.ManyToManyField(
        Question,
        through=QuestionSurveyAssociation,
        blank=True,
        related_name='surveys',
        help_text="Select questions to include in this survey."
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"

class SurveyResponse(models.Model):
    survey = models.ForeignKey(
        Survey,
        on_delete=models.CASCADE,
        related_name='responses',
        help_text="The survey this response belongs to."
    )
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='survey_responses',
        help_text="The user who submitted this response."
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Status (is_complete?)
    # User Notes

    def __str__(self):
        return f"Response by {self.user} for {self.survey}"
    
    class Meta:
        verbose_name = "Survey Response"
        verbose_name_plural = "Survey Responses"
        unique_together = ('survey', 'user')