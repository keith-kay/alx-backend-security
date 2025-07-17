# ip_tracking/middleware.py

from ipware import get_client_ip
from django.http import HttpResponseForbidden
from .models import RequestLog, BlockedIP
import datetime
from django.utils.deprecation import MiddlewareMixin

class IPLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip, _ = get_client_ip(request)
        if ip is None:
            ip = "Unknown"

        # Block if IP is in blacklist
        if BlockedIP.objects.filter(ip_address=ip).exists():
            return HttpResponseForbidden("Access Denied: Your IP has been blocked.")

        # Log the request
        RequestLog.objects.create(
            ip_address=ip,
            timestamp=datetime.datetime.now(),
            path=request.path
        )
