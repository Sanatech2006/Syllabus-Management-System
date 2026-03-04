from django.shortcuts import redirect

class LoginProtectionMiddleware:  # ✅ CORRECT CLASS NAME
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        allowed_paths = [
            '/core/login/',
            '/core/logout/',
            '/dashboard/',
            '/courses/',
            '/admin/'
        ]
        
        if (not request.session.get('logged_in') and 
            request.path not in allowed_paths and 
            not request.path.startswith('/static/') and
            not request.path.startswith('/media/')):
            return redirect('/core/login/')
        
        return self.get_response(request)
