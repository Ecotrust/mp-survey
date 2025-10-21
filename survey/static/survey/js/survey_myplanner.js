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
                $('#myplanner-survey-dialog-next').on('click', function() {
                    let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    // AJAX call to save form data
                    $.ajax({
                        type: 'POST',
                        url: '/survey/start/'+surveyId+'/'+data.response_id+'/',
                        headers: { 'X-CSRFToken': csrftoken },
                        data: $('#myplanner-survey-dialog-body form').serialize(),
                        success: function(saveData) {
                            if (saveData.status === 'success') {
                                // window.alert('Survey responses saved. Thank you!');
                                // refreshSurveyContent();
                                // hideSurveyForm();
                                loadNextSurveyScenario(surveyId, responseId, data.next_scenario_id);
                            } else {
                                window.alert('Error saving survey responses. Please try again.');
                            }
                        },
                        error: function() {
                            window.alert('Error saving survey responses. Please try again.');
                        }
                    });
                    e.preventDefault();
                    // Logic to load next scenario if applicable
                    // For now, just hide the dialog
                    // loadNextSurveyScenario(surveyId, responseId, data.next_scenario_id);
                });
                showNextButton();
            } else {
                $('#myplanner-survey-dialog-save').off('click');
                $('#myplanner-survey-dialog-save').on('click', function(e) {
                    let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
                    // AJAX call to save form data
                    $.ajax({
                        type: 'POST',
                        url: '/survey/start/'+surveyId+'/'+data.response_id+'/',
                        headers: { 'X-CSRFToken': csrftoken },
                        data: $('#myplanner-survey-dialog-body form').serialize(),
                        success: function(saveData) {
                            if (saveData.status === 'success') {
                                window.alert('Survey responses saved. Thank you!');
                                refreshSurveyContent();
                                hideSurveyForm();
                            } else {
                                window.alert('Error saving survey responses. Please try again.');
                            }
                        },
                        error: function() {
                            window.alert('Error saving survey responses. Please try again.');
                        }
                    });
                    e.preventDefault();
                });
                showSaveButton();
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

function loadNextSurveyScenario(surveyId, responseId, nextScenarioId) {
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
                    loadNextSurveyScenario(surveyId, responseId, data.next_scenario_id);
                });
                showNextButton();
            } else {
                $('#myplanner-survey-dialog-save').off('click');
                $('#myplanner-survey-dialog-save').on('click', function(e) {
                    finishSurvey(responseId);
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

function finishSurvey(responseId) {
    let csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    // AJAX call to save form data
    $.ajax({
        type: 'POST',
        url: '/survey/start/' + surveyId + '/' + responseId + '/',
        headers: { 'X-CSRFToken': csrftoken },
        data: $('#myplanner-survey-dialog-body form').serialize(),
        success: function(saveData) {
            if (saveData.status === 'success') {
                window.alert('Survey responses saved. Thank you!');
                refreshSurveyContent();
                hideSurveyForm();
            } else {
                window.alert('Error saving survey responses. Please try again.');
            }
        },
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