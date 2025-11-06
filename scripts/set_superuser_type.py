from django.contrib.auth import get_user_model
User = get_user_model()

username = 'admin'
try:
    u = User.objects.get(username=username)
    u.user_type = 'admin'
    u.is_staff = True
    u.is_superuser = True
    u.save()
    print('Updated', u.username, '->', u.user_type)
except User.DoesNotExist:
    print('User', username, 'does not exist.');
    # List first 5 users for debugging
    for q in User.objects.all()[:5]:
        print('-', q.username, getattr(q, 'user_type', None))
