from django.contrib.auth import get_user_model
from school.models import Class, Subject, Term, Teacher, Student, Mark, Comment
from django.utils import timezone

User = get_user_model()

# Create classes
c1, _ = Class.objects.get_or_create(name='Grade 1', defaults={'level':'1','academic_year':'2024/2025'})
c2, _ = Class.objects.get_or_create(name='Grade 2', defaults={'level':'2','academic_year':'2024/2025'})

# Create subjects
s_math, _ = Subject.objects.get_or_create(code='MATH101', defaults={'name':'Mathematics'})
s_eng, _ = Subject.objects.get_or_create(code='ENG101', defaults={'name':'English'})
s_sci, _ = Subject.objects.get_or_create(code='SCI101', defaults={'name':'Science'})

# Create an active term
term, _ = Term.objects.get_or_create(term='1', academic_year='2024/2025', defaults={'start_date':timezone.now().date(),'end_date':timezone.now().date(),'is_active':True})

# Create a teacher user
teacher_user, created = User.objects.get_or_create(username='teacher1', defaults={'email':'teacher1@example.com','user_type':'teacher','first_name':'Alice','is_staff':False})
if created:
    teacher_user.set_password('teacher123')
    teacher_user.save()

teacher, _ = Teacher.objects.get_or_create(user=teacher_user, defaults={'employee_id':'T1001'})
# assign subjects and classes
teacher.subjects.set([s_math, s_eng])
teacher.classes.set([c1])

# Create a student user
student_user, created = User.objects.get_or_create(username='student1', defaults={'email':'student1@example.com','user_type':'student','first_name':'Bob'})
if created:
    student_user.set_password('student123')
    student_user.save()

student, _ = Student.objects.get_or_create(user=student_user, defaults={'admission_number':'S1001','student_class':c1,'date_of_birth':'2012-01-01','guardian_name':'Parent','guardian_phone':'1234567890'})

# Create marks for the student
for subj,assign,mid,exam in [
    (s_math, 15, 25, 40),
    (s_eng, 12, 20, 35),
    (s_sci, 10, 18, 30),
]:
    mk, created = Mark.objects.get_or_create(student=student, subject=subj, term=term, class_assigned=c1, defaults={'teacher':teacher})
    mk.assignment_marks = assign
    mk.midterm_marks = mid
    mk.exam_marks = exam
    mk.save()

# Add a comment
cm, created = Comment.objects.get_or_create(student=student, term=term, defaults={'teacher':teacher, 'class_teacher_comment':'Good progress', 'headteacher_comment':'Keep it up'})

print('Sample data created: classes, subjects, term, teacher, student, marks, comment')
