from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from .models import User, Class, Subject, Student, Teacher, Term, Mark, Comment, AcademicYear, Enrollment


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """Use Django's built-in UserAdmin which correctly handles password hashing
    and user creation forms. We extend it to expose our extra fields.
    """
    list_display = ['username', 'email', 'user_type', 'first_name', 'last_name', 'is_staff', 'is_superuser']
    list_filter = ['user_type', 'is_staff', 'is_superuser']
    search_fields = ['username', 'email', 'first_name', 'last_name']

    # Add our custom fields to the default fieldsets
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('Additional info', {'fields': ('user_type', 'phone', 'address')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('Additional info', {'fields': ('user_type', 'phone', 'address')}),
    )

@admin.register(Class)
class ClassAdmin(admin.ModelAdmin):
    list_display = ['name', 'level', 'promotion_rank', 'class_teacher', 'academic_year']
    list_filter = ['level', 'academic_year']

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name']
    search_fields = ['code', 'name']

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ['admission_number', 'user', 'student_class', 'guardian_name']
    list_filter = ['student_class']
    search_fields = ['admission_number', 'user__first_name', 'user__last_name']

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ['employee_id', 'user']
    search_fields = ['employee_id', 'user__first_name', 'user__last_name']

@admin.register(Term)
class TermAdmin(admin.ModelAdmin):
    list_display = ['term', 'academic_year', 'start_date', 'end_date', 'is_active']
    list_filter = ['academic_year', 'is_active']

@admin.register(Mark)
class MarkAdmin(admin.ModelAdmin):
    list_display = ['student', 'subject', 'term', 'total_marks', 'grade']
    list_filter = ['term', 'subject', 'grade']
    search_fields = ['student__admission_number', 'student__user__first_name']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['student', 'term', 'teacher', 'created_at']
    list_filter = ['term']
    search_fields = ['student__admission_number']

@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display = ['code', 'is_active']
    list_filter = ['is_active']

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'academic_year', 'class_assigned', 'status', 'average_score', 'override_status']
    list_filter = ['academic_year', 'status']
    search_fields = ['student__admission_number', 'student__user__first_name', 'student__user__last_name']