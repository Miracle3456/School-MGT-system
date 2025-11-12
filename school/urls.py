from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    # Login selection page
    path('', views.login_selection, name='login_select'),

    # Separate login pages per user type
    path('login/admin/', views.login_view, {'user_type': 'admin'}, name='login_admin'),
    path('login/teacher/', views.login_view, {'user_type': 'teacher'}, name='login_teacher'),
    path('login/student/', views.login_view, {'user_type': 'student'}, name='login_student'),
    path('login/bursar/', views.login_view, {'user_type': 'bursar'}, name='login_bursar'),

    # Backwards-compatible generic login route (keeps old behavior)
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Admin (app) URLs — use a non-conflicting prefix to avoid Django admin site clash
    path('portal/admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('portal/admin/students/', views.manage_students, name='manage_students'),
    path('portal/admin/student/<int:student_id>/', views.admin_view_student, name='admin_view_student'),
    path('portal/admin/teachers/', views.manage_teachers, name='manage_teachers'),
    path('portal/search/students/', views.search_students, name='search_students'),
    
    # Fee Management URLs
    path('portal/admin/fees/', views.manage_fees, name='manage_fees'),
    path('portal/admin/fees/class/<int:class_id>/', views.class_fee_detail, name='class_fee_detail'),
    path('portal/admin/fees/class/<int:class_id>/unpaid/<int:term_id>/', views.unpaid_report, name='unpaid_report'),
    path('portal/admin/fees/class/<int:class_id>/unpaid/<int:term_id>/pdf/', views.unpaid_report_pdf, name='unpaid_report_pdf'),
    path('portal/bursar/dashboard/', views.bursar_dashboard, name='bursar_dashboard'),
    path('portal/bursar/payments/', views.manage_payments, name='manage_payments'),
    path('portal/bursar/unpaid/class/<int:class_id>/term/<int:term_id>/', views.unpaid_report, name='bursar_unpaid_report'),
    path('portal/bursar/unpaid/class/<int:class_id>/term/<int:term_id>/pdf/', views.unpaid_report_pdf, name='bursar_unpaid_report_pdf'),
    path('portal/bursar/student/<int:student_id>/fees/', views.student_fee_detail, name='student_fee_detail'),
    path('portal/bursar/payment/receipt/<int:payment_id>/', views.generate_fee_receipt, name='generate_fee_receipt'),
    # Class PDF report for teachers/admins
    path('portal/class_report/<int:class_id>/<int:term_id>/', views.class_pdf_report, name='class_pdf_report'),
    path('portal/class_reports_zip/<int:class_id>/<int:term_id>/', views.batch_student_reports_zip, name='batch_student_reports_zip'),

    # Teacher URLs
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/marks/', views.enter_marks, name='enter_marks'),
    path('teacher/comments/', views.add_comments, name='add_comments'),

    # Student URLs
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/report/<int:term_id>/', views.view_report, name='view_report'),
    path('student/fees/', views.student_my_fees, name='student_my_fees'),
    path('report/pdf/<int:student_id>/<int:term_id>/', views.generate_pdf_report, name='generate_pdf_report'),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
