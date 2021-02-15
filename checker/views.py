from django.core.validators import URLValidator, ValidationError
from django.conf import settings
from django.contrib import messages
from django.shortcuts import render, redirect, reverse
from django.views.generic import TemplateView

from urllib.parse import parse_qsl
from .forms import SiteForm


class IndexView(TemplateView):
    template_name = 'checker/index.html'

    def get_context_data(self, **kwargs):
        context = super(IndexView, self).get_context_data()
        form_init = dict()

        # get messages from ResultView
        msgs = messages.get_messages(self.request)
        for msg in msgs:
            if msg.level == messages.INFO:
                form_init = dict(parse_qsl(str(msg)))

        context['form'] = SiteForm(initial=form_init)
        return context


class ResultView(TemplateView):
    template_name = 'checker/result.html'

    def get_context_data(self, **kwargs):
        context = super(ResultView, self).get_context_data()
        if settings.DEBUG:
            result_script = 'result.js'
        else:
            result_script = 'result.min.js'
        context['result_script'] = result_script
        return context

    def post(self, request):
        url, url_clone = str(), str()
        form = SiteForm(request.POST)
        if form.is_valid():
            url = form.cleaned_data['url']
            if not url.startswith(('http://', 'https://')):
                # use HTTPS as the default
                url_clone = url
                url = f'https://{url}'
            try:
                URLValidator().__call__(url)
            except ValidationError:
                messages.info(request, f'url={url_clone}')
                messages.error(request, 'URL validator error')
                return redirect(reverse('checker:index'))

        context = self.get_context_data()
        context['url'] = url
        return render(request, self.template_name, context)
