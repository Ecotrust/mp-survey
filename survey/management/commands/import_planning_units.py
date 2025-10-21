import os
import zipfile
import tempfile
import shutil
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.contrib.gis.geos import GEOSGeometry, MultiPolygon
from django.conf import settings
from survey.models import PlanningUnitFamily, PlanningUnit

try:
    from osgeo import ogr

    ogr.UseExceptions()  # Enable GDAL exceptions to avoid FutureWarning
except ImportError:
    raise CommandError(
        "GDAL is required for this command. Please install it using: "
        "pip install gdal or conda install gdal"
    )


class Command(BaseCommand):
    help = "Imports planning units from a specified file into a Planning Unit Family. Creates or updates units."

    def add_arguments(self, parser):
        parser.add_argument(
            "input_file",
            type=str,
            help="The absolute or relative path to the source data file.",
        )
        parser.add_argument(
            "--family-name",
            type=str,
            help="The name of the Planning Unit Family to associate the units with. "
            "If a family with this name exists, it will be used; otherwise, a new one will be created.",
        )

    def handle(self, *args, **options):
        input_file = options["input_file"]
        family_name = options.get("family_name")

        # Validate input file exists
        if not os.path.exists(input_file):
            raise CommandError(f"Input file does not exist: {input_file}")

        # Handle zip files
        temp_dir = None
        original_input_file = (
            input_file  # Store original file path for family description
        )
        try:
            if input_file.lower().endswith(".zip"):
                self.stdout.write(f"Extracting zip file: {input_file}")
                temp_dir = tempfile.mkdtemp()
                with zipfile.ZipFile(input_file, "r") as zip_ref:
                    zip_ref.extractall(temp_dir)

                # Find the .shp file in the extracted contents
                shp_file = self._find_shp_file(temp_dir)
                if not shp_file:
                    raise CommandError(
                        f"No shapefile (.shp) found in zip archive: {input_file}"
                    )

                input_file = shp_file
                self.stdout.write(f"Using shapefile from zip: {shp_file}")

            # Resolve Planning Unit Family using original file path for description
            family = self._resolve_planning_unit_family(
                original_input_file, family_name
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Found or created Planning Unit Family: {family.name}"
                )
            )

            # Read and process the file
            self.stdout.write(f"Reading features from {input_file}...")
            features = self._read_features(input_file)

            if not features:
                raise CommandError("No valid features found in the source file.")

            self.stdout.write(f"Importing {len(features)} planning units...")
            created_count = self._import_planning_units(features, family)

            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully imported planning units: {created_count} created"
                )
            )

        except Exception as e:
            raise CommandError(f"Import failed: {str(e)}")
        finally:
            # Clean up temporary directory if created
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)

    def _resolve_planning_unit_family(self, input_file, family_name):
        """Resolve the PlanningUnitFamily based on provided name or generate from filename."""
        if not family_name:
            # Generate family name from input file
            base_name = os.path.splitext(os.path.basename(input_file))[0]
            family_name = base_name

        family, created = PlanningUnitFamily.objects.get_or_create(
            name=family_name, defaults={"description": f"Imported from {input_file}"}
        )
        return family

    def _read_features(self, input_file):
        """Read features from the input file using GDAL/OGR."""
        # Check if this is a shapefile missing projection information
        if input_file.lower().endswith(".shp"):
            prj_file = os.path.splitext(input_file)[0] + ".prj"
            if not os.path.exists(prj_file):
                raise CommandError(
                    f"Shapefile is missing projection information: {prj_file} not found. "
                    f"Shapefiles require a .prj file to define the coordinate system."
                )

        data_source = ogr.Open(input_file)
        if data_source is None:
            raise CommandError(f"Could not open file: {input_file}")

        layer = data_source.GetLayer()
        if layer is None:
            raise CommandError("Could not get layer from data source")

        # Get the spatial reference of the source data
        source_srs = layer.GetSpatialRef()
        if source_srs is None:
            raise CommandError("Could not determine spatial reference system of source data")

        # Create target spatial reference (database SRID)
        target_srs = ogr.osr.SpatialReference()
        target_srs.ImportFromEPSG(settings.SERVER_SRID)

        # Create coordinate transformation if needed
        transform = None
        if source_srs.IsSame(target_srs) == 0:  # 0 means not the same
            transform = ogr.osr.CoordinateTransformation(source_srs, target_srs)
            self.stdout.write(
                f"Transforming geometries from EPSG:{source_srs.GetAuthorityCode(None)} to EPSG:{settings.SERVER_SRID}"
            )

        features = []
        for i in range(layer.GetFeatureCount()):
            feature = layer.GetFeature(i)
            if feature is None:
                continue

            # Extract geometry
            geometry_ref = feature.GetGeometryRef()
            if geometry_ref is None:
                self.stdout.write(
                    self.style.WARNING(f"Feature {i} has no geometry, skipping")
                )
                continue

            try:
                # Transform geometry if needed
                if transform:
                    geometry_ref.Transform(transform)
                
                wkt_geometry = geometry_ref.ExportToWkt()
                geos_geometry = GEOSGeometry(wkt_geometry, srid=settings.SERVER_SRID)

                # Process both Polygon and MultiPolygon geometries
                if geos_geometry.geom_type not in ["Polygon", "MultiPolygon"]:
                    self.stdout.write(
                        self.style.WARNING(
                            f"Feature {i} is not a polygon or multipolygon ({geos_geometry.geom_type}), skipping"
                        )
                    )
                    continue

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(
                        f"Feature {i} has invalid geometry: {str(e)}, skipping"
                    )
                )
                continue

            # Extract attributes
            # attributes = {}
            # for j in range(feature.GetFieldCount()):
            #     field_defn = feature.GetFieldDefnRef(j)
            #     field_name = field_defn.GetName()
            #     field_value = feature.GetField(j)
            #     attributes[field_name] = field_value

            features.append({"geometry": geos_geometry})  # , "attributes": attributes})

        data_source = None  # Close the data source
        return features

    def _import_planning_units(self, features, family):
        """Import planning units from features into the database."""
        created_count = 0
        failed_count = 0

        for i, feature_data in enumerate(features):
            try:
                geometry = feature_data["geometry"]
                if geometry.geom_type == "Polygon":
                    geometry = MultiPolygon(geometry)

                # Wrap each planning unit creation in its own atomic transaction
                with transaction.atomic():
                    # Create the planning unit without attributes
                    planning_unit = PlanningUnit.objects.create(
                        geometry=geometry,
                    )
                    # Add the planning unit to the family (ManyToMany relationship)
                    planning_unit.family.add(family)
                    created_count += 1
                    
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Failed to create planning unit {i}: {str(e)}")
                )
                failed_count += 1
                # Continue with other features even if one fails

        # Log summary
        if failed_count > 0:
            self.stdout.write(
                self.style.WARNING(
                    f"Import completed with {failed_count} failures out of {len(features)} features"
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f"All {len(features)} features imported successfully"
                )
            )

        return created_count

    def _find_shp_file(self, directory):
        """Find the first .shp file in the root directory of the zip file."""
        for file in os.listdir(directory):
            if file.lower().endswith(".shp"):
                return os.path.join(directory, file)
        return None
