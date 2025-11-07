$( "#group-surveys-header" ).on( "click", function() {
    $( "#survey-planner-content" ).slideToggle( "fast", function() {
      // Animation complete.
    });
    if ($("#group-surveys-header").hasClass("active")) {
        $("#group-surveys-header").removeClass("active");
    } else {
        $("#group-surveys-header").addClass("active");
    }   
});

function showSurveyForm() {
    app.viewModel.scenarios.externalForm(true);
    $("#myplanner-survey-dialog").show();
}

function hideSurveyForm() {
    refreshSurveyContent();
    app.map.on('singleclick', app.wrapper.listeners['singleclick']);
    app.viewModel.scenarios.externalForm(false);
    $("#myplanner-survey-dialog").hide();
}

function hideNavButtons() {
    $('#myplanner-survey-dialog-next').hide();
    $('#myplanner-survey-dialog-save').hide();
}

function showNextButton() {
    $('#myplanner-survey-dialog-save').hide();
    $('#myplanner-survey-dialog-next').show();
}

function showSaveButton() {
    $('#myplanner-survey-dialog-next').hide();
    $('#myplanner-survey-dialog-save').show();
}

function refreshSurveyContent() {
    let active_survey_layer_boxes = $('#myplanner-survey-dialog').find('input[type=checkbox]:checked');
    active_survey_layer_boxes.prop('checked', false);
    active_survey_layer_boxes.change();
    $('#survey-planner-content').html('<p>Loading...</p>');
    let url = '/survey/myplanner/content/';
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            $('#survey-planner-content').html(data.html);
        },
        error: function(xhr, status, error) {
            $('#survey-planner-content').html('Error refreshing survey content.<br/>' +
                '<button class="btn btn-success btn-sm" onclick="refreshSurveyContent()">Try Again</button>'
            );
        }
    });
}

function takeSurvey(surveyId, responseId){
    // Populate form field with loader
    hideNavButtons();
    $('#myplanner-survey-dialog-body').html(
        '<h3>Loading survey...</h3>'
    );
    let url = '/survey/start/'+surveyId+'/';
    if (responseId) {
        url += responseId + '/';
    }
    showSurveyForm();
    // AJAX call to get form HTML
    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            app.survey.survey_id = data.survey_id;
            app.survey.response_id = data.response_id;
            app.survey.scenario_id = null;
            $('#myplanner-survey-dialog-body').html(data.html);
            if (data.next_scenario_id) {
                $('#myplanner-survey-dialog-next').off('click');
                $('#myplanner-survey-dialog-next').on('click', function(e) {
                    submitSurveyForm(
                        '/survey/start/'+surveyId+'/'+data.response_id+'/', 
                        function(saveData) {
                            if (saveData.status === 'success') {
                                // window.alert('Survey responses saved. Thank you!');
                                // refreshSurveyContent();
                                // hideSurveyForm();
                                loadNextSurveyScenario(surveyId, data.response_id, data.scenario_id, data.next_scenario_id);
                            } else {
                                window.alert('Error saving survey responses. Please try again.');
                            }
                        }
                    );
                    e.preventDefault();
                });
                showNextButton();
            } else {
                $('#myplanner-survey-dialog-save').off('click');
                $('#myplanner-survey-dialog-save').on('click', function(e) {
                    submitSurveyForm(
                        '/survey/start/'+surveyId+'/'+data.response_id+'/',
                        function(saveData) {
                            if (saveData.status === 'success') {
                                window.alert('Survey responses saved. Thank you!');
                                refreshSurveyContent();
                                hideSurveyForm();
                            } else {
                                window.alert('Error saving survey responses. Please try again.');
                            }
                        }
                    );
                    e.preventDefault();
                });
                showSaveButton();
            }
            if (data.layer_groups_html) {
                $('#myplanner-survey-layers-list').html(data.layer_groups_html);
                $('#myplanner-survey-layers-slideup-button').show();
                enableSurveyLayerControls(data.layer_groups);
            } else {
                $('#myplanner-survey-layers-slideup-button').hide();
            }
        },
        error: function(xhr, status, error) {
            $('#myplanner-survey-dialog-body').html(
                '<h3>Error loading survey. Please try again later.</h3>'
            );
            hideNavButtons();
        }
    });
}

function enableSurveyLayerControls(layerGroups) {
    // Enable layer controls based on the provided layer groups
    // ensure layer objects exist in app.viewModel
    for (let group_idx in layerGroups) {
        let group = layerGroups[group_idx];
        for (let i = 0; i < group.layers.length; i++) {
            let layer = group.layers[i];
            app.viewModel.getOrCreateLayer(
                {
                    id: layer.id,
                    name: layer.name,
                    slug_name: layer.slug_name,
                }, //layer_obj
                null, //parent
                "return", //action
                null //event
            );
            if (layer.auto_show) {
                app.viewModel.getLayerById(layer.id).activateLayer();
            }
        }
    }

}

app.survey = {}

app.survey.toggleSurveyLayer = function(event, layer_id) {
    let layer = app.viewModel.getLayerById(layer_id);
    if (layer) {
        if (layer.active() && event.target.checked === false){
            layer.deactivateLayer();
        } else if (!layer.active() && event.target.checked === true){
            layer.activateLayer();
        }
    }
}

app.survey.addPlanningUnitsLayer = function(geojson_object) {
    // Written assuming OpenLayers 8
    let source = new ol.source.Vector({wrapX: false});

    source.clear();
    if (geojson_object !== null && geojson_object !== undefined) {
        let json_features = new ol.format.GeoJSON({featureProjection: app.map.getView().getProjection()}).readFeatures(geojson_object);
        source.addFeatures(json_features);
    }

    // Thanks to TomazicM at https://gis.stackexchange.com/a/425178 for help getting styles to work
    let featureStyleCache = {};

    function getFeatureColor(properties) {
        if (properties.existing == 'yes') {
            return [216, 125, 27];
        } else {
            return [134, 216, 27];
        }
    }

    function getFeatureStyle(properties) {
      if (!featureStyleCache[properties.existing]) {
        const color = getFeatureColor(properties);
        featureStyleCache[properties.existing] = new ol.style.Style({
            fill: new ol.style.Fill({
                color: `rgba(${color[0]}, ${color[1]}, ${color[2]}, 0.4)`,
            }),
            stroke: new ol.style.Stroke({
                color: `rgba(${color[0]}, ${color[1]}, ${color[2]}, 1)`,
                width: 2,
            }),
        });
      }
      return featureStyleCache[properties.existing];
    }

    function selectedPUStyleFunction(feature, resolution) {
      return getFeatureStyle(feature.getProperties());
    }

    app.survey.planningUnitLayer = new ol.layer.Vector({
        source: source,
        style: selectedPUStyleFunction,
    });

    app.map.addLayer(app.survey.planningUnitLayer);

}

app.survey.enableExistingPUSelection = function() {};


app.survey.loadPlanningUnitsLayer = function(geometries) {
    // create vector layer with geometries
    if (app.survey.planningUnitLayer !== undefined) {
        app.map.removeLayer(app.survey.planningUnitLayer);
    }
    app.survey.addPlanningUnitsLayer(geometries);
};

app.survey.selectPlanningUnitListener = function(event) {
    features = app.map.getFeaturesAtPixel(event.pixel);
    selected_pu_feature = false;
    for (let i = 0; i < features.length; i++) {
        if (app.survey.planningUnitLayer.getSource().hasFeature(features[i])) {
            selected_pu_feature = features[i];
            break;
        }
    }
    if (selected_pu_feature) {
        if (selected_pu_feature.get('existing') === 'yes') {
            console.log('This Planning Unit has already been selected.');
            return;
        } else{
            app.survey.planningUnitLayer.getSource().removeFeature(selected_pu_feature);
        }
    } else {
        if (event.pixel) {
            let coordinate = app.map.getCoordinateFromPixel(event.pixel);
            url = '/survey/scenario/' + app.survey.scenario_id + '/get_area_by_point?x=' + coordinate[0] + '&y=' + coordinate[1];
            $.ajax({
                url: url,
                type: 'GET',
                success: function(data) {
                    if (data.status === 'success') {
                        if (data.planning_unit_geometry !== null && data.planning_unit_geometry !== undefined) {
                            geometry_geojson = {
                                'type': 'FeatureCollection',
                                'crs': {
                                    'type': 'name',
                                    'properties': {
                                    'name': 'EPSG:3857',
                                    },
                                },
                                'features': [
                                    {
                                        'type': 'Feature',
                                        'geometry': JSON.parse(data.planning_unit_geometry),
                                        'properties': {
                                            'planning_unit_id': data.planning_unit_id,
                                            'existing': 'no',
                                        },
                                    },
                                ],
                            };

                            let source = app.survey.planningUnitLayer.getSource();
                            source.addFeatures(new ol.format.GeoJSON().readFeatures(geometry_geojson));
                        }

                    } else {
                        window.alert('No planning unit found at the selected location.');
                    }
                },
                error: function(xhr, status, error) {
                    window.alert('Error retrieving planning unit. Please try again.');
                }
            });
                    
        } else {
            window.alert('No feature or coordinate found in event.');
        }
    }
}

app.survey.startPlanningUnitSelection = function(event) {
    // hide form
    $('#survey-scenario-pu-form').hide();
    $('#survey-scenario-pu-select-areas-button').prop('disabled', true);
    // show instructions
    // show cancel button
    $('#survey-scenario-pu-selection-block').show();
    // handle drawing vs. selection?
    app.map.un('singleclick', app.wrapper.listeners['singleclick']);
    app.map.on('singleclick', app.survey.selectPlanningUnitListener);

}

app.survey.stopPlanningUnitSelection = function(event) {
    $('#survey-scenario-pu-selection-block').hide();
    $('#survey-scenario-pu-select-areas-button').prop('disabled', false);
    $('#survey-scenario-pu-form').show();
    app.map.un('singleclick', app.survey.selectPlanningUnitListener);
    app.map.on('singleclick', app.wrapper.listeners['singleclick']);
    // enable form
    // hide instructions?
    // hide cancel button
}

function loadNextSurveyScenario(surveyId, responseId, scenarioId, nextScenarioId) {
    // TODO: Ajax call to load next scenario
    // window.alert('Loading next scenario. Id: ' + nextScenarioId);
    $.ajax({
        url: '/survey/scenario/'+responseId+'/'+nextScenarioId+'/',
        type: 'GET',
        success: function(data) {
            app.survey.survey_id = data.survey_id;
            app.survey.response_id = data.response_id;
            app.survey.scenario_id = data.scenario_id;
            $('#myplanner-survey-dialog-body').html(data.html);
            if (data.next_scenario_id) {
                $('#myplanner-survey-dialog-next').off('click');
                $('#myplanner-survey-dialog-next').on('click', function() {
                    loadNextSurveyScenario(surveyId, responseId, data.scenario_id, data.next_scenario_id);
                });
                showNextButton();
            } else {
                $('#myplanner-survey-dialog-save').off('click');
                $('#myplanner-survey-dialog-save').on('click', function(e) {
                    submitSurveyForm(
                        '/survey/scenario/'+responseId+'/'+data.scenario_id+'/',
                        function(saveData) {
                            if (saveData.status === 'success') {
                                window.alert('Scenario responses saved. Thank you!');
                                refreshSurveyContent();
                                hideSurveyForm();
                            } else {
                                window.alert('Error saving survey responses. Please try again.');
                            }
                        }
                    );
                    e.preventDefault();
                });
                showSaveButton();
            }
            if (data.is_spatial) {
                app.survey.loadPlanningUnitsLayer(data.planning_units_geojson);
            }
        },
        error: function(xhr, status, error) {
            $('#myplanner-survey-dialog-body').html(
                '<h3>Error loading survey scenario. Please try again later.</h3>'
            );
            hideNavButtons();
        }
    });
}

function submitSurveyForm(url, successCallback) {
    let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;

    // AJAX call to save form data
    $.ajax({
        type: 'POST',
        url: url,
        headers: { 'X-CSRFToken': csrftoken },
        data: $('#myplanner-survey-dialog-body form').serialize(),
        success: successCallback,
        error: function() {
            window.alert('Error saving survey responses. Please try again.');
        }
    });
}

function showLayersPanel() {
    $('#myplanner-survey-layer-button-before i').removeClass('fa-chevron-up');
    $('#myplanner-survey-layer-button-before i').addClass('fa-chevron-down');
    $('#myplanner-survey-layers-slideup-button').addClass('active');
    $('#myplanner-survey-layers-container').animate({height: '80%'}, 300);
}

function hideLayersPanel() {
    $('#myplanner-survey-layer-button-before i').removeClass('fa-chevron-down');
    $('#myplanner-survey-layer-button-before i').addClass('fa-chevron-up');
    $('#myplanner-survey-layers-slideup-button').removeClass('active');
    $('#myplanner-survey-layers-container').animate({height: 0}, 300);
}

function toggleLayersPanel() {
    if ($('#myplanner-survey-layers-slideup-button').hasClass('active')) {
        hideLayersPanel();
    } else {
        showLayersPanel();
    }
}

function showLayersGroup(group_id) {
    let group_container_id = '#'+group_id;
    let group_header_id = group_container_id+"-header";
    let group_toggle_icon = group_header_id+" span.myplanner-survey-layer-group-collapse i";
    $(group_toggle_icon).removeClass('fa-chevron-right');
    $(group_toggle_icon).addClass('fa-chevron-down');
    $(group_header_id).addClass('active');
    $(group_container_id).slideDown(300, function(){});
}

function hideLayersGroup(group_id) {
    let group_container_id = '#'+group_id;
    let group_header_id = group_container_id+"-header";
    let group_toggle_icon = group_header_id+" span.myplanner-survey-layer-group-collapse i";
    $(group_toggle_icon).removeClass('fa-chevron-down');
    $(group_toggle_icon).addClass('fa-chevron-right');
    $(group_header_id).removeClass('active');
    $(group_container_id).slideUp(300, function(){});
}

function toggleLayersGroup(group_id) {
    if ($('#'+group_id+"-header").hasClass('active')) {
        hideLayersGroup(group_id);
    } else {
        showLayersGroup(group_id);
    }
}
