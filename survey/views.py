from datetime import datetime
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from django.utils import timezone
from urllib import response
from urllib.parse import urlparse, parse_qs, unquote

from .forms import SurveyResponseForm, ScenarioForm, PlanningUnitForm
from .models import (
    Survey, SurveyLayerGroup, SurveyResponse, Scenario, ScenarioAnswer, 
    PlanningUnitAnswer
)

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
                form.save_answers(response)
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
    
    # if no existing response, or multiple allowed, create a new one
    if response is None:
        try:
            if SurveyResponse.objects.filter(survey=survey, user=user).exists():
                raise NotImplementedError('Multiple responses per user not yet implemented.')
            response = SurveyResponse.objects.create(survey=survey, user=user)
        except NotImplementedError as e:
            return {
                'status': 'error',
                'status_code': 501,
                'message': str(e)
            }
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

    layer_groups = {}
    if SurveyLayerGroup.objects.filter(survey=response.survey).exists():
        for group in response.survey.survey_layer_groups_survey.all().order_by('order'):
            layer_groups[group.id] = {
                'name': group.name,
                'id': group.id,
                'layers': []
            }
            for layer_order in group.survey_layer_orders_layer_group.all().order_by('order'):
                layer_groups[group.id]['layers'].append({
                    'name': layer_order.layer.name,
                    'id': layer_order.layer.id,
                    'slug_name': layer_order.layer.slug_name,
                    'order': layer_order.order,
                    'auto_show': layer_order.auto_show
                })

        layer_group_html = render_to_string('survey/survey_myplanner_layerpicker.html', {
            'layer_groups': layer_groups
        }, request=request)
    else:
        layer_group_html = False


    return JsonResponse({
        'status': 'success',
        'status_code': 200,
        'message': 'Survey response form loaded.',
        'html': get_response_form(response, request).content.decode('utf-8'),
        'response_id': response.id,
        'survey_id': response.survey.id,
        'layer_groups': layer_groups,
        'layer_groups_html': layer_group_html,
        'next_scenario_id': next_scenario.id if next_scenario else False
    }) 

def get_scenario_response(request, response_id, scenario_id):
    error = None
    status = 200
    try:
        response = SurveyResponse.objects.get(pk=response_id, user=request.user)
        scenario = response.survey.get_scenarios().filter(id=scenario_id).first()
        if scenario is None:
            error = {
                'status': 'error',
                'status_code': 404,
                'message': 'Scenario not found in this survey.'
            }
            status = 404
            pass
    except SurveyResponse.DoesNotExist:
        response = None
        scenario = None
        error = {
            'status': 'error',
            'status_code': 404,
            'message': 'Survey response not found.'
        }
        status = 404
        pass

    return {
        'response': response,
        'scenario': scenario,
        'error': error,
        'status': status
    }

def survey_scenario(request, response_id, scenario_id, template='survey/survey_myplanner_scenario_form.html'):
    scenario_dict = get_scenario_response(request, response_id, scenario_id)
    if scenario_dict['error'] is not None:
        return JsonResponse(scenario_dict['error'], status=scenario_dict['status'])
    else:
        response = scenario_dict['response']
        scenario = scenario_dict['scenario']

    if request.method == 'POST':
        
        form = ScenarioForm(request.POST, response=response, scenario=scenario)
        if form.is_valid():
            try:
                form.save_answers(response, scenario)
                try:
                    response.save()
                
                    return JsonResponse({
                        'status': 'success',
                        'status_code': 200,
                        'message': 'Scenario answers saved successfully.',
                        'response_id': response.id,
                        'survey_id': response.survey.id
                    })
                
                except Exception as e:
                    return JsonResponse({
                        'status': 'error',
                        'status_code': 500,
                        'message': 'Error saving survey response.'
                    }, status=500)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'status_code': 500,
                    'message': 'Error saving scenario answers.'
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'status_code': 400,
                'message': 'There were errors in the form.',
                'errors': form.errors
            }, status=400)
    else:
        scenario_status = response.scenario_status(scenario.pk)
    
        next_scenario = response.survey.get_next_scenario(scenario.id)

        form = ScenarioForm(response=response, scenario=scenario)

        if scenario.is_spatial:
            # TODO: Load existing PU selection layer!
            planning_unit_answers = PlanningUnitAnswer.objects.filter(response=response)

            selected_planning_units = []
            for pu in planning_unit_answers:
                if scenario.is_weighted:
                    coins = pu.coins
                else:
                    coins = None
                area = pu.planning_unit.geometry
                # TODO: insert attribute 'existing' = True
                # TODO: insert attribute 'coins' = coins
                selected_planning_units.append({'area': area, 'coins': coins, 'existing': 'yes'})\

            if len(form.fields) == 0 and len(selected_planning_units) == 0:
                # No planning unit selected yet, redirect to area selection
                return survey_scenario_area(request, response_id, scenario_id)
        else:
            selected_planning_units = []
            

        context = {
            'response': response,
            'survey': response.survey,
            'scenario': scenario,
            'scenario_status': scenario_status,
            'questions': scenario.scenario_questions_scenario.all(),
            'user': response.user,
            'form': form,
        }

        # TODO: Get Scenario Response, answers and summary
        rendered = render(request, template, context)
        return JsonResponse({
            'status': 'success',
            'status_code': 200,
            'message': 'Scenario form loaded.',
            'html': rendered.content.decode('utf-8'),
            'survey_id': response.survey.id,
            'response_id': response.id,
            'scenario_id': scenario.id,
            'next_scenario_id': next_scenario.id if next_scenario else False,
            'is_spatial': scenario.is_spatial,
            'is_weighted': scenario.is_weighted,
            'planning_units_geojson': selected_planning_units,
            'minimum_coins': scenario.min_coins_per_pu,
            'maximum_coins': scenario.max_coins_per_pu,
            'total_coins': scenario.total_coins,
            'require_all_coins': scenario.require_all_coins_used,
        })

def survey_scenario_area(request, response_id, scenario_id, unit_id=None, template='survey/survey_myplanner_unit_form.html'):
    scenario_dict = get_scenario_response(request, response_id, scenario_id)
    if scenario_dict['error'] is not None:
        return JsonResponse(scenario_dict['error'], status=scenario_dict['status'])
    else:
        response = scenario_dict['response']
        scenario = scenario_dict['scenario']

    if request.method == 'POST':
        form = PlanningUnitForm(request.POST, response=response, scenario=scenario)
        if form.is_valid():
            try:
                form.save_answers(response, scenario)
                try:
                    response.save()

                    return JsonResponse({
                        'status': 'success',
                        'status_code': 200,
                        'message': 'Planning unit answers saved successfully.',
                        'response_id': response.id,
                        'survey_id': response.survey.id
                    })

                except Exception as e:
                    return JsonResponse({
                        'status': 'error',
                        'status_code': 500,
                        'message': 'Error saving survey response.'
                    }, status=500)
            except Exception as e:
                return JsonResponse({
                    'status': 'error',
                    'status_code': 500,
                    'message': 'Error saving planning unit answers.'
                }, status=500)
        else:
            return JsonResponse({
                'status': 'error',
                'status_code': 400,
                'message': 'There were errors in the form.',
                'errors': form.errors
            }, status=400)
    else:
        scenario_status = response.scenario_status(scenario.pk)

        next_scenario = response.survey.get_next_scenario(scenario.id)

        context = {
            'response': response,
            'survey': response.survey,
            'scenario': scenario,
            'scenario_status': scenario_status,
            'questions': scenario.planning_unit_questions_scenario.all(),
            'user': response.user,
            'form': PlanningUnitForm(response=response, scenario=scenario)
        }

        # TODO: Get Scenario Response, answers and summary
        rendered = render(request, template, context)
        return JsonResponse({
            'status': 'success',
            'status_code': 200,
            'message': 'Area form loaded.',
            'html': rendered.content.decode('utf-8'),
            'scenario_id': scenario.id,
            'next_scenario_id': next_scenario.id if next_scenario else False,
            'is_spatial': scenario.is_spatial,
            'is_weighted': scenario.is_weighted,
            'minimum_coins': scenario.min_coins_per_pu,
            'maximum_coins': scenario.max_coins_per_pu,
            'total_coins': scenario.total_coins,
            'require_all_coins': scenario.require_all_coins_used,
        })


def get_scenario_pu_by_coordinates(request, scenario_id, x_coord=None, y_coord=None):
    try:
        scenario = Scenario.objects.get(id=scenario_id)
        if scenario.is_spatial is False:
            return JsonResponse({
                'status': 'error',
                'status_code': 400,
                'message': 'Scenario is not spatial.'
            }, status=400)
        
    except Scenario.DoesNotExist:
        return JsonResponse({
            'status': 'error',
            'status_code': 404,
            'message': 'Scenario not found.'
        }, status=404)
    
    querydict = parse_qs(urlparse(unquote(request.get_full_path())).query)

    if x_coord is None:
        x_coord = querydict.get('x', [None])[0]
    if y_coord is None:
        y_coord = querydict.get('y', [None])[0]

    planning_unit = scenario.get_planning_unit_by_coordinates(x_coord, y_coord)
    if planning_unit is None:
        return JsonResponse({
            'status': 'error',
            'status_code': 404,
            'message': 'No planning unit found at the provided coordinates.'
        }, status=404)
    
    planning_unit.geometry.transform(3857)  # Transform to web mercator

    return JsonResponse({
        'status': 'success',
        'status_code': 200,
        'message': 'Planning unit retrieved successfully.',
        'planning_unit_id': planning_unit.id,
        'planning_unit_geometry': planning_unit.geometry.geojson
    })
    
# def get_scenario_areas(request, response_id, scenario_id):
#     scenario_dict = get_scenario_response(request, response_id, scenario_id)
#     if scenario_dict['error'] is not None:
#         return JsonResponse(scenario_dict['error'], status=scenario_dict['status'])
#     else:
#         response = scenario_dict['response']
#         scenario = scenario_dict['scenario']

#     planning_unit_answers = PlanningUnitAnswer.objects.filter(response=response)

#     selected_planning_units = []
#     for pu in planning_unit_answers:
#         if scenario.is_weighted:
#             coins = pu.coins
#         else:
#             coins = None
#         area = pu.planning_unit.geometry
#         selected_planning_units.append({'area': area, 'coins': coins})

#     return JsonResponse({
#         'status': 'success',
#         'status_code': 200,
#         'message': 'Planning units retrieved successfully.',
#         'selected_planning_units': selected_planning_units
#     })

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
    