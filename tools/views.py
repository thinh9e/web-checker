from django.shortcuts import render, redirect
from django.contrib import messages
from django.views.generic import TemplateView
from .functions import parsing, reCaptcha


class IndexView(TemplateView):
    template_name = 'tools/index.html'


class AboutView(TemplateView):
    template_name = 'tools/about.html'


class ContactView(TemplateView):
    template_name = 'tools/contact.html'


class CheckView(TemplateView):
    template_name = 'tools/check.html'
    template_error = 'tools/index.html'

    def get(self, request):
        context = {
            'title': 'Phân tích & Đánh giá SEO cho website của bạn | Đánh Giá Web',
            'description': 'Trang phân tích, đánh giá SEO cho website nhanh chóng, chính xác và miễn phí',
            'pageRank': 0,
            'favicon': 'https://danhgiaweb.top/static/img/favicon.png',
            'robotsMeta': 'index, follow, noodp, noydir',
            'h1Tags': ['Phân tích & Đánh giá SEO'],
            'h2Tags': ['Nhanh chóng, Chính xác, Miễn phí'],
            'robotsTxt': 'https://danhgiaweb.top/robots.txt',
            'sitemaps': ['https://danhgiaweb.top/sitemap.xml'],
            'aBrokens': [],
            'cssInlines': [],
            'missAlts': [],
            'url': 'https://danhgiaweb.top/',
        }
        return render(request, self.template_name, context)

    def post(self, request):
        url = request.POST['url']
        # reCaptcha
        if reCaptcha(request.POST['g-recaptcha-response'], request.META['REMOTE_ADDR']):
            # Parsing
            context = parsing(url)
            if context:
                context['url'] = url
                return render(request, self.template_name, context)
            messages.info(request, url)
            messages.error(
                request, '* Không phân tích được URL. Vui lòng kiểm tra lại!')
            return redirect('/')
        messages.info(request, url)
        messages.error(
            request, '* Bạn chưa được kiểm tra không phải là robot!')
        return redirect('/')