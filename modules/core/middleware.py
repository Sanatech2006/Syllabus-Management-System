from django.shortcuts import redirect


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

        # These paths are always public — no login needed
        self.public_paths = [
            '/login/',
            '/logout/',
            '/dashboard/',
            '/courses/',
            '/admin/',
            '/static/',
            '/media/',
        ]

    def __call__(self, request):
        current_path = request.path_info

        # Always allow authenticated users
        if request.user.is_authenticated:
            return self.get_response(request)

        # Allow public paths
        for path in self.public_paths:
            if current_path.startswith(path):
                return self.get_response(request)

        # Root path '/' → allow (redirects to dashboard)
        if current_path == '/':
            return self.get_response(request)

        # Everything else → redirect to login with destination preserved
        return redirect(f'/login/?next={current_path}')