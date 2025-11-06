from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    phone = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'users'

class Class(models.Model):
    name = models.CharField(max_length=50)
    level = models.CharField(max_length=20)
    class_teacher = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, 
                                      limit_choices_to={'user_type': 'teacher'})
    academic_year = models.CharField(max_length=9, default='2024/2025')
    
    def __str__(self):
        return self.name
    
    class Meta:
        db_table = 'classes'
        verbose_name_plural = 'Classes'

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    class Meta:
        db_table = 'subjects'

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=20, unique=True)
    student_class = models.ForeignKey(Class, on_delete=models.SET_NULL, null=True)
    date_of_birth = models.DateField()
    guardian_name = models.CharField(max_length=100)
    guardian_phone = models.CharField(max_length=15)
    
    def __str__(self):
        return f"{self.admission_number} - {self.user.get_full_name()}"
    
    class Meta:
        db_table = 'students'

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    employee_id = models.CharField(max_length=20, unique=True)
    subjects = models.ManyToManyField(Subject)
    classes = models.ManyToManyField(Class, related_name='teachers')
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    class Meta:
        db_table = 'teachers'

class Term(models.Model):
    TERM_CHOICES = (
        ('1', 'Term 1'),
        ('2', 'Term 2'),
        ('3', 'Term 3'),
    )
    term = models.CharField(max_length=1, choices=TERM_CHOICES)
    academic_year = models.CharField(max_length=9)
    start_date = models.DateField()
    end_date = models.DateField()
    is_active = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Term {self.term} - {self.academic_year}"
    
    class Meta:
        db_table = 'terms'
        unique_together = ['term', 'academic_year']

class Mark(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True)
    
    # Assessment components
    assignment_marks = models.DecimalField(max_digits=5, decimal_places=2, 
                                          validators=[MinValueValidator(0), MaxValueValidator(20)],
                                          default=0)
    midterm_marks = models.DecimalField(max_digits=5, decimal_places=2,
                                       validators=[MinValueValidator(0), MaxValueValidator(30)],
                                       default=0)
    exam_marks = models.DecimalField(max_digits=5, decimal_places=2,
                                    validators=[MinValueValidator(0), MaxValueValidator(50)],
                                    default=0)
    total_marks = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    grade = models.CharField(max_length=2, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        self.total_marks = self.assignment_marks + self.midterm_marks + self.exam_marks
        self.grade = self.calculate_grade()
        super().save(*args, **kwargs)
    
    def calculate_grade(self):
        total = float(self.total_marks)
        if total >= 90:
            return 'A+'
        elif total >= 80:
            return 'A'
        elif total >= 70:
            return 'B+'
        elif total >= 60:
            return 'B'
        elif total >= 50:
            return 'C'
        elif total >= 40:
            return 'D'
        else:
            return 'F'
    
    class Meta:
        db_table = 'marks'
        unique_together = ['student', 'subject', 'term', 'class_assigned']

class Comment(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    teacher = models.ForeignKey(Teacher, on_delete=models.SET_NULL, null=True, blank=True)
    class_teacher_comment = models.TextField()
    headteacher_comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'comments'
        unique_together = ['student', 'term']