import requests

base_url = "http://127.0.0.1:8000"
test_urls = [
    ('/', 'Home'),
    ('/dashboard/', 'Dashboard'),
    ('/courses/', 'Courses'),
    ('/login/', 'Login'),
    ('/programs/', 'Programs'),
    ('/uploads/upload-center/', 'Upload Center'),
    ('/users/', 'Users'),
    ('/random-page/', 'Random Page'),
]

print("Testing URL access (should be logged out):")
print("-" * 60)

session = requests.Session()

for url, name in test_urls:
    full_url = base_url + url
    response = session.get(full_url, allow_redirects=False)
    
    if response.status_code == 302:  # Redirect
        redirect_url = response.headers.get('Location', '')
        if '/login/' in redirect_url:
            print(f"✅ {name:20} → Redirected to login (correct)")
        else:
            print(f"❌ {name:20} → Redirected to {redirect_url}")
    elif response.status_code == 200:  # Success
        if url in ['/', '/dashboard/', '/courses/', '/login/']:
            print(f"✅ {name:20} → Accessible (correct)")
        else:
            print(f"❌ {name:20} → Should NOT be accessible!")
    else:
        print(f"⚠️ {name:20} → Status {response.status_code}")