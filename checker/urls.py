from django.urls import path

from .views import (IndexView, ResultView)
from .api import get_status, parse_content

app_name = 'checker'

urlpatterns = [
    path('', IndexView.as_view(), name='index'),
    path('result', ResultView.as_view(), name='result'),
    path('api/get-status', get_status, name='api-get-status'),
    path('api/parse-content', parse_content, name='api-parse-content'),
]
