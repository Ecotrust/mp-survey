from urllib import response
from django.http import HttpResponse, JsonResponse
from django.template.loader import render_to_string
from django.utils import timezone
from .models import Survey, SurveyResponse
from datetime import datetime
from django.shortcuts import render
from .forms import SurveyResponseForm, ScenarioForm

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
        now = timezone.now()
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

def get_myplanner_survey_content(request, template='survey/survey_myplanner_content.html'):
    return JsonResponse({
        'html': get_myplanner_html(request, template)
    })

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

def get_survey_response(request, surveypk, responsepk=None):
    user = request.user
    response = None
    survey = None

    # check if user is authenticated
    if not user.is_authenticated:
        return {
            'status': 'error',
            'status_code': 403,
            'message': 'User must be authenticated to start a survey.'
        }
    # Get survey and response if responsepk is provided
    if responsepk is not None:
        try:
            response = SurveyResponse.objects.get(pk=responsepk, user=user)
            if response.survey.pk != int(surveypk):
                return {
                    'status': 'error',
                    'status_code': 404,
                    'message': 'Provided response ID does not match provided survey ID.'
                }
            survey = response.survey
        except SurveyResponse.DoesNotExist:
            return {
                'status': 'error',
                'status_code': 404,
                'message': 'No matching survey response found for this user.'
            }
    else:
        # Get survey
        try:
            survey = Survey.objects.get(pk=surveypk)
        except Survey.DoesNotExist:
            return {
                'status': 'error',
                'status_code': 404,
                'message': 'Survey does not exist.'
            }

    # Check if user is in any of the groups for this survey
    if not survey.groups.filter(mapgroupmember__user=user).exists():
        return {
            'status': 'error',
            'status_code': 403,
            'message': 'User does not have permission to take this survey.'
        }
        
    # check if survey is active
    now = timezone.now()
    if survey.start_date and survey.start_date > now:
        return {
            'status': 'error',
            'status_code': 403,
            'message': 'Survey has not started yet.'
        }
    if survey.end_date and survey.end_date < now:
        return {
            'status': 'error',
            'status_code': 403,
            'message': 'Survey has ended.'
        }

    if not survey.allow_multiple_responses:
        # Check for existing responses
        existing_responses = SurveyResponse.objects.filter(survey=survey, user=user)
        if existing_responses.count() > 1:
            return {
                'status': 'error',
                'status_code': 400,
                'message': 'Multiple responses found for a survey that does not allow them.'
            }
        elif existing_responses.count() == 1:
            if response is not None and response not in existing_responses:
                return {
                    'status': 'error',
                    'status_code': 400,
                    'message': 'This user already has another response for this survey.'
                }
            elif response is None:
                response = existing_responses.first()
    
    # if no existing response, create a new one
    if response is None:
        try:
            response = SurveyResponse.objects.create(survey=survey, user=user)
        except Exception as e:
            return {
                'status': 'error',
                'status_code': 500,
                'message': f'Error creating survey response: {str(e)}'
            }   
        
    return {
        'status': 'success',
        'status_code': 200,
        'message': 'Survey response ready.',
        'response': response,
        # 'survey': survey
    }

def survey_start(request, surveypk, responsepk=None):
    survey_response = get_survey_response(request, surveypk, responsepk)

    if isinstance(survey_response, dict) and survey_response.get('status') == 'error':
        return HttpResponse(survey_response, status=survey_response.get('status_code', 400))

    response = survey_response.get('response')

    if request.method == 'POST':
        context = save_survey_response(request, response)
        return JsonResponse(context, status=context.get('status_code', 200))
    
    next_scenario = response.survey.get_scenarios().first()

    return JsonResponse({
        'status': 'success',
        'status_code': 200,
        'message': 'Survey response form loaded.',
        'html': get_response_form(response, request).content.decode('utf-8'),
        'response_id': response.id,
        'survey_id': response.survey.id,
        'next_scenario_id': next_scenario.id if next_scenario else False
    }) 

# def get_survey_scenario_form(request, response_id, scenario_id, template='survey/survey_scenario_form.html'):
def get_survey_scenario_form(request, response_id, scenario_id, template='survey/survey_response_form.html'):
    try:
        response = SurveyResponse.objects.get(pk=response_id, user=request.user)
    except SurveyResponse.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'status_code': 404,
            'message': 'Survey response not found.'
        }, status=404)
    
    scenario = response.survey.get_scenarios().filter(id=scenario_id).first()
    if scenario is None:
        return JsonResponse({
            'status': 'error',
            'status_code': 404,
            'message': 'Scenario not found in this survey.'
        }, status=404)
    
    next_scenario = response.survey.get_next_scenario(scenario_id)

    context = {
        'response': response,
        'survey': response.survey,
        'scenario': scenario,
        'questions': scenario.scenario_questions_scenario.all(),
        'user': response.user,
        'form': ScenarioForm(response=response, scenario=scenario)
    }
    rendered = render(request, template, context)
    return JsonResponse({
        'status': 'success',
        'status_code': 200,
        'message': 'Scenario form loaded.',
        'html': rendered.content.decode('utf-8'),
        'next_scenario_id': next_scenario.id if next_scenario else False
    })

def get_response_form(response, request, template='survey/survey_response_form.html'):
    if response is None or request is None:
        return None
    context = {
        'response': response,
        'survey': response.survey,
        'questions': response.survey.survey_questions_survey.all(),
        'user': response.user,
        'form': SurveyResponseForm(survey=response.survey, instance=response)
    }
    return render(request, template, context)
    