import os

path = os.path.join('modules', 'course_manage', 'views.py')

with open(path, 'r') as f:
    content = f.read()

content = content.replace(
    "redirect('course_management')",
    "redirect('course_manage:course_management')"
)

with open(path, 'w') as f:
    f.write(content)

print("Fixed! All redirects updated.")