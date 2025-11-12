from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal
from django.utils import timezone

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrator'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
        ('bursar', 'Bursar'),
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

class ClassFee(models.Model):
    class_assigned = models.ForeignKey(Class, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField()
    fee_type = models.CharField(max_length=50, choices=[
        ('tuition', 'Tuition Fee'),
        ('exam', 'Examination Fee'),
        ('lab', 'Laboratory Fee'),
        ('other', 'Other Charges')
    ])
    description = models.TextField(blank=True)
    
    class Meta:
        db_table = 'class_fees'
        unique_together = ['class_assigned', 'term', 'fee_type']
        
    def __str__(self):
        return f"{self.class_assigned} - {self.term} - {self.get_fee_type_display()} ({self.amount} shs)"
        
class FeePayment(models.Model):
    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('partial', 'Partially Paid'),
        ('paid', 'Fully Paid'),
        ('overdue', 'Overdue')
    )
    PAYMENT_METHOD_CHOICES = (
        ('cash', 'Cash'),
        ('bank', 'Bank Transfer'),
        ('mtn', 'MTN Mobile Money'),
        ('airtel', 'Airtel Mobile Money'),
        ('momo_pay', 'MoMo Pay'),
    )
    
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    term = models.ForeignKey(Term, on_delete=models.CASCADE)
    payment_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_status = models.CharField(max_length=10, choices=PAYMENT_STATUS_CHOICES, default='pending')
    receipt_no = models.CharField(max_length=20, unique=True)
    transaction_reference = models.CharField(max_length=50, blank=True)
    processed_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to=models.Q(user_type__in=['bursar', 'admin'])
    )
    notes = models.TextField(blank=True)
    
    class Meta:
        db_table = 'fee_payments'
        
    def __str__(self):
        return f"Receipt #{self.receipt_no} - {self.student}"
        
    def save(self, *args, **kwargs):
        # Auto-generate receipt number if not provided
        if not self.receipt_no:
            last_payment = FeePayment.objects.order_by('-id').first()
            next_id = (last_payment.id + 1) if last_payment else 1
            self.receipt_no = f"RCP{next_id:06d}"
            
        # Calculate payment status based on total fees vs amount paid
        total_fees = ClassFee.objects.filter(
            class_assigned=self.student.student_class,
            term=self.term
        ).aggregate(total=models.Sum('amount'))['total']
        total_fees = total_fees if total_fees is not None else Decimal('0')
        
        total_paid = FeePayment.objects.filter(
            student=self.student,
            term=self.term
        ).aggregate(paid=models.Sum('amount_paid'))['paid']
        total_paid = total_paid if total_paid is not None else Decimal('0')

        # Ensure current amount is Decimal before arithmetic
        current_payment = self.amount_paid
        if isinstance(current_payment, str):
            try:
                current_payment = Decimal(current_payment)
            except Exception:
                current_payment = Decimal('0')
        total_paid = Decimal(total_paid) + Decimal(current_payment)
        
        if total_paid >= total_fees:
            self.payment_status = 'paid'
        elif total_paid > 0:
            self.payment_status = 'partial'
        else:
            # Determine overdue using the earliest due date among class fees for this term
            earliest_due = ClassFee.objects.filter(
                class_assigned=self.student.student_class,
                term=self.term
            ).order_by('due_date').values_list('due_date', flat=True).first()
            if earliest_due and earliest_due < timezone.now().date():
                self.payment_status = 'overdue'
            else:
                self.payment_status = 'pending'
            
        super().save(*args, **kwargs)