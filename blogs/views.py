from django.shortcuts import render
from django.views.generic import TemplateView


class Tips1View(TemplateView):
    """
    Tips 1: Các tiêu chuẩn SEO
    """
    template_name = 'blogs/tips1.html'
