from django.urls import path, re_path
from . import views

app_name = 'survey'

urlpatterns = [
    # path('', views.survey_list, name='survey_list'),
    re_path(r'start/(?P<surveypk>\d+)/?$', views.survey_start, name='survey_start'),
    # path('<int:pk>/', views.survey_detail, name='survey_detail'),
    # path('create/', views.survey_create, name='survey_create'),
    # path('<int:pk>/edit/', views.survey_edit, name='survey_edit'),
    # path('<int:pk>/delete/', views.survey_delete, name='survey_delete'),
]