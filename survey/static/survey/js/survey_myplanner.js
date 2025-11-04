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
    refreshSurveyContent()
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
            console.error('Error refreshing survey content:', error);
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

function loadNextSurveyScenario(surveyId, responseId, scenarioId, nextScenarioId) {
    // TODO: Ajax call to load next scenario
    // window.alert('Loading next scenario. Id: ' + nextScenarioId);
    $.ajax({
        url: '/survey/scenario/'+responseId+'/'+nextScenarioId+'/',
        type: 'GET',
        success: function(data) {
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