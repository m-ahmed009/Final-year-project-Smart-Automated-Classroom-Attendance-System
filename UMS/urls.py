from django.urls import path
from .views import home, login_view, admin_dashboard,Logout
from .controller.admin import users_views, university_views, campus_views,program_views,department_views,course_views,admin_faculty_views,departAssign_views,admin_student_views,semester_views,semCourse_views,Assigncourse_views,enrollment_views,Attendance_views
from .controller.faculty import faculty_views,settings_views
from .controller.student import student_views
from .import views
from django.conf import settings
from django.conf.urls.static import static



urlpatterns = [


    path('', views.home, name='home'),  # Home Page
    path('login/', login_view, name='login'),  # Login Page for users(Admin,Faculty,student)
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),  # Admin Dashboard
    path('logout/', Logout, name='logout'),  # Logout URL for users(Admin,Faculty,student)


    # password reset steps URLS
    path("password_reset/", views.request_password_reset, name="password_reset"),
    path("password_reset_done/", views.CustomPasswordResetDoneView.as_view(), name="password_reset_done"),
    path("reset/<uidb64>/<token>/", views.password_reset_confirm, name="password_reset_confirm"),
    path("reset_complete/", views.custom_password_reset_complete, name="password_reset_complete"),
   

#------------------------------------------------------------------
#           Admin side urls
#------------------------------------------------------------------


    # Users URLS
    path('users/', users_views.user_index, name='user_index'),
    path('register-user/', users_views.register_user, name='register_user'),
    path('user-approve/<int:user_id>/', users_views.approve_user, name='approve_user'),
    path('delete-user/<int:user_id>/', users_views.delete_user, name='delete_user'),

   # University URLs
    path('university/', university_views.university_index, name='university_index'),
    path('university/create/', university_views.university_create, name='university_create'),
    path('university/<int:pk>/', university_views.university_show, name='university_show'),
    path('university/<int:pk>/edit/', university_views.university_edit, name='university_edit'),
    path('university/<int:pk>/delete/', university_views.university_delete, name='university_delete'),



    # Campus URLs
    path('campus/', campus_views.campus_index, name='campus_index'),
    path('campus/create/', campus_views.campus_create, name='campus_create'),
    path('campus/<int:pk>/', campus_views.campus_show, name='campus_show'),
    path('campus/<int:pk>/edit/', campus_views.campus_edit, name='campus_edit'),
    path('campus/<int:pk>/delete/', campus_views.campus_delete, name='campus_delete'),


   # department urls
    path('department/', department_views.department_index, name='department_index'),
    path('department/create/', department_views.department_create, name='department_create'),
    path('department/<int:pk>/', department_views.department_show, name='department_show'),
    path('department/<int:pk>/edit/', department_views.department_edit, name='department_edit'),
    path('department/<int:pk>/delete/', department_views.department_delete, name='department_delete'),


    # program urls
    path('programs/', program_views.programs_index, name='programs_index'),
    path('programs/create/', program_views.program_create, name='program_create'),
    path('programs/<int:pk>/', program_views.programs_show, name='programs_show'),
    path('programs/<int:pk>/edit/', program_views.programs_edit, name='programs_edit'),
    path('programs/<int:pk>/delete/', program_views.programs_delete, name='programs_delete'),



    # courses urls
    path('course/', course_views.course_index, name='course_index'),
    path('course/create/', course_views.course_create, name='course_create'),
    path('course/<int:pk>/', course_views.course_show, name='course_show'),
    path('course/<int:pk>/edit/', course_views.course_edit, name='course_edit'),
    path('course/<int:pk>/delete/', course_views.course_delete, name='course_delete'),



    # faculty urls
    path('faculty/', admin_faculty_views.faculty_index, name='faculty_index'),
    path('faculty/create/', admin_faculty_views.faculty_create, name='faculty_create'),
    path('faculty/<int:pk>/', admin_faculty_views.faculty_show, name='faculty_show'),
    path('faculty/<int:pk>/edit/', admin_faculty_views.faculty_edit, name='faculty_edit'),
    path('faculty/<int:pk>/delete/', admin_faculty_views.faculty_delete, name='faculty_delete'),




    # departAssign urls
    path('departAssign/', departAssign_views.departAssign_index, name='departAssign_index'),
    path('departAssign/create/', departAssign_views.departAssign_create, name='departAssign_create'),
    path('departAssign/<int:pk>/', departAssign_views.departAssign_show, name='departAssign_show'),
    path('departAssign/<int:pk>/edit/', departAssign_views.departAssign_edit, name='departAssign_edit'),
    path('departAssign/<int:pk>/delete/', departAssign_views.departAssign_delete, name='departAssign_delete'),



    # Students urls
    path('Students/', admin_student_views.Students_index, name='Students_index'),
    path('Students/create/', admin_student_views.Students_create, name='Students_create'),
    path('Students/<int:pk>/', admin_student_views.Students_show, name='Students_show'),
    path('Students/<int:pk>/edit/', admin_student_views.Students_edit, name='Students_edit'),
    path('Students/<int:pk>/delete/', admin_student_views.Students_delete, name='Students_delete'),



    # semester urls
    path('semester/', semester_views.semester_index, name='semester_index'),
    path('semester/create/', semester_views.semester_create, name='semester_create'),
    path('semester/<int:pk>/', semester_views.semester_show, name='semester_show'),
    path('semester/<int:pk>/edit/', semester_views.semester_edit, name='semester_edit'),
    path('semester/<int:pk>/delete/', semester_views.semester_delete, name='semester_delete'),
    path('semester/<int:id>/toggle/', semester_views.semester_toggle, name='semester_toggle'),
    
    # semester course urls
    path('semesterCourse/', semCourse_views.semesterCourse_index, name='semesterCourse_index'),
    path('semesterCourse/create/', semCourse_views.semesterCourse_create, name='semesterCourse_create'),
    path('semesterCourse/<int:pk>/', semCourse_views.semesterCourse_show, name='semesterCourse_show'),
    path('semesterCourse/<int:pk>/edit/', semCourse_views.semesterCourse_edit, name='semesterCourse_edit'),
    path('semesterCourse/<int:pk>/delete/', semCourse_views.semesterCourse_delete, name='semesterCourse_delete'),   



    # Assigncourse urls
    path('Assigncourse/', Assigncourse_views.Assigncourse_index, name='Assigncourse_index'),
    path('Assigncourse/create/', Assigncourse_views.Assigncourse_create, name='Assigncourse_create'),
    path('Assigncourse/<int:pk>/', Assigncourse_views.Assigncourse_show, name='Assigncourse_show'),
    path('Assigncourse/<int:pk>/edit/', Assigncourse_views.Assigncourse_edit, name='Assigncourse_edit'),
    path('Assigncourse/<int:pk>/delete/', Assigncourse_views.Assigncourse_delete, name='Assigncourse_delete'), 


# enrollment urls
    path('enrollment/', enrollment_views.enrollment_index, name='enrollment_index'),
    path('enrollments/<int:sem_course_id>/<int:student_id>/', enrollment_views.enrollment_indexs, name='enrollment_indexs'),
    path('enrollments/<int:sem_course_id>/', enrollment_views.enrollment_indexs, name='enrollment_indexs'),
    path('enrollmentcard/', enrollment_views.enrollment_card, name='enrollment_card'),
    path('enrollment/create/', enrollment_views.enrollment_create, name='enrollment_create'),
    path('get_student_images/', enrollment_views.get_student_images, name='get_student_images'),    
    path('enrollment/<int:pk>/', enrollment_views.enrollment_show, name='enrollment_show'),
    path('enrollment/<int:pk>/edit/', enrollment_views.enrollment_edit, name='enrollment_edit'),
    path('enrollment/delete/<int:pk>/', enrollment_views.enrollment_delete, name='enrollment_delete'),
    path('enrollment/single_delete/<int:pk>/', enrollment_views.single_enrollment_delete, name='single_enrollment_delete'),


    # +------------------+
    ## Model Url
    path('initiate-training/', enrollment_views.initiate_training, name='initiate_training'),
    # +------------------+



    # Attendance urls
    path('attendances/', Attendance_views.attendance_index, name='attendance_index'),
    path('attendances/create/', Attendance_views.attendance_create, name='attendance_create'),
    path('attendances/<int:id>/', Attendance_views.attendance_show, name='attendance_show'),
    path('attendances/<int:pk>/edit/', Attendance_views.attendance_edit, name='attendance_edit'),
    path('attendances/delete/<int:pk>/', Attendance_views.attendance_delete, name='attendance_delete'),

#------------------------------------------------------------------
#           Student side urls
#------------------------------------------------------------------
    path('student/dashboard/', student_views.student_dashboard, name='student_dashboard'),
    path('student/courses/', student_views.student_courses_index, name='student_courses_index'),
    path('student/courses/<int:course_id>/', student_views.student_course_detail, name='student_course_detail'),

#------------------------------------------------------------------
#           Faculty side urls
#------------------------------------------------------------------
   
    path('faculty/dashboard/', faculty_views.faculty_dashboard, name='faculty_dashboard'),
    # Cources List
    path('courses/', faculty_views.faculty_cources_index, name='faculty_cources_index'),

    # Camera Attendance urls
    path('takeattendance/', faculty_views.camera_attendance, name='camera_attendance'),
    path('takeattendance/<int:sem_course_id>/<int:attendance_id>/', faculty_views.camera_attendance, name='camera_attendance'),
    path('takeattendance/save/<int:sem_course_id>/<int:attendance_id>/', faculty_views.save_camera_attendance, name='save_camera_attendance'),
    # path('get_active_camera/', faculty_views.get_active_camera, name='get_active_camera'),  
    path('stream-frame/', faculty_views.stream_frame, name='stream_frame'),
  

    # manual attendance urls.py
    path('attendance/', faculty_views.attendance_page, name='attendance_page'),
    path('attendance/<int:sem_course_id>/<int:attendance_id>/', faculty_views.attendance_page, name='attendance_page'),
    path('attendance/save/<int:sem_course_id>/<int:attendance_id>/', faculty_views.save_attendance, name='save_attendance'),


    #Attendance logs
    path('attendance-log/', faculty_views.attendance_log, name='attendance_log'),
    path('edit-attendance/<int:pk>/', faculty_views.edit_attendance, name='edit_attendance'),
    path('view-attendance/<int:pk>/', faculty_views.view_attendance, name='view_attendance'),
    path('delete-attendance/<int:pk>/', faculty_views.delete_attendance, name='delete_attendance'),  
    #Attendance Roaster
    path('faculty/attendance_roaster/<int:sem_course_id>/', faculty_views.attendance_roaster, name='attendance_roaster'),
    path('faculty/attendance/mark/<int:sem_course_id>/<int:attendance_id>/', faculty_views.mark_attendance_for_date, name='mark_attendance_for_date'),
    path('faculty/attendance/save/', faculty_views.save_attendance, name='save_attendance'),

    #Settings camera & Profile
    path('settings/', settings_views.settings_index, name='settings_index'),    
    path('camera-settings/', settings_views.camera_settings, name='camera_settings'),
    path('camera/<int:pk>/get/', settings_views.get_camera_data, name='get_camera_data'),
    path('camera/<int:pk>/update/', settings_views.update_camera, name='update_camera'),

    path('delete-camera/<int:pk>/', settings_views.delete_camera, name='delete_camera'),
    path('get_active_camera/', settings_views.get_active_camera, name='get_active_camera'),
    path('camera/<int:pk>/toggle/', settings_views.toggle_camera_status, name='toggle_camera_status'),
 
]+ static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
