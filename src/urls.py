from django.urls import path, include
from django.conf.urls import handler400, handler403, handler404, handler500
from . import views

urlpatterns = [
    path('', include('checkweb.urls')),
    path('robots.txt', views.Robots.as_view(), name='robots'),
    path('sitemap.xml', views.Sitemap.as_view(), name='sitemap'),
]

handler400 = views.bad_request
handler403 = views.permission_denied
handler404 = views.page_not_found
handler500 = views.server_error
