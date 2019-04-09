from django.shortcuts import render
from django.views.generic import TemplateView
from .functions import parsing, reCaptcha


class IndexView(TemplateView):
    template_name = 'checkweb/index.html'


class AboutView(TemplateView):
    template_name = 'checkweb/about.html'


class ContactView(TemplateView):
    template_name = 'checkweb/contact.html'


class CheckView(TemplateView):
    template_name = 'checkweb/index.html'
    template_success = 'checkweb/check.html'

    def post(self, request):
        url = request.POST['url']
        # reCaptcha
        if reCaptcha(request.POST['g-recaptcha-response']):
            # Parsing
            context = parsing(url)
            if context:
                context['url'] = url
                return render(request, self.template_success, context)
            return render(request, self.template_name, {'errURL': True, 'url': url})

        return render(request, self.template_name, {'errCC': True, 'url': url})
