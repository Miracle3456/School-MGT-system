from django.core.management.base import BaseCommand
from school.models import Student, Teacher


class Command(BaseCommand):
    help = 'Updates all existing student admission numbers and teacher employee IDs to new format'

    def handle(self, *args, **options):
        # Update Students
        students = Student.objects.all().order_by('id')
        student_count = 0
        self.stdout.write('Updating student admission numbers...')
        
        for idx, student in enumerate(students, start=1):
            old_admission = student.admission_number
            new_admission = f"ST{idx:04d}"
            student.admission_number = new_admission
            student.save()
            student_count += 1
            self.stdout.write(f'  {old_admission} → {new_admission}')
        
        self.stdout.write(self.style.SUCCESS(f'\nUpdated {student_count} students'))
        
        # Update Teachers
        teachers = Teacher.objects.all().order_by('id')
        teacher_count = 0
        self.stdout.write('\nUpdating teacher employee IDs...')
        
        for idx, teacher in enumerate(teachers, start=1):
            old_employee_id = teacher.employee_id
            new_employee_id = f"TC{idx:04d}"
            teacher.employee_id = new_employee_id
            teacher.save()
            teacher_count += 1
            self.stdout.write(f'  {old_employee_id} → {new_employee_id}')
        
        self.stdout.write(self.style.SUCCESS(f'\nUpdated {teacher_count} teachers'))
        self.stdout.write(self.style.SUCCESS('\nAll IDs updated successfully!'))
