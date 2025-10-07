import os
from django.test import TestCase
from django.core.management import call_command
from django.core.management.base import CommandError
from django.contrib.gis.geos import MultiPolygon
from survey.models import PlanningUnitFamily, PlanningUnit


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
