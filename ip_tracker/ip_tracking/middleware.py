from ipware import get_client_ip
from .models import RequestLog
import datetime
from django.utils.deprecation import MiddlewareMixin

class IPLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip, _ = get_client_ip(request)
        if ip is None:
            ip = "Unknown"

        RequestLog.objects.create(
            ip_address=ip,
            timestamp=datetime.datetime.now(),
            path=request.path
        )
