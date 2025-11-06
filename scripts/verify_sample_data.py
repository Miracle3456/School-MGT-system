from django.contrib.auth import get_user_model
from school.models import Class, Subject, Term, Teacher, Student, Mark, Comment

User = get_user_model()

print('Users:')
for u in User.objects.all():
    print('-', u.username, getattr(u, 'user_type', None), 'is_super:', u.is_superuser)

print('\nClasses:')
for c in Class.objects.all():
    print('-', c.name)

print('\nSubjects:')
for s in Subject.objects.all():
    print('-', s.code, s.name)

print('\nTerms:')
for t in Term.objects.all():
    print('-', t)

print('\nTeachers:')
for t in Teacher.objects.all():
    print('-', t.employee_id, t.user.username)

print('\nStudents:')
for s in Student.objects.all():
    print('-', s.admission_number, s.user.username)

print('\nMarks:')
for m in Mark.objects.all():
    print('-', m.student.user.username, m.subject.code, m.total_marks, m.grade)

print('\nComments:')
for c in Comment.objects.all():
    print('-', c.student.user.username, c.class_teacher_comment)