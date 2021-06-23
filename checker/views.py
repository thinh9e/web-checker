from urllib.parse import parse_qsl, urlsplit

from django.conf import settings
from django.contrib import messages
from django.core.validators import URLValidator, ValidationError
from django.shortcuts import render, redirect, reverse
from django.views.generic import TemplateView

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
            schemes = ('http', 'https')
            try:
                url = self.validate_url(url, schemes)
            except ValidationError:
                messages.info(request, f'url={url}')
                messages.error(request, 'URL validator error')
                return redirect(reverse('checker:index'))

        context = self.get_context_data()
        context['url'] = url
        return render(request, self.template_name, context)

    @staticmethod
    def validate_url(url: str, schemes: tuple) -> str:
        """
        Check a string is a valid URL or raise a ValidationError

        :param url: string need to check
        :param schemes: list allow schemes
        :return: a valid URL
        """
        url_parse = urlsplit(url)
        url_scheme = url_parse.scheme
        if url_scheme == '':
            # use HTTPS as the default
            url = f'https://{url}'
        elif url_scheme not in schemes:
            raise ValidationError(URLValidator.message, URLValidator.code)

        # re-parse url
        url_parse = urlsplit(url)
        url_netloc = url_parse.netloc
        # except for email
        exception_chars = {'@'}
        for char in exception_chars:
            if char in url_netloc:
                raise ValidationError(URLValidator.message, URLValidator.code)

        URLValidator(schemes=schemes)(url)
        return url
