from django.urls import path
from . import views

urlpatterns = [
    path('cac-tieu-chuan-seo/', views.Tips1View.as_view(), name='tips1'),
]
