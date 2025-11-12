from django.core.management.base import BaseCommand
from school.models import Student, Teacher


class Command(BaseCommand):
    help = 'Regenerate student admission numbers and teacher employee IDs to ST#### and TC#### format'

    def handle(self, *args, **options):
        # Regenerate student admission numbers
        students = Student.objects.all().order_by('id')
        self.stdout.write('Regenerating student admission numbers...')
        
        for idx, student in enumerate(students, start=1):
            old_admission = student.admission_number
            new_admission = f"ST{idx:04d}"
            student.admission_number = new_admission
            student.save(update_fields=['admission_number'])
            self.stdout.write(f'  {old_admission} → {new_admission} ({student.user.get_full_name()})')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Updated {students.count()} student admission numbers'))
        
        # Regenerate teacher employee IDs
        teachers = Teacher.objects.all().order_by('id')
        self.stdout.write('\nRegenerating teacher employee IDs...')
        
        for idx, teacher in enumerate(teachers, start=1):
            old_employee_id = teacher.employee_id
            new_employee_id = f"TC{idx:04d}"
            teacher.employee_id = new_employee_id
            teacher.save(update_fields=['employee_id'])
            self.stdout.write(f'  {old_employee_id} → {new_employee_id} ({teacher.user.get_full_name()})')
        
        self.stdout.write(self.style.SUCCESS(f'✓ Updated {teachers.count()} teacher employee IDs'))
        self.stdout.write(self.style.SUCCESS('\n✓ All IDs regenerated successfully!'))
