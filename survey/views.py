from django.template.loader import render_to_string

def get_myplanner_js(request):
    js_tag = '<script src="/static/survey/js/survey_myplanner.js"></script>'
    return js_tag

def get_myplanner_html(request, template='survey/survey_myplanner.html'):
    context = {}
    rendered = render_to_string(template, context=context, request=request)
    return rendered

def get_myplanner_css(request):
    return ''