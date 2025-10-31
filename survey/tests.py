from datetime import timedelta
from django.contrib.auth.models import User, Group
from django.contrib.gis.geos import MultiPolygon, Polygon
from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
import json
import os

from mapgroups.models import MapGroup
from survey.models import (
    Survey, Scenario, SurveyResponse, SurveyQuestion, ScenarioQuestion,
    PlanningUnitQuestion, SurveyQuestionOption, ScenarioQuestionOption,
    PlanningUnitQuestionOption, SurveyAnswer, ScenarioAnswer,
    PlanningUnitAnswer, PlanningUnitFamily, PlanningUnit, CoinAssignment,
    SurveyLayerGroup, SurveyLayerOrder
)

class ImportPlanningUnitsTest(TestCase):
    """Test cases for the import_planning_units management command."""

    def setUp(self):
        """Set up test data."""
        self.test_file_path = os.path.join(
            os.path.dirname(__file__), 'test_data', 'geojson', 'test_grid.geojson'
        )

    def test_successful_import_without_family_name(self):
        """Test successful import without specifying a family name."""
        # Verify no planning units exist initially
        self.assertEqual(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 0)

        # Run the import command
        call_command('import_planning_units', self.test_file_path)

        # Verify the results - should import 5 planning units
        self.assertEqual(PlanningUnit.objects.count(), 5)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)
        
        # Check that family was created with filename as name
        family = PlanningUnitFamily.objects.first()
        self.assertEqual(family.name, 'test_grid')
        self.assertIn('test_grid.geojson', family.description)

    def test_successful_import_with_family_name(self):
        """Test successful import with a specified family name."""
        # Run the import command with custom family name
        call_command('import_planning_units', self.test_file_path, '--family-name=test_family')

        # Verify the results - should import 5 planning units
        self.assertEqual(PlanningUnit.objects.count(), 5)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)
        
        # Check that family was created with specified name
        family = PlanningUnitFamily.objects.first()
        self.assertEqual(family.name, 'test_family')

    def test_geometry_conversion_polygon_to_multipolygon(self):
        """Test that Polygon geometries are converted to MultiPolygon."""
        # Run the import command
        call_command('import_planning_units', self.test_file_path)

        # Check that all geometries are MultiPolygon
        planning_units = PlanningUnit.objects.all()
        for unit in planning_units:
            self.assertIsInstance(unit.geometry, MultiPolygon)
            self.assertEqual(unit.geometry.geom_type, 'MultiPolygon')

    # def test_attribute_import(self):
    #     """Test that feature attributes are correctly imported."""
    #     # Run the import command
    #     call_command('import_planning_units', self.test_file_path)
    # 
    #     # Check that attributes are correctly imported
    #     planning_units = PlanningUnit.objects.all().order_by('id')
    #     self.assertEqual(len(planning_units), 5, "Should import exactly 5 planning units")
    #     
    #     # Check that key attributes are present
    #     unit1 = planning_units[0]
    #     self.assertIn('OBJECTID', unit1.attributes)
    #     self.assertIn('Grid_ID', unit1.attributes)
    #     self.assertIn('Cell_ID', unit1.attributes)
    #     self.assertIn('Shape_Area', unit1.attributes)

    def test_error_nonexistent_file(self):
        """Test that CommandError is raised for non-existent files."""
        with self.assertRaises(CommandError) as cm:
            call_command('import_planning_units', 'nonexistent_file.geojson')
        
        self.assertIn('Input file does not exist', str(cm.exception))

    def test_error_shapefile_missing_prj(self):
        """Test that CommandError is raised for shapefiles missing projection information."""
        # Path to shapefile without .prj file
        shapefile_path = os.path.join(
            os.path.dirname(__file__), 'test_data', 'shp', 'missing_prj', 'test_grid.shp'
        )
        
        with self.assertRaises(CommandError) as cm:
            call_command('import_planning_units', shapefile_path)
        
        self.assertIn('Shapefile is missing projection information', str(cm.exception))

    def test_successful_shapefile_import(self):
        """Test successful import of a complete shapefile with all required files."""
        # Path to complete shapefile with .prj file
        shapefile_path = os.path.join(
            os.path.dirname(__file__), 'test_data', 'shp', 'complete', 'test_grid.shp'
        )
        
        # Verify no planning units exist initially
        self.assertEqual(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 0)

        # Run the import command
        call_command('import_planning_units', shapefile_path)

        # Verify the results - should import planning units successfully
        self.assertGreater(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)
        
        # Check that family was created with filename as name
        family = PlanningUnitFamily.objects.first()
        self.assertEqual(family.name, 'test_grid')
        self.assertIn('test_grid.shp', family.description)

        # Check that all geometries are valid
        planning_units = PlanningUnit.objects.all()
        for unit in planning_units:
            self.assertIsInstance(unit.geometry, MultiPolygon)
            self.assertEqual(unit.geometry.geom_type, 'MultiPolygon')

    def test_successful_zip_import(self):
        """Test successful import of a zipped shapefile."""
        # Path to zipped shapefile in test data directory
        zip_path = os.path.join(
            os.path.dirname(__file__), 'test_data', 'shp', 'zipped', 'test_grid.zip'
        )
        
        # Verify no planning units exist initially
        self.assertEqual(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 0)

        # Run the import command
        call_command('import_planning_units', zip_path)

        # Verify the results - should import planning units successfully
        self.assertGreater(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)
        
        # Check that family was created with filename as name
        family = PlanningUnitFamily.objects.first()
        self.assertEqual(family.name, 'test_grid')
        # The description should contain the original zip file path
        self.assertIn('test_grid.zip', family.description)

        # Check that all geometries are valid
        planning_units = PlanningUnit.objects.all()
        for unit in planning_units:
            self.assertIsInstance(unit.geometry, MultiPolygon)
            self.assertEqual(unit.geometry.geom_type, 'MultiPolygon')

    def test_error_zip_missing_shapefile(self):
        """Test that CommandError is raised for zip files missing shapefiles."""
        # Create a temporary zip file without a shapefile
        import tempfile
        import zipfile
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as temp_zip:
            # Create a zip file with only a text file, no shapefile
            with zipfile.ZipFile(temp_zip.name, 'w') as zip_ref:
                zip_ref.writestr('test.txt', 'This is a test file')
            
            try:
                with self.assertRaises(CommandError) as cm:
                    call_command('import_planning_units', temp_zip.name)
                
                self.assertIn('No shapefile (.shp) found in zip archive', str(cm.exception))
            finally:
                # Clean up the temporary file
                os.unlink(temp_zip.name)

    def test_family_reuse(self):
        """Test that existing family is reused when importing again."""
        # First import
        call_command('import_planning_units', self.test_file_path, '--family-name=reuse_test')
        self.assertEqual(PlanningUnit.objects.count(), 5)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)

        # Clear planning units but keep family
        PlanningUnit.objects.all().delete()
        self.assertEqual(PlanningUnit.objects.count(), 0)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)

        # Second import to same family
        call_command('import_planning_units', self.test_file_path, '--family-name=reuse_test')
        self.assertEqual(PlanningUnit.objects.count(), 5)
        self.assertEqual(PlanningUnitFamily.objects.count(), 1)  # Still only one family

    def test_transaction_rollback_on_error(self):
        """Test that transaction is rolled back if import fails."""
        # Create a test file with invalid geometry
        invalid_file_path = os.path.join(
            os.path.dirname(__file__), 'test_data', 'invalid_test.geojson'
        )
        
        # Create invalid GeoJSON (missing coordinates)
        with open(invalid_file_path, 'w') as f:
            f.write('''{
                "type": "FeatureCollection",
                "features": [{
                    "type": "Feature",
                    "properties": {"id": 1},
                    "geometry": {"type": "Polygon", "coordinates": []}
                }]
            }''')

        try:
            # This should fail and rollback
            with self.assertRaises(CommandError):
                call_command('import_planning_units', invalid_file_path)
            
            # Verify no data was persisted
            self.assertEqual(PlanningUnit.objects.count(), 0)
            self.assertEqual(PlanningUnitFamily.objects.count(), 0)
            
        finally:
            # Clean up the test file
            if os.path.exists(invalid_file_path):
                os.remove(invalid_file_path)

# Many of the tests below were generated using copilot.
class SurveyModelTests(TestCase):
    """Test cases for Survey model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = Group.objects.create(name='testgroup')
        self.map_group = MapGroup.objects.create(
            name='Test Map Group',
            owner=self.user
        )[0] #Create returns a tuple: [instance, owner membership card]
        
    def test_survey_creation(self):
        """Test creating a survey"""
        survey = Survey.objects.create(
            title='Test Survey',
            description='A test survey',
            start_date=timezone.now(),
            end_date=timezone.now() + timedelta(days=30)
        )
        self.assertEqual(survey.title, 'Test Survey')
        self.assertTrue(survey.allow_multiple_responses is False)
        
    def test_survey_get_scenarios(self):
        """Test getting scenarios in order"""
        survey = Survey.objects.create(title='Test Survey')
        scenario1 = Scenario.objects.create(
            name='Scenario 1', survey=survey, order=2
        )
        scenario2 = Scenario.objects.create(
            name='Scenario 2', survey=survey, order=1
        )
        
        scenarios = survey.get_scenarios()
        self.assertEqual(scenarios.first(), scenario2)
        self.assertEqual(scenarios.last(), scenario1)
        
    def test_survey_get_next_scenario(self):
        """Test getting next scenario"""
        survey = Survey.objects.create(title='Test Survey')
        scenario1 = Scenario.objects.create(
            name='Scenario 1', survey=survey, order=1
        )
        scenario2 = Scenario.objects.create(
            name='Scenario 2', survey=survey, order=2
        )
        
        next_scenario = survey.get_next_scenario(scenario1.id)
        self.assertEqual(next_scenario, scenario2.id)
        
        # Test last scenario returns None
        last_scenario = survey.get_next_scenario(scenario2.id)
        self.assertIsNone(last_scenario)

class ScenarioModelTests(TestCase):
    """Test cases for Scenario model"""
    
    def setUp(self):
        self.survey = Survey.objects.create(title='Test Survey')
        self.pu_family = PlanningUnitFamily.objects.create(
            name='Test PU Family'
        )
        
    def test_scenario_creation(self):
        """Test creating a scenario"""
        scenario = Scenario.objects.create(
            name='Test Scenario',
            survey=self.survey,
            order=1,
            pu_family=self.pu_family,
            is_spatial=True,
            is_weighted=True,
            total_coins=100
        )
        self.assertEqual(scenario.name, 'Test Scenario')
        self.assertEqual(scenario.survey, self.survey)
        self.assertTrue(scenario.is_spatial)
        self.assertEqual(scenario.total_coins, 100)

class QuestionModelTests(TestCase):
    """Test cases for Question models"""
    
    def setUp(self):
        self.survey = Survey.objects.create(title='Test Survey')
        self.scenario = Scenario.objects.create(
            name='Test Scenario', survey=self.survey, order=1
        )
        
    def test_survey_question_creation(self):
        """Test creating a survey question"""
        question = SurveyQuestion.objects.create(
            text='What is your name?',
            survey=self.survey,
            order=1,
            question_type='text',
            is_required=True
        )
        self.assertEqual(question.text, 'What is your name?')
        self.assertTrue(question.is_required)
        
    def test_scenario_question_creation(self):
        """Test creating a scenario question"""
        question = ScenarioQuestion.objects.create(
            text='Rate this scenario',
            scenario=self.scenario,
            order=1,
            question_type='single_choice',
            is_required=False
        )
        self.assertEqual(question.text, 'Rate this scenario')
        self.assertFalse(question.is_required)
        
    def test_planning_unit_question_creation(self):
        """Test creating a planning unit question"""
        question = PlanningUnitQuestion.objects.create(
            text='How important is this area?',
            scenario=self.scenario,
            order=1,
            question_type='number'
        )
        self.assertEqual(question.text, 'How important is this area?')
        
    def test_question_options(self):
        """Test creating question options"""
        question = SurveyQuestion.objects.create(
            text='Choose your favorite color',
            survey=self.survey,
            order=1,
            question_type='single_choice'
        )
        
        option1 = SurveyQuestionOption.objects.create(
            text='Red', question=question, order=1
        )
        option2 = SurveyQuestionOption.objects.create(
            text='Blue', question=question, order=2
        )
        
        choices = question.get_choices()
        self.assertEqual(len(choices), 2)
        self.assertEqual(choices[0][1], 'Red')
        self.assertEqual(choices[1][1], 'Blue')

class SurveyResponseModelTests(TestCase):
    """Test cases for SurveyResponse model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.survey = Survey.objects.create(title='Test Survey')
        
    def test_survey_response_creation(self):
        """Test creating a survey response"""
        response = SurveyResponse.objects.create(
            survey=self.survey,
            user=self.user
        )
        self.assertEqual(response.survey, self.survey)
        self.assertEqual(response.user, self.user)
        
    def test_survey_response_completed_property(self):
        """Test the completed property"""
        response = SurveyResponse.objects.create(
            survey=self.survey,
            user=self.user
        )
        
        # Should be complete when no required questions
        self.assertTrue(response.completed)
        
        # Add required question
        question = SurveyQuestion.objects.create(
            text='Required question',
            survey=self.survey,
            order=1,
            question_type='text',
            is_required=True
        )
        
        # Should not be complete now
        self.assertFalse(response.completed)
        
        # Add answer
        SurveyAnswer.objects.create(
            response=response,
            question=question,
            text_answer='Test answer'
        )
        
        # Should be complete now
        self.assertTrue(response.completed)

class AnswerModelTests(TestCase):
    """Test cases for Answer models"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.survey = Survey.objects.create(title='Test Survey')
        self.response = SurveyResponse.objects.create(
            survey=self.survey,
            user=self.user
        )
        
    def test_survey_answer_creation(self):
        """Test creating a survey answer"""
        question = SurveyQuestion.objects.create(
            text='Test question',
            survey=self.survey,
            order=1,
            question_type='text'
        )
        
        answer = SurveyAnswer.objects.create(
            response=self.response,
            question=question,
            text_answer='Test answer'
        )
        
        self.assertEqual(answer.text_answer, 'Test answer')
        self.assertEqual(answer.value, 'Test answer')
        
    def test_numeric_answer(self):
        """Test numeric answer"""
        question = SurveyQuestion.objects.create(
            text='Test number question',
            survey=self.survey,
            order=1,
            question_type='number'
        )
        
        answer = SurveyAnswer.objects.create(
            response=self.response,
            question=question,
            numeric_answer=42.5
        )
        
        self.assertEqual(answer.numeric_answer, 42.5)
        self.assertEqual(answer.value, 42.5)

    def test_select_single_answer(self):
        """Test single choice answer"""
        question = SurveyQuestion.objects.create(
            text='Select one option',
            survey=self.survey,
            order=1,
            question_type='single_choice'
        )
        option1 = SurveyQuestionOption.objects.create(
            text='Option 1', question=question, order=1
        )
        option2 = SurveyQuestionOption.objects.create(
            text='Option 2', question=question, order=2
        )
        
        answer = SurveyAnswer.objects.create(
            response=self.response,
            question=question,
            selected_options=[{"option_id": option1.id, "text": option1.text}]
        )
        
        self.assertEqual(len(answer.selected_options), 1)
        self.assertEqual(answer.selected_options[0]['text'], 'Option 1')
        self.assertEqual(answer.value, [(option1.pk, 'Option 1')])

    def test_select_multiple_answer(self):
        """Test multiple choice answer"""
        question = SurveyQuestion.objects.create(
            text='Select multiple options',
            survey=self.survey,
            order=1,
            question_type='multiple_choice'
        )
        option1 = SurveyQuestionOption.objects.create(
            text='Option 1', question=question, order=1
        )
        option2 = SurveyQuestionOption.objects.create(
            text='Option 2', question=question, order=2
        )
        
        answer = SurveyAnswer.objects.create(
            response=self.response,
            question=question,
            selected_options=[
                {"option_id": option1.id, "text": option1.text},
                {"option_id": option2.id, "text": option2.text}
            ]
        )
        
        self.assertEqual(len(answer.selected_options), 2)
        self.assertEqual(answer.selected_options[0]['text'], 'Option 1')
        self.assertEqual(answer.selected_options[1]['text'], 'Option 2')
        self.assertEqual(answer.value, [(option1.pk, 'Option 1'), (option2.pk, 'Option 2')])

class PlanningUnitModelTests(TestCase):
    """Test cases for PlanningUnit models"""
    
    def setUp(self):
        self.pu_family = PlanningUnitFamily.objects.create(
            name='Test Family',
            description='Test planning unit family'
        )
        
    def test_planning_unit_family_creation(self):
        """Test creating a planning unit family"""
        self.assertEqual(self.pu_family.name, 'Test Family')
        self.assertEqual(str(self.pu_family), 'Test Family')
        
    def test_planning_unit_creation(self):
        """Test creating a planning unit"""
        # Create a simple polygon geometry
        polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        multipolygon = MultiPolygon(polygon)
        
        pu = PlanningUnit.objects.create(
            geometry=multipolygon
        )
        pu.family.add(self.pu_family)
        
        self.assertIsNotNone(pu.geometry)
        self.assertIn(self.pu_family, pu.family.all())

class SurveyViewTests(TestCase):
    """Test cases for Survey views"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.group = Group.objects.create(name='testgroup')
        self.map_group = MapGroup.objects.create(
            name='Test Map Group',
            owner=self.user
        )[0]
        # self.map_group.mapgroupmember_set.create(user=self.user)
        
        self.survey = Survey.objects.create(
            title='Test Survey',
            description='Test description',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30)
        )
        self.survey.groups.add(self.map_group)
        
    def test_get_myplanner_survey_content_unauthenticated(self):
        """Test getting survey content when not authenticated"""
        response = self.client.get(
            reverse('survey:get_myplanner_survey_content')
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('html', data)
        
    def test_get_myplanner_survey_content_authenticated(self):
        """Test getting survey content when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:get_myplanner_survey_content')
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn('html', data)
        
    def test_survey_start_unauthenticated(self):
        """Test starting survey when not authenticated"""
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': self.survey.pk})
        )
        self.assertEqual(response.status_code, 403)
        
    def test_survey_start_authenticated(self):
        """Test starting survey when authenticated"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': self.survey.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('response_id', data)
        
    def test_survey_start_nonexistent_survey(self):
        """Test starting non-existent survey"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': 99999})
        )
        self.assertEqual(response.status_code, 404)
        
    def test_survey_start_expired_survey(self):
        """Test starting expired survey"""
        expired_survey = Survey.objects.create(
            title='Expired Survey',
            start_date=timezone.now() - timedelta(days=30),
            end_date=timezone.now() - timedelta(days=1)
        )
        expired_survey.groups.add(self.map_group)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': expired_survey.pk})
        )
        self.assertEqual(response.status_code, 403)
        
    def test_survey_start_future_survey(self):
        """Test starting future survey"""
        future_survey = Survey.objects.create(
            title='Future Survey',
            start_date=timezone.now() + timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30)
        )
        future_survey.groups.add(self.map_group)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': future_survey.pk})
        )
        self.assertEqual(response.status_code, 403)
        
    def test_survey_start_no_permission(self):
        """Test starting survey without permission"""
        other_group = Group.objects.create(name='othergroup')
        self.other_user = User.objects.create_user(
            username='otheruser',
            email='othertest@example.com',
            password='testpass123'
        )

        other_map_group = MapGroup.objects.create(
            name='Other Map Group',
            owner=self.other_user
        )[0]
        restricted_survey = Survey.objects.create(
            title='Restricted Survey',
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30)
        )
        restricted_survey.groups.add(other_map_group)
        
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': restricted_survey.pk})
        )
        self.assertEqual(response.status_code, 403)
        
    def test_survey_post_response(self):
        """Test posting survey response"""
        question = SurveyQuestion.objects.create(
            text='Test question',
            survey=self.survey,
            order=1,
            question_type='text'
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # First get the survey to create response
        response = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': self.survey.pk})
        )
        data = json.loads(response.content)
        response_id = data['response_id']
        
        # Then post answer
        post_data = {
            f'question_{question.id}': 'Test answer'
        }
        response = self.client.post(
            reverse('survey:survey_start', kwargs={'surveypk': self.survey.pk}),
            data=post_data
        )
        self.assertEqual(response.status_code, 200)
        
    def test_get_survey_scenario_form(self):
        """Test getting scenario form"""
        scenario = Scenario.objects.create(
            name='Test Scenario',
            survey=self.survey,
            order=1
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create response first
        survey_response = SurveyResponse.objects.create(
            survey=self.survey,
            user=self.user
        )
        
        response = self.client.get(
            reverse('survey:get_survey_scenario_form', kwargs={
                'response_id': survey_response.id,
                'scenario_id': scenario.id
            })
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['status'], 'success')
        self.assertIn('html', data)
        
    def test_get_survey_scenario_form_nonexistent_response(self):
        """Test getting scenario form with non-existent response"""
        scenario = Scenario.objects.create(
            name='Test Scenario',
            survey=self.survey,
            order=1
        )
        
        self.client.login(username='testuser', password='testpass123')
        
        response = self.client.get(
            reverse('survey:get_survey_scenario_form', kwargs={
                'response_id': 99999,
                'scenario_id': scenario.id
            })
        )
        self.assertEqual(response.status_code, 404)

class SurveyAPITests(TestCase):
    """Test cases for Survey API functionality"""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        # self.group = Group.objects.create(name='testgroup')
        self.map_group = MapGroup.objects.create(
            name='Test Map Group',
            owner=self.user
        )[0]
        # self.map_group.mapgroupmember_set.create(user=self.user)
        
    def test_api_multiple_responses_allowed(self):
        """Test API when multiple responses are allowed"""
        survey = Survey.objects.create(
            title='Multiple Response Survey',
            allow_multiple_responses=True,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30)
        )
        survey.groups.add(self.map_group)
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create first response
        response1 = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': survey.pk})
        )
        self.assertEqual(response1.status_code, 200)
        
        # Create second response (should be allowed... once implemented)
        response2 = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': survey.pk})
        )
        # self.assertEqual(response2.status_code, 200)
        # Not implemented yet!
        self.assertEqual(response2.status_code, 501)
        
    def test_api_single_response_only(self):
        """Test API when only single response is allowed"""
        survey = Survey.objects.create(
            title='Single Response Survey',
            allow_multiple_responses=False,
            start_date=timezone.now() - timedelta(days=1),
            end_date=timezone.now() + timedelta(days=30)
        )
        survey.groups.add(self.map_group)
        
        self.client.login(username='testuser', password='testpass123')
        
        # Create first response
        response1 = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': survey.pk})
        )
        self.assertEqual(response1.status_code, 200)
        data1 = json.loads(response1.content)
        
        # Try to create second response (should return existing)
        response2 = self.client.get(
            reverse('survey:survey_start', kwargs={'surveypk': survey.pk})
        )
        self.assertEqual(response2.status_code, 200)
        data2 = json.loads(response2.content)
        
        # Should return the same response ID
        self.assertEqual(data1['response_id'], data2['response_id'])

class CoinAssignmentTests(TestCase):
    """Test cases for coin assignment functionality"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.survey = Survey.objects.create(title='Test Survey')
        self.pu_family = PlanningUnitFamily.objects.create(
            name='Test Family'
        )
        self.scenario = Scenario.objects.create(
            name='Test Scenario',
            survey=self.survey,
            order=1,
            pu_family=self.pu_family,
            is_weighted=True,
            total_coins=100
        )
        self.response = SurveyResponse.objects.create(
            survey=self.survey,
            user=self.user
        )
        polygon = Polygon(((0, 0), (0, 1), (1, 1), (1, 0), (0, 0)))
        polygon2 = Polygon(((1, 0), (1, 1), (2, 1), (2, 0), (1, 0)))
        multipolygon = MultiPolygon(polygon)
        multipolygon2 = MultiPolygon(polygon2)
        
        self.planning_unit = PlanningUnit.objects.create(
            geometry=multipolygon
        )
        self.planning_unit2 = PlanningUnit.objects.create(
            geometry=multipolygon2
        )
        self.planning_unit.family.add(self.pu_family)
        self.planning_unit2.family.add(self.pu_family)  
        
    def test_coin_assignment_creation(self):
        """Test creating a coin assignment"""
        assignment = CoinAssignment.objects.create(
            response=self.response,
            scenario=self.scenario,
            planning_unit=self.planning_unit,
            coins_assigned=25
        )
        
        self.assertEqual(assignment.coins_assigned, 25)
        self.assertEqual(assignment.response, self.response)
        self.assertEqual(assignment.scenario, self.scenario)
        self.assertEqual(assignment.planning_unit, self.planning_unit)
        self.assertEqual(self.response.completed, False)
        
        current_scenario_status = self.response.scenario_status(self.scenario.pk)
        self.assertEqual(current_scenario_status['is_weighted'], True)
        self.assertEqual(current_scenario_status['coins_required'], True)
        self.assertEqual(current_scenario_status['coins_assigned'], 25)
        self.assertEqual(current_scenario_status['questions_completed'], True)
        self.assertEqual(current_scenario_status['planning_unit_questions_completed'], True)
        self.assertEqual(current_scenario_status['coins_completed'], False)
        self.assertEqual(current_scenario_status['scenario_completed'], False)
        self.assertEqual(current_scenario_status['coins_available'], 75)
        self.assertEqual(current_scenario_status['areas_selected'], 1)


        assignment2 = CoinAssignment.objects.create(
            response=self.response,
            scenario=self.scenario,
            planning_unit=self.planning_unit2,
            coins_assigned=74
        )

        self.assertEqual(assignment2.coins_assigned, 74)
        self.assertEqual(assignment2.response, self.response)
        self.assertEqual(assignment2.scenario, self.scenario)
        self.assertEqual(assignment2.planning_unit, self.planning_unit2)
        
        current_scenario_status = self.response.scenario_status(self.scenario.pk)
        self.assertEqual(current_scenario_status['coins_assigned'], 99)
        self.assertEqual(current_scenario_status['coins_completed'], False)
        self.assertEqual(current_scenario_status['scenario_completed'], False)
        self.assertEqual(current_scenario_status['coins_available'], 1)
        self.assertEqual(current_scenario_status['areas_selected'], 2)


        self.assertEqual(self.response.completed, False)

        assignment2.coins_assigned = 75
        assignment2.save()

        self.assertEqual(self.response.completed, True)
        
        current_scenario_status = self.response.scenario_status(self.scenario.pk)
        self.assertEqual(current_scenario_status['coins_assigned'], 100)
        self.assertEqual(current_scenario_status['coins_completed'], True)
        self.assertEqual(current_scenario_status['scenario_completed'], True)
        self.assertEqual(current_scenario_status['coins_available'], 0)
        self.assertEqual(current_scenario_status['areas_selected'], 2)

    def test_coin_assignment_unique_constraint(self):
        """Test unique constraint on coin assignments"""
        CoinAssignment.objects.create(
            response=self.response,
            scenario=self.scenario,
            planning_unit=self.planning_unit,
            coins_assigned=25
        )
        
        # Should not be able to create duplicate
        with self.assertRaises(Exception):
            CoinAssignment.objects.create(
                response=self.response,
                scenario=self.scenario,
                planning_unit=self.planning_unit,
                coins_assigned=50
            )

