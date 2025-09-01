import json

from des.models import DynamicEmailConfiguration
from django.conf import settings
from django.core.mail import send_mail
from django.http import HttpResponse
from django.shortcuts import render
from django.template import loader
from django.utils.translation import gettext as _
from django.views.decorators.http import require_http_methods

subject = getattr(settings, "DES_TEST_SUBJECT", _("Test Email"))
text_template = getattr(settings, "DES_TEST_TEXT_TEMPLATE", "des/test_email.txt")
html_template = getattr(settings, "DES_TEST_HTML_TEMPLATE", None)

message_text = loader.render_to_string(text_template)
message_html = loader.render_to_string(html_template) if html_template else None


@require_http_methods(["POST"])
def send_test_email(request):
    body_unicode = request.body.decode("utf-8")
    body = json.loads(body_unicode)
    to_email = body.get("to_email")
    config = DynamicEmailConfiguration.get_solo()
    response = {}
    if to_email:
        try:
            send_mail(
                subject,
                message_text,
                config.from_email or None,
                [to_email],
                html_message=message_html,
            )
            response["detail"] = _(
                "Test email sent. Please check '{}' for a "
                "message with the subject '{}'"
            ).format(to_email, subject)
        except Exception as e:
            response["error"] = _(f"Could not send email. {e}")
    else:
        response["error"] = _("You must provide an email address to test with.")
    return HttpResponse(json.dumps(response))


def test_visualiza_email(request):
    return render(request, "fluxo_autorizar_negar_cancelar.html")
