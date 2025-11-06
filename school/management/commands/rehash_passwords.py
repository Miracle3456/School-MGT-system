from django.core.management.base import BaseCommand

class Command(BaseCommand):
    help = 'Re-hash plaintext passwords stored on the custom User model if any exist.'

    def handle(self, *args, **options):
        from school.models import User
        prefixes = ('pbkdf2_', 'argon2$', 'bcrypt$', 'bcrypt_sha256$', 'sha1$', 'md5$')
        rehashed = 0
        for user in User.objects.all():
            pw = user.password or ''
            # If password doesn't look like a hashed value, assume it's raw and hash it.
            if pw and not pw.startswith(prefixes):
                raw = pw
                user.set_password(raw)
                user.save()
                rehashed += 1
                self.stdout.write(self.style.SUCCESS(f'Re-hashed password for: {user.username}'))

        self.stdout.write(self.style.SUCCESS(f'Done. {rehashed} user(s) re-hashed.'))
