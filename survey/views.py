from django.template.loader import render_to_string
from .models import Survey
from datetime import datetime

def get_myplanner_js(request):
    js_tag = '<script src="/static/survey/js/survey_myplanner.js"></script>'
    return js_tag

def get_myplanner_html(request, template='survey/survey_myplanner.html'):
    context = {
        'GROUP_SURVEYS': []
    }
    user = request.user
    if user.is_authenticated:
        # get current date-time
        now = datetime.now()
        # get surveys that are active
        surveys = Survey.objects.filter(start_date__lte=now, end_date__gte=now)
        for survey in surveys:
            if survey.groups.filter(mapgroupmember__user=user).exists():
                context['GROUP_SURVEYS'].append(survey)

    if len(context['GROUP_SURVEYS']) == 0:
        return ''
    rendered = render_to_string(template, context=context, request=request)
    return rendered

def get_myplanner_css(request):
    return '<link rel="stylesheet" href="/static/survey/css/survey_myplanner.css" type="text/css">'