from .models import AuditLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # We only want to log mutating actions as requested
        if request.user.is_authenticated and request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            action = f"{request.method} {request.path}"
            
            details = {
                'method': request.method,
                'path': request.path,
                'query_string': request.META.get('QUERY_STRING', ''),
                'user_agent': request.META.get('HTTP_USER_AGENT', '')
            }
            
            AuditLog.objects.create(
                user=request.user,
                action=action,
                details=details,
                ip_address=get_client_ip(request)
            )

        response = self.get_response(request)
        return response
