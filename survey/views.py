from django.http import HttpResponse
from django.template.loader import render_to_string
from .models import Survey, SurveyResponse
from datetime import datetime
# from django.http import JsonResponse
from django.shortcuts import render
from .forms import SurveyResponseForm

def get_myplanner_js(request):
    js_tag = '<script src="/static/survey/js/survey_myplanner.js"></script>'
    return js_tag

def get_myplanner_html(request, template='survey/survey_myplanner.html'):
    context = {
        'GROUP_SURVEYS': [],
        'SURVEY_STATUS': []
    }
    user = request.user
    if user.is_authenticated:
        # get current date-time
        now = datetime.now()
        # get surveys that are active
        surveys = Survey.objects.filter(start_date__lte=now, end_date__gte=now)
        for survey in surveys:
            if survey.groups.filter(mapgroupmember__user=user).exists() and not survey in context['GROUP_SURVEYS']:
                context['GROUP_SURVEYS'].append(survey)
                if SurveyResponse.objects.filter(survey=survey, user=user).exists():
                    for response in SurveyResponse.objects.filter(survey=survey, user=user):
                        context['SURVEY_STATUS'].append(
                            {
                                'survey': survey,
                                'response': response
                            }
                        )
                else:
                    context['SURVEY_STATUS'].append(
                        {
                            'survey': survey,
                            'response': None
                        }
                    )

    if len(context['GROUP_SURVEYS']) == 0:
        return ''
    rendered = render_to_string(template, context=context, request=request)
    return rendered

def get_myplanner_css(request):
    return '<link rel="stylesheet" href="/static/survey/css/survey_myplanner.css" type="text/css">'

def get_myplanner_dialog(request, template='survey/survey_myplanner_dialog.html'):
    context = {}
    rendered = render_to_string(template, context=context, request=request)
    return rendered

def save_survey_response(request, response):
    error_message = 'There were errors in the form.'
    if request.method == 'POST':
        form = SurveyResponseForm(request.POST, survey=response.survey, instance=response)
        if form.is_valid():
            try:
                form.save_answers(response, response.survey)
                try:
                    response.save()
                
                    return {
                        'status': 'success',
                        'status_code': 200,
                        'message': 'Survey response saved successfully.',
                        'response_id': response.id,
                        'survey_id': response.survey.id
                    }
                except Exception as e:
                    error_message = 'Error saving survey response.'
                    pass
            except Exception as e:
                error_message = 'Error saving answers.'
                pass
    else:
        error_message = 'Invalid request method. Only POST requests are allowed.'
    return {
        'status': 'error',
        'status_code': 400,
        'message': error_message,
        'errors': form.errors
    }

def survey_start(request, surveypk):
    user = request.user
    if not user.is_authenticated:
        return None
    try:
        survey = Survey.objects.get(pk=surveypk)
    except Survey.DoesNotExist:
        return None
    # check if user is in any of the groups for this survey
    if not survey.groups.filter(mapgroupmember__user=user).exists():
        return None
    response = None
    responses = SurveyResponse.objects.filter(survey=survey, user=user)
    for response_candidate in responses:
        if hasattr(survey, 'allow_multiple_responses') and survey.allow_multiple_responses:
            # check if there is an existing incomplete response
            if not response_candidate.completed:
                response = response_candidate
                break
        else:
            response = response_candidate
            break
    # if no existing incomplete response, create a new one
    if response is None:
        response = SurveyResponse.objects.create(survey=survey, user=user)
    # return JsonResponse({'response_id': response.id, 'survey_id': survey.id, 'response_form': response.get_form(request), 'step': 1, 'steps': survey.get_step_count()})
    if request.method == 'POST':
        context = save_survey_response(request, response)
        return HttpResponse(context)
    return get_response_form(response,request)

def survey_continue(request, responsepk):
    user = request.user
    if not user.is_authenticated:
        return None
    try:
        response = SurveyResponse.objects.get(pk=responsepk, user=user)
    except SurveyResponse.DoesNotExist:
        return None
    if request.method == 'POST':
        context = save_survey_response(request, response)
        return HttpResponse(context)
    return get_response_form(response,request)

def get_response_form(response, request, template='survey/survey_response_form.html'):
    if response is None or request is None:
        return None
    context = {
        'response': response,
        'survey': response.survey,
        # 'scenarios': self.survey.scenarios_survey.all(),
        'questions': response.survey.survey_questions_survey.all(),
        'user': response.user,
        'form': SurveyResponseForm(survey=response.survey, instance=response)
    }
    return render(request, template, context)
    