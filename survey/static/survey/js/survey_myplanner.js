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
    app.viewModel.scenarios.externalForm(false);
    $("#myplanner-survey-dialog").hide();
}

function takeNewSurvey(surveyId){
    // Populate form field with loader
    $('#myplanner-survey-dialog-body').html(
        '<h3>Loading new survey...</h3>'
    );
    showSurveyForm();
    // AJAX call to get form HTML
    $.ajax({
        url: '/survey/start/'+surveyId+'/',
        type: 'GET',
        success: function(data) {
            $('#myplanner-survey-dialog-body').html(data);
        },
        error: function(xhr, status, error) {
            $('#myplanner-survey-dialog-body').html(
                '<h3>Error loading survey. Please try again later.</h3>'
            );
        }
    });
}

function continueSurvey(responseId){
    // Populate form field with loader
    $('#myplanner-survey-dialog-body').html(
        '<h3>Loading your survey...</h3>'
    );
    showSurveyForm();
    // AJAX call to get form HTML
    $.ajax({
        url: '/survey/continue/'+responseId+'/',
        type: 'GET',
        success: function(data) {
            $('#myplanner-survey-dialog-body').html(data);
        },
        error: function(xhr, status, error) {
            $('#myplanner-survey-dialog-body').html(
                '<h3>Error loading survey. Please try again later.</h3>'
            );
        }
    });
}