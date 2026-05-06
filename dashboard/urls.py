from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('options/', views.options, name='options'),
    path('visualize/', views.visualize_data, name='visualize'),
    path('insights/', views.get_insights, name='insights'),
    path('analyze/', views.perform_analysis, name='analyze'),
]
