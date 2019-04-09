from django.urls import path
from . import views

urlpatterns = [
    path('', views.IndexView.as_view(), name='index'),
    path('gioi-thieu/', views.AboutView.as_view(), name='about'),
    path('lien-he/', views.ContactView.as_view(), name='contact'),
    path('kiem-tra/', views.CheckView.as_view(), name='check'),
]
