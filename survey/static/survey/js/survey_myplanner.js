$( "#group-surveys-header" ).on( "click", function() {
    $( "#survey-planner-content" ).slideToggle( "fast", function() {
      // Animation complete.
    });
});

function showSurveyForm(surveyId) {
    app.viewModel.scenarios.externalForm(true);
    $("#myplanner-survey-dialog").show();
}

function hideSurveyForm() {
    app.viewModel.scenarios.externalForm(false);
    $("#myplanner-survey-dialog").hide();
}