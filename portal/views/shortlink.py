from django.shortcuts import get_object_or_404, redirect
from portal.models import ShortLink

def shortlink_redirect(request, code):
    shortlink = get_object_or_404(ShortLink, code=code)
    return redirect(shortlink.url)
