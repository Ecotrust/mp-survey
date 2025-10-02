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
}

function continueSurvey(responseId){
    // Populate form field with loader
    $('#myplanner-survey-dialog-body').html(
        '<h3>Loading your survey...</h3>'
    );
    showSurveyForm();
    // AJAX call to get form HTML
}