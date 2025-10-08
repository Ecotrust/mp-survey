$( "#group-surveys-header" ).on( "click", function() {
    $( "#survey-planner-content" ).slideToggle( "fast", function() {
      // Animation complete.
    });
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
                    // Logic to load next scenario if applicable
                    // For now, just hide the dialog
                    loadNextSurveyScenario(surveyId, responseId, data.next_scenario_id);
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
    window.alert('Loading next scenario. Id: ' + nextScenarioId);
}
