from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import RequestLog, SuspiciousIP

@shared_task
def detect_suspicious_ips():
    now = timezone.now()
    one_hour_ago = now - timedelta(hours=1)

    # 1. Flag IPs with > 100 requests in the last hour
    from django.db.models import Count
    heavy_ips = (
        RequestLog.objects.filter(timestamp__gte=one_hour_ago)
        .values('ip_address')
        .annotate(request_count=Count('id'))
        .filter(request_count__gt=100)
    )

    for entry in heavy_ips:
        SuspiciousIP.objects.get_or_create(
            ip_address=entry['ip_address'],
            reason='Excessive requests (>100/hour)'
        )

    # 2. Flag IPs accessing sensitive paths
    sensitive_paths = ['/admin', '/login']
    flagged = RequestLog.objects.filter(timestamp__gte=one_hour_ago, path__in=sensitive_paths)
    for log in flagged:
        SuspiciousIP.objects.get_or_create(
            ip_address=log.ip_address,
            reason=f"Accessed sensitive path: {log.path}"
        )
