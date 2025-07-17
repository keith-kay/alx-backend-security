import datetime
from django.utils.timezone import now
from ipgeolocation import IpGeolocationAPI
from django.core.cache import cache
from .models import RequestLog, BlockedIP
from .models import RequestLog
from django.utils.deprecation import MiddlewareMixin

# Replace with your actual API key
API_KEY = "YOUR_API_KEY"
geolocation_api = IpGeolocationAPI(API_KEY)

class RequestLoggingMiddleware(MiddlewareMixin):
    def process_request(self, request):
        ip = get_client_ip(request)
        path = request.path
        RequestLog.objects.create(ip_address=ip, path=path)

def get_client_ip(request):
    x_forwarded = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded:
        ip = x_forwarded.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class IPTrackingMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        ip = self.get_client_ip(request)

        # Block if in blacklist
        if BlockedIP.objects.filter(ip_address=ip).exists():
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("Access denied.")

        # Check cache
        cache_key = f"geo_{ip}"
        geo_data = cache.get(cache_key)

        if geo_data is None:
            response = geolocation_api.get_geolocation(ip_address=ip)
            geo_data = {
                'country': response.get('country_name', ''),
                'city': response.get('city', '')
            }
            cache.set(cache_key, geo_data, 60 * 60 * 24)  # Cache for 24 hours

        # Log request
        RequestLog.objects.create(
            ip_address=ip,
            path=request.path,
            country=geo_data['country'],
            city=geo_data['city'],
        )

        return self.get_response(request)

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR')
