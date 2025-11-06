from django.contrib.auth import get_user_model

User = get_user_model()

# Create an admin user
user = User.objects.create_user(
    username='admin',
    email='admin@example.com',
    password='admin123',
    is_staff=True,
    is_superuser=True,
    user_type='admin'
)
print("Admin user created successfully!")