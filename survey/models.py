from django.db import models
from features.models import GeometryField

# Create your models here.
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
    study_bounds = GeometryField(
        blank=True,
        null=True,
        help_text="Define the study area for this survey."
    )
    selection_snapping = models.ChoiceField(
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
    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Survey"
        verbose_name_plural = "Surveys"

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
    geometry = GeometryField(
        help_text="Geometry of the planning unit."
    )
    family = models.ManyToManyField(
        Survey.PlanningUnitFamily,
        related_name='planning_units',
        help_text="Select the Planning Unit Families this planning unit belongs to."
    )
    
    def __str__(self):
        return f"Planning Unit {self.id}"
    class Meta:
        verbose_name = "Planning Unit"
        verbose_name_plural = "Planning Units"
        unique_together = ('geometry', 'family')

