from django.urls import path, re_path
from . import views

app_name = 'survey'

urlpatterns = [
    # path('', views.survey_list, name='survey_list'),
    re_path(r'start/(?P<surveypk>\d+)/?(?P<responsepk>\d+)?/?$', views.survey_start, name='survey_start'),
    re_path(r'scenario/(?P<response_id>\d+)/(?P<scenario_id>\d+)/?$', views.survey_scenario, name='survey_scenario'),
    re_path(r'area/(?P<response_id>\d+)/(?P<scenario_id>\d+)/?(?P<unit_id>\d+)?/?$', views.survey_scenario_area, name='survey_scenario_area'),
    re_path(r'myplanner/content/?$', views.get_myplanner_survey_content, name='get_myplanner_survey_content'),
    # re_path(r'continue/(?P<responsepk>\d+)/?$', views.survey_continue, name='survey_continue'),
    # path('<int:pk>/', views.survey_detail, name='survey_detail'),
    # path('create/', views.survey_create, name='survey_create'),
    # path('<int:pk>/edit/', views.survey_edit, name='survey_edit'),
    # path('<int:pk>/delete/', views.survey_delete, name='survey_delete'),
]