from django.contrib import messages
from django.shortcuts import redirect, render
from django.views.generic import TemplateView

from .functions import parsing, re_captcha


class IndexView(TemplateView):
    template_name = "checker/index.html"


class AboutView(TemplateView):
    template_name = "checker/about.html"


class ContactView(TemplateView):
    template_name = "checker/contact.html"


class CheckView(TemplateView):
    template_name = "checker/check.html"
    template_error = "checker/index.html"

    def post(self, request):
        url = request.POST["url"]
        # reCaptcha
        if re_captcha(
            request.POST["g-recaptcha-response"], request.META["REMOTE_ADDR"]
        ):
            # Parsing
            context = parsing(url)
            if context:
                context["url"] = url
                return render(request, self.template_name, context)
            messages.info(request, url)
            messages.error(
                request, "* Không phân tích được URL. Vui lòng kiểm tra lại!"
            )
            return redirect("/")
        messages.info(request, url)
        messages.error(request, "* Bạn chưa được kiểm tra không phải là robot!")
        return redirect("/")

    def get_context_data(self, **kwargs):
        context = super(CheckView, self).get_context_data()
        context.update(
            {
                "title": "Phân tích & Đánh giá SEO cho website của bạn | Đánh Giá Web",
                "description": "Trang phân tích, đánh giá SEO cho website nhanh chóng, chính xác và miễn phí",
                "pageRank": 0,
                "favicon": "https://checkseo.top/static/img/favicon.png",
                "robotsMeta": "index, follow, noodp, noydir",
                "h1Tags": ["Phân tích & Đánh giá SEO"],
                "h2Tags": ["Nhanh chóng, Chính xác, Miễn phí"],
                "robotsTxt": "https://checkseo.top/robots.txt",
                "sitemaps": ["https://checkseo.top/sitemap.xml"],
                "aBrokens": [],
                "cssInlines": [],
                "missAlts": [],
                "url": "https://checkseo.top/",
            }
        )
        return context
