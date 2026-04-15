import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth.models import User

admin_user = User.objects.get(username='admin')
admin_user.set_password('admin123')
admin_user.save()

print("Password for user 'admin' set to 'admin123'")
