
import zipfile
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db.models import Avg, Sum, Count, Q
from django.utils import timezone
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from io import BytesIO
import csv
from .models import User, Student, Teacher, Class, Subject, Term, Mark, Comment, ClassFee, FeePayment


@login_required
def batch_student_reports_zip(request, class_id, term_id):
    class_obj = get_object_or_404(Class, id=class_id)
    term = get_object_or_404(Term, id=term_id)
    students = Student.objects.filter(student_class=class_obj).select_related('user')
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, 'w') as zipf:
        for student in students:
            marks = Mark.objects.filter(student=student, term=term).select_related('subject')
            comment = Comment.objects.filter(student=student, term=term).first()
            # Generate PDF for this student (reuse code from generate_pdf_report)
            pdf_buffer = BytesIO()
            doc = SimpleDocTemplate(pdf_buffer, pagesize=A4)
            elements = []
            styles = getSampleStyleSheet()
            title = Paragraph(f"<b>STUDENT REPORT CARD</b>", styles['Title'])
            elements.append(title)
            elements.append(Spacer(1, 12))
            info = f"""
            <b>Name:</b> {student.user.get_full_name()}<br/>
            <b>Admission No:</b> {student.admission_number}<br/>
            <b>Class:</b> {student.student_class.name}<br/>
            <b>Term:</b> {term}<br/>
            """
            elements.append(Paragraph(info, styles['Normal']))
            elements.append(Spacer(1, 20))
            data = [['Subject', 'Assignment', 'Midterm', 'Exam', 'Total', 'Grade']]
            for mark in marks:
                data.append([
                    mark.subject.name,
                    str(mark.assignment_marks),
                    str(mark.midterm_marks),
                    str(mark.exam_marks),
                    str(mark.total_marks),
                    mark.grade
                ])
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)
            elements.append(Spacer(1, 20))
            if comment:
                comments_text = f"""
                <b>Class Teacher's Comment:</b><br/>
                {comment.class_teacher_comment}<br/><br/>
                <b>Head Teacher's Comment:</b><br/>
                {comment.headteacher_comment or 'N/A'}
                """
                elements.append(Paragraph(comments_text, styles['Normal']))
            doc.build(elements)
            pdf_buffer.seek(0)
            filename = f"{student.admission_number}_{student.user.get_full_name().replace(' ', '_')}_{term.term}.pdf"
            zipf.writestr(filename, pdf_buffer.read())
    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type='application/zip')
    response['Content-Disposition'] = f'attachment; filename="class_reports_{class_obj.name}_{term.term}.zip"'
    return response

@login_required
def class_pdf_report(request, class_id, term_id):
    class_obj = get_object_or_404(Class, id=class_id)
    term = get_object_or_404(Term, id=term_id)
    students = Student.objects.filter(student_class=class_obj).select_related('user')
    marks = Mark.objects.filter(class_assigned=class_obj, term=term).select_related('student', 'subject')

    # Build a mapping: student_id -> {subject: mark}
    student_marks = {}
    for mark in marks:
        student_marks.setdefault(mark.student_id, {})[mark.subject.name] = mark

    subjects = list(Subject.objects.all())

    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    title = Paragraph(f"<b>CLASS REPORT: {class_obj.name} - {term}</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Table header
    header = ['Student'] + [s.name for s in subjects]
    data = [header]
    for student in students:
        row = [student.user.get_full_name()]
        for subject in subjects:
            mark = student_marks.get(student.id, {}).get(subject.name)
            row.append(str(mark.total_marks) if mark else '-')
        data.append(row)

    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="class_report_{class_obj.name}_{term.term}.pdf"'
    return response

# Helper functions for user type checking
def is_admin(user):
    # Allow explicit admin user_type or Django superuser/staff to be treated as admin
    return getattr(user, 'user_type', None) == 'admin' or user.is_superuser or user.is_staff

def is_teacher(user):
    return user.user_type == 'teacher'

def is_student(user):
    return user.user_type == 'student'

def is_bursar(user):
    return user.user_type == 'bursar'

@login_required
@user_passes_test(is_admin)
def admin_view_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    marks = Mark.objects.filter(student=student).select_related('subject', 'term').order_by('term__academic_year', 'term__term', 'subject__name')
    comments = Comment.objects.filter(student=student).select_related('term', 'teacher').order_by('term__academic_year', 'term__term')
    context = {
        'student': student,
        'marks': marks,
        'comments': comments,
    }
    return render(request, 'admin/student_detail.html', context)

# Login View
def login_view(request, user_type=None):
    """Generic login view that can be used for admin/teacher/student logins.

    If user_type is provided (one of 'admin','teacher','student'), the view
    will render the corresponding template and enforce that the authenticated
    user has that user_type. If user_type is None it will behave as the
    selection page renderer (handled by login_selection).
    """
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user is not None:
                # Allow superusers to access any login type
                if user.is_superuser:
                    login(request, user)
                    return redirect('admin_dashboard')
                
                # For regular users, check if they're using the correct login page
                if user_type and user.user_type != user_type:
                    messages.error(request, f'Please use the {user.user_type} login page.')
                    # Redirect to the correctly named login URL (login_admin, login_teacher, login_student, login_bursar)
                    return redirect(f'login_{user.user_type}')
            
                login(request, user)
                # Redirect to appropriate dashboard
                if user.user_type == 'admin':
                    return redirect('admin_dashboard')
                elif user.user_type == 'teacher':
                    return redirect('teacher_dashboard')
                elif user.user_type == 'bursar':
                    return redirect('bursar_dashboard')
                else:
                    return redirect('student_dashboard')
        else:
            messages.error(request, 'Invalid username or password')

    # Render the template for the requested user_type (or a default login)
    template_name = 'accounts/login.html'
    if user_type in ('admin', 'teacher', 'student', 'bursar'):
        template_name = f'accounts/{user_type}_login.html'

    return render(request, template_name, {'user_type': user_type})


def login_selection(request):
    """Render a simple page that links to the three user-type-specific login pages.

    If the user is already authenticated, redirect them straight to their
    dashboard to avoid showing the selection page.
    """
    if request.user.is_authenticated:
        # Redirect logged in users to their dashboard
        ut = getattr(request.user, 'user_type', None)
        if ut == 'admin':
            return redirect('admin_dashboard')
        if ut == 'teacher':
            return redirect('teacher_dashboard')
        if ut == 'student':
            return redirect('student_dashboard')
        if ut == 'bursar':
            return redirect('bursar_dashboard')
        # fallback to admin dashboard for superuser/staff without user_type
        if request.user.is_staff or request.user.is_superuser:
            return redirect('admin_dashboard')

    return render(request, 'accounts/login_select.html')

def logout_view(request):
    logout(request)
    return redirect('login')

# Admin Views
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Get active term for current statistics
    active_term = Term.objects.filter(is_active=True).first()
    
    # Basic statistics
    student_count = Student.objects.count()
    teacher_count = Teacher.objects.count()
    class_count = Class.objects.count()
    subject_count = Subject.objects.count()
    
    # Performance statistics for active term
    if active_term:
        class_averages = Mark.objects.filter(term=active_term).values(
            'class_assigned__name'
        ).annotate(
            average_score=Avg('total_marks'),
            student_count=Count('student', distinct=True)
        )
        
        subject_averages = Mark.objects.filter(term=active_term).values(
            'subject__name'
        ).annotate(
            average_score=Avg('total_marks'),
            student_count=Count('student', distinct=True)
        )
        
        top_performers = Student.objects.filter(
            mark__term=active_term
        ).annotate(
            average_score=Avg('mark__total_marks')
        ).order_by('-average_score')[:5]
    else:
        class_averages = []
        subject_averages = []
        top_performers = []
    
    classes = Class.objects.all()
    terms = Term.objects.all()
    subjects = Subject.objects.all()
    context = {
        'total_students': student_count,
        'total_teachers': teacher_count,
        'total_classes': class_count,
        'total_subjects': subject_count,
        'active_term': active_term,
        'class_averages': class_averages,
        'subject_averages': subject_averages,
        'top_performers': top_performers,
        'classes': classes,
        'terms': terms,
        'subjects': subjects,
    }
    return render(request, 'admin/dashboard.html', context)

@login_required
@user_passes_test(is_admin)
def manage_students(request):
    students = Student.objects.select_related('user', 'student_class').all()
    classes = Class.objects.all()
    
    if request.method == 'POST':
        # Handle student creation/update
        action = request.POST.get('action')
        if action == 'add':
            # Create user first
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                user_type='student'
            )
            # Auto-generate admission number if not provided
            admission_number = request.POST.get('admission_number')
            if not admission_number:
                last_student = Student.objects.order_by('-id').first()
                next_id = (last_student.id + 1) if last_student else 1
                admission_number = f"S{next_id:04d}"
            Student.objects.create(
                user=user,
                admission_number=admission_number,
                student_class_id=request.POST.get('class_id'),
                date_of_birth=request.POST.get('date_of_birth'),
                guardian_name=request.POST.get('guardian_name'),
                guardian_phone=request.POST.get('guardian_phone')
            )
            messages.success(request, f'Student added successfully. Admission Number: {admission_number}')
        
        return redirect('manage_students')
    
    context = {'students': students, 'classes': classes}
    return render(request, 'admin/students.html', context)

@login_required
@user_passes_test(is_admin)
def manage_teachers(request):
    teachers = Teacher.objects.select_related('user').prefetch_related('subjects', 'classes').all()
    subjects = Subject.objects.all()
    classes = Class.objects.all()
    
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'add':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            if not first_name or not last_name:
                messages.error(request, 'First name and last name are required.')
                return redirect('manage_teachers')
            user = User.objects.create_user(
                username=request.POST.get('username'),
                email=request.POST.get('email'),
                password=request.POST.get('password'),
                first_name=first_name,
                last_name=last_name,
                user_type='teacher'
            )
            # Auto-generate employee ID if not provided
            employee_id = request.POST.get('employee_id')
            if not employee_id:
                last_teacher = Teacher.objects.order_by('-id').first()
                next_id = (last_teacher.id + 1) if last_teacher else 1
                employee_id = f"T{next_id:04d}"
            teacher = Teacher.objects.create(
                user=user,
                employee_id=employee_id
            )
            # Add subjects and classes
            subject_ids = request.POST.getlist('subjects')
            class_ids = request.POST.getlist('classes')
            teacher.subjects.set(subject_ids)
            teacher.classes.set(class_ids)
            messages.success(request, f'Teacher added successfully. Employee ID: {employee_id}')
        
        return redirect('manage_teachers')
    
    context = {'teachers': teachers, 'subjects': subjects, 'classes': classes}
    return render(request, 'admin/teachers.html', context)

# Teacher Views
@login_required
@user_passes_test(is_teacher)
def teacher_dashboard(request):
    teacher = Teacher.objects.get(user=request.user)
    active_term = Term.objects.filter(is_active=True).first()
    
    # Get teacher's classes and subjects
    teacher_classes = teacher.classes.all()
    teacher_subjects = teacher.subjects.all()
    
    # Get performance statistics for each class and subject taught by this teacher
    class_statistics = []
    if active_term:
        for class_obj in teacher_classes:
            class_stats = Mark.objects.filter(
                teacher=teacher,
                class_assigned=class_obj,
                term=active_term
            ).aggregate(
                avg_score=Avg('total_marks'),
                total_students=Count('student', distinct=True),
                assignments_pending=Count('id', filter=Q(assignment_marks=0)),
                exams_pending=Count('id', filter=Q(exam_marks=0))
            )
            class_stats['class'] = class_obj
            class_statistics.append(class_stats)
            
        # Get subject-wise performance
        subject_statistics = Mark.objects.filter(
            teacher=teacher,
            term=active_term
        ).values(
            'subject__name'
        ).annotate(
            avg_score=Avg('total_marks'),
            total_students=Count('student', distinct=True),
            assignments_complete=Count('id', filter=~Q(assignment_marks=0)),
            exams_complete=Count('id', filter=~Q(exam_marks=0))
        )
        
        # Recent activities (marks entered in last 7 days)
        recent_activities = Mark.objects.filter(
            teacher=teacher,
            term=active_term,
            updated_at__gte=timezone.now() - timezone.timedelta(days=7)
        ).select_related('student', 'subject').order_by('-updated_at')[:10]
    else:
        subject_statistics = []
        recent_activities = []
    
    terms = Term.objects.all()
    context = {
        'teacher': teacher,
        'classes': teacher_classes,
        'subjects': teacher_subjects,
        'terms': terms,
        'active_term': active_term,
        'class_statistics': class_statistics,
        'subject_statistics': subject_statistics,
        'recent_activities': recent_activities,
    }
    return render(request, 'teacher/dashboard.html', context)

@login_required
@user_passes_test(is_teacher)
def enter_marks(request):
    teacher = Teacher.objects.get(user=request.user)
    classes = teacher.classes.all()
    subjects = teacher.subjects.all()
    terms = Term.objects.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        subject_id = request.POST.get('subject_id')
        term_id = request.POST.get('term_id')
        class_id = request.GET.get('class_id') or request.POST.get('class_id')
        if not class_id:
            messages.error(request, 'Class must be selected before entering marks.')
            return redirect('enter_marks')
        mark, created = Mark.objects.get_or_create(
            student_id=student_id,
            subject_id=subject_id,
            term_id=term_id,
            class_assigned_id=class_id,
            defaults={'teacher': teacher}
        )
        mark.assignment_marks = request.POST.get('assignment_marks', 0)
        mark.midterm_marks = request.POST.get('midterm_marks', 0)
        mark.exam_marks = request.POST.get('exam_marks', 0)
        mark.save()
        messages.success(request, 'Marks saved successfully')
        return redirect(f'{request.path}?class_id={class_id}')
    
    # Get students for selected class
    selected_class_id = request.GET.get('class_id')
    students = Student.objects.filter(student_class_id=selected_class_id) if selected_class_id else []
    
    context = {
        'classes': classes,
        'subjects': subjects,
        'terms': terms,
        'students': students
    }
    return render(request, 'teacher/enter_marks.html', context)

@login_required
@user_passes_test(is_teacher)
def add_comments(request):
    teacher = Teacher.objects.get(user=request.user)
    classes = teacher.classes.all()
    terms = Term.objects.all()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        term_id = request.POST.get('term_id')
        comment_text = request.POST.get('comment')
        
        comment, created = Comment.objects.get_or_create(
            student_id=student_id,
            term_id=term_id,
            defaults={'teacher': teacher}
        )
        
        comment.class_teacher_comment = comment_text
        comment.save()
        
        messages.success(request, 'Comment added successfully')
        return redirect('add_comments')
    
    selected_class_id = request.GET.get('class_id')
    students = Student.objects.filter(student_class_id=selected_class_id) if selected_class_id else []
    
    context = {
        'classes': classes,
        'terms': terms,
        'students': students
    }
    return render(request, 'teacher/comments.html', context)

# Student Views
@login_required
@user_passes_test(is_student)
def student_dashboard(request):
    student = Student.objects.get(user=request.user)
    active_term = Term.objects.filter(is_active=True).first()
    
    # Get student's current marks and performance
    current_marks = Mark.objects.filter(
        student=student,
        term=active_term
    ).select_related('subject', 'teacher') if active_term else []
    
    # Calculate overall performance
    if active_term:
        # Use only model fields for aggregation
        overall_stats = current_marks.aggregate(
            total_marks=Sum('total_marks'),
            average_score=Avg('assignment_marks')  # placeholder, will fix below
        )
        # Fix average_score to be the average of total_marks
        # (Django can't aggregate on an aggregate, so do it in Python)
        total_marks_list = list(current_marks.values_list('total_marks', flat=True))
        if total_marks_list:
            overall_stats['average_score'] = sum(total_marks_list) / len(total_marks_list)
        else:
            overall_stats['average_score'] = 0

        # Get subject-wise performance
        subject_performance = current_marks.values(
            'subject__name'
        ).annotate(
            marks=Sum('total_marks'),
            assignments_done=Count('assignment_marks', filter=~Q(assignment_marks=0)),
            total_assignments=Count('assignment_marks'),
            exams_done=Count('exam_marks', filter=~Q(exam_marks=0)),
            total_exams=Count('exam_marks')
        )

        # Get class rank (average of total_marks per student)
        class_ranks = Mark.objects.filter(
            term=active_term,
            class_assigned=student.student_class
        ).values('student_id').annotate(
            avg_score=Avg('total_marks')
        ).order_by('-avg_score')

        student_rank = next(
            (i for i, x in enumerate(class_ranks, 1) if x['student_id'] == student.id),
            None
        )

        # Get upcoming or pending assignments
        pending_work = current_marks.filter(
            Q(assignment_marks=0) | Q(exam_marks=0)
        ).values('subject__name', 'assignment_marks', 'exam_marks')
    else:
        overall_stats = None
        subject_performance = []
        student_rank = None
        pending_work = []
    
    context = {
        'student': student,
        'active_term': active_term,
        'current_marks': current_marks,
        'overall_stats': overall_stats,
        'subject_performance': subject_performance,
        'class_rank': student_rank,
        'total_students': student.student_class.student_set.count(),
        'pending_work': pending_work
    }
    return render(request, 'student/dashboard.html', context)

@login_required
@user_passes_test(is_student)
def view_report(request, term_id):
    student = Student.objects.get(user=request.user)
    term = get_object_or_404(Term, id=term_id)
    
    marks = Mark.objects.filter(
        student=student,
        term=term
    ).select_related('subject')
    
    comment = Comment.objects.filter(student=student, term=term).first()
    
    # Calculate statistics
    total_marks = marks.aggregate(Sum('total_marks'))['total_marks__sum'] or 0
    average = marks.aggregate(Avg('total_marks'))['total_marks__avg'] or 0
    
    context = {
        'student': student,
        'term': term,
        'marks': marks,
        'comment': comment,
        'total_marks': total_marks,
        'average': round(average, 2)
    }
    return render(request, 'student/report.html', context)

@login_required
def generate_pdf_report(request, student_id, term_id):
    student = get_object_or_404(Student, id=student_id)
    term = get_object_or_404(Term, id=term_id)
    marks = Mark.objects.filter(student=student, term=term).select_related('subject')
    comment = Comment.objects.filter(student=student, term=term).first()
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # Title
    title = Paragraph(f"<b>STUDENT REPORT CARD</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Student info
    info = f"""
    <b>Name:</b> {student.user.get_full_name()}<br/>
    <b>Admission No:</b> {student.admission_number}<br/>
    <b>Class:</b> {student.student_class.name}<br/>
    <b>Term:</b> {term}<br/>
    """
    elements.append(Paragraph(info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Marks table
    data = [['Subject', 'Assignment', 'Midterm', 'Exam', 'Total', 'Grade']]
    for mark in marks:
        data.append([
            mark.subject.name,
            str(mark.assignment_marks),
            str(mark.midterm_marks),
            str(mark.exam_marks),
            str(mark.total_marks),
            mark.grade
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    # Comments
    if comment:
        comments_text = f"""
        <b>Class Teacher's Comment:</b><br/>
        {comment.class_teacher_comment}<br/><br/>
        <b>Head Teacher's Comment:</b><br/>
        {comment.headteacher_comment or 'N/A'}
        """
        elements.append(Paragraph(comments_text, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="report_{student.admission_number}_{term.term}.pdf"'
    return response

# Fee Management Views
@login_required
@user_passes_test(is_admin)
def manage_fees(request):
    classes = Class.objects.all()
    active_term = Term.objects.filter(is_active=True).first()
    terms = Term.objects.all()
    
    if request.method == 'POST':
        class_id = request.POST.get('class_id')
        term_id = request.POST.get('term_id')
        fee_type = request.POST.get('fee_type')
        amount = request.POST.get('amount')
        due_date = request.POST.get('due_date')
        description = request.POST.get('description')
        
        class_fee = ClassFee.objects.create(
            class_assigned_id=class_id,
            term_id=term_id,
            fee_type=fee_type,
            amount=amount,
            due_date=due_date,
            description=description
        )
        messages.success(request, 'Fee structure added successfully')
        return redirect('class_fee_detail', class_id=class_id)
    
    context = {
        'classes': classes,
        'active_term': active_term,
        'terms': terms
    }
    return render(request, 'admin/manage_fees.html', context)

@login_required
@user_passes_test(is_admin)
def class_fee_detail(request, class_id):
    class_obj = get_object_or_404(Class, id=class_id)
    active_term = Term.objects.filter(is_active=True).first()
    
    fees = ClassFee.objects.filter(
        class_assigned=class_obj,
        term=active_term
    ) if active_term else []
    
    students = Student.objects.filter(student_class=class_obj)
    
    # Calculate payment statistics
    payment_stats = {}
    for student in students:
        total_fees = sum(fee.amount for fee in fees)
        payments = FeePayment.objects.filter(student=student, term=active_term)
        total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        balance = total_fees - total_paid
        payment_stats[student.id] = {
            'total_fees': total_fees,
            'total_paid': total_paid,
            'balance': balance,
            'status': 'paid' if balance <= 0 else 'partial' if total_paid > 0 else 'pending'
        }
    
    context = {
        'class': class_obj,
        'term': active_term,
        'fees': fees,
        'students': students,
        'payment_stats': payment_stats
    }
    return render(request, 'admin/class_fee_detail.html', context)

@login_required
@user_passes_test(is_bursar)
def bursar_dashboard(request):
    active_term = Term.objects.filter(is_active=True).first()
    
    if active_term:
        # Today's collections
        today = timezone.now().date()
        today_payments = FeePayment.objects.filter(
            payment_date__date=today,
            term=active_term
        )
        today_total = today_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Week's collections
        week_start = today - timezone.timedelta(days=today.weekday())
        week_payments = FeePayment.objects.filter(
            payment_date__date__gte=week_start,
            term=active_term
        )
        week_total = week_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        
        # Term statistics
        term_fees = ClassFee.objects.filter(term=active_term)
        term_payments = FeePayment.objects.filter(term=active_term)
        
        total_expected = term_fees.aggregate(total=Sum('amount'))['total'] or 0
        total_collected = term_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        collection_rate = (total_collected / total_expected * 100) if total_expected > 0 else 0
        
        # Payment method distribution
        payment_methods = term_payments.values('payment_method').annotate(
            total=Sum('amount_paid'),
            count=Count('id')
        )
        
        # Class-wise collection status
        class_stats = []
        for class_obj in Class.objects.all():
            class_fees = term_fees.filter(class_assigned=class_obj)
            class_expected = class_fees.aggregate(total=Sum('amount'))['total'] or 0
            class_payments = term_payments.filter(student__student_class=class_obj)
            class_collected = class_payments.aggregate(total=Sum('amount_paid'))['total'] or 0
            class_stats.append({
                'class': class_obj,
                'expected': class_expected,
                'collected': class_collected,
                'rate': (class_collected / class_expected * 100) if class_expected > 0 else 0
            })
    else:
        today_total = week_total = total_expected = total_collected = collection_rate = 0
        payment_methods = []
        class_stats = []
    
    context = {
        'active_term': active_term,
        'today_total': today_total,
        'week_total': week_total,
        'total_expected': total_expected,
        'total_collected': total_collected,
        'collection_rate': round(collection_rate, 2),
        'payment_methods': payment_methods,
        'class_stats': class_stats,
        'recent_payments': FeePayment.objects.select_related('student', 'term').order_by('-payment_date')[:10]
    }
    return render(request, 'bursar/dashboard.html', context)

@login_required
@user_passes_test(is_bursar)
def manage_payments(request):
    active_term = Term.objects.filter(is_active=True).first()
    
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
        payment_method = request.POST.get('payment_method')
        transaction_reference = request.POST.get('transaction_reference')
        notes = request.POST.get('notes')
        
        payment = FeePayment.objects.create(
            student_id=student_id,
            term=active_term,
            amount_paid=amount,
            payment_method=payment_method,
            transaction_reference=transaction_reference,
            processed_by=request.user,
            notes=notes
        )
        messages.success(request, f'Payment recorded successfully. Receipt No: {payment.receipt_no}')
        return redirect('generate_fee_receipt', payment_id=payment.id)
    
    # Get all students with their fee status
    students = Student.objects.all()
    fee_status = {}
    
    if active_term:
        for student in students:
            total_fees = ClassFee.objects.filter(
                class_assigned=student.student_class,
                term=active_term
            ).aggregate(total=Sum('amount'))['total'] or 0
            
            total_paid = FeePayment.objects.filter(
                student=student,
                term=active_term
            ).aggregate(total=Sum('amount_paid'))['total'] or 0
            
            fee_status[student.id] = {
                'total_fees': total_fees,
                'total_paid': total_paid,
                'balance': total_fees - total_paid
            }
    
    context = {
        'students': students,
        'fee_status': fee_status,
        'active_term': active_term,
        'payment_methods': FeePayment.PAYMENT_METHOD_CHOICES
    }
    return render(request, 'bursar/manage_payments.html', context)

@login_required
def student_fee_detail(request, student_id):
    # Allow bursar/admin to view any student, but allow a student to view their own fees.
    student = get_object_or_404(Student, id=student_id)
    # Permission check
    if not (is_bursar(request.user) or is_admin(request.user) or (is_student(request.user) and getattr(request.user, 'student', None) and request.user.student.id == student_id)):
        messages.error(request, 'You do not have permission to view this student\'s fees.')
        return redirect('login')

    terms = Term.objects.all()
    term_id = request.GET.get('term_id')
    term = get_object_or_404(Term, id=term_id) if term_id else Term.objects.filter(is_active=True).first()
    
    if term:
        fees = ClassFee.objects.filter(
            class_assigned=student.student_class,
            term=term
        )
        payments = FeePayment.objects.filter(
            student=student,
            term=term
        ).order_by('-payment_date')
        
        total_fees = fees.aggregate(total=Sum('amount'))['total'] or 0
        total_paid = payments.aggregate(total=Sum('amount_paid'))['total'] or 0
        balance = total_fees - total_paid
    else:
        fees = payments = []
        total_fees = total_paid = balance = 0
    
    context = {
        'student': student,
        'terms': terms,
        'current_term': term,
        'fees': fees,
        'payments': payments,
        'total_fees': total_fees,
        'total_paid': total_paid,
        'balance': balance
    }
    return render(request, 'bursar/student_fee_detail.html', context)

@login_required
@user_passes_test(lambda u: is_bursar(u) or is_admin(u))
def generate_fee_receipt(request, payment_id):
    payment = get_object_or_404(FeePayment, id=payment_id)
    
    # Create PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()
    
    # School Header
    title = Paragraph("<b>SCHOOL FEE RECEIPT</b>", styles['Title'])
    elements.append(title)
    elements.append(Spacer(1, 12))
    
    # Receipt Details
    receipt_info = f"""
    <b>Receipt No:</b> {payment.receipt_no}<br/>
    <b>Date:</b> {payment.payment_date.strftime('%d/%m/%Y %I:%M %p')}<br/>
    <b>Payment Method:</b> {payment.get_payment_method_display()}<br/>
    <b>Transaction Ref:</b> {payment.transaction_reference or 'N/A'}<br/>
    """
    elements.append(Paragraph(receipt_info, styles['Normal']))
    elements.append(Spacer(1, 12))
    
    # Student Details
    student_info = f"""
    <b>Student Name:</b> {payment.student.user.get_full_name()}<br/>
    <b>Admission No:</b> {payment.student.admission_number}<br/>
    <b>Class:</b> {payment.student.student_class.name}<br/>
    <b>Term:</b> {payment.term}<br/>
    """
    elements.append(Paragraph(student_info, styles['Normal']))
    elements.append(Spacer(1, 20))
    
    # Payment Details Table
    data = [
        ['Description', 'Amount'],
        ['Term Fees Payment', f'${payment.amount_paid:,.2f}']
    ]
    
    # Get current fee status
    total_fees = ClassFee.objects.filter(
        class_assigned=payment.student.student_class,
        term=payment.term
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_paid = FeePayment.objects.filter(
        student=payment.student,
        term=payment.term
    ).aggregate(total=Sum('amount_paid'))['total'] or 0
    
    balance = total_fees - total_paid
    
    data.extend([
        ['Total Term Fees', f'${total_fees:,.2f}'],
        ['Total Paid to Date', f'${total_paid:,.2f}'],
        ['Balance', f'${balance:,.2f}']
    ])
    
    table = Table(data, colWidths=['*', 100])
    table.setStyle(TableStyle([
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))
    
    if payment.notes:
        elements.append(Paragraph(f"<b>Notes:</b> {payment.notes}", styles['Normal']))
        elements.append(Spacer(1, 12))
    
    # Footer
    footer = f"""
    <b>Processed By:</b> {payment.processed_by.get_full_name()}<br/>
    This is a computer generated receipt
    """
    elements.append(Paragraph(footer, styles['Normal']))
    
    doc.build(elements)
    buffer.seek(0)
    
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="receipt_{payment.receipt_no}.pdf"'
    return response


@login_required
@user_passes_test(lambda u: is_bursar(u) or is_admin(u))
def unpaid_report(request, class_id, term_id):
    """Generate a CSV report of students in `class_id` for `term_id` who have outstanding balances."""
    class_obj = get_object_or_404(Class, id=class_id)
    term = get_object_or_404(Term, id=term_id)

    # Get fee items for the class & term
    fee_items = ClassFee.objects.filter(class_assigned=class_obj, term=term)
    total_expected = fee_items.aggregate(total=Sum('amount'))['total'] or 0

    students = Student.objects.filter(student_class=class_obj).select_related('user')

    rows = []
    for s in students:
        total_paid = FeePayment.objects.filter(student=s, term=term).aggregate(total=Sum('amount_paid'))['total'] or 0
        balance = total_expected - total_paid
        if balance > 0:
            rows.append({
                'admission': s.admission_number,
                'name': s.user.get_full_name(),
                'class': class_obj.name,
                'term': str(term),
                'expected': f"{total_expected:,.2f}",
                'paid': f"{total_paid:,.2f}",
                'balance': f"{balance:,.2f}"
            })

    # Build CSV response
    filename = f"unpaid_report_{class_obj.name}_{term.term}.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Admission', 'Student Name', 'Class', 'Term', 'Expected', 'Paid', 'Balance'])
    for r in rows:
        writer.writerow([r['admission'], r['name'], r['class'], r['term'], r['expected'], r['paid'], r['balance']])

    return response