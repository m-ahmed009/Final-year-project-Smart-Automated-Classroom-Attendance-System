from django.shortcuts import render
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ...models import Student,Enrollment,CourseAssign,StudentAttendance,Course




# Student Dashboard
@login_required
def student_dashboard(request):
    stored_session_user_id = request.session.get("session_student")

    print(f"Student Dashboard - Expected: {request.user.id}, Found: {stored_session_user_id}")

    if stored_session_user_id is None or stored_session_user_id != request.user.id:
        messages.warning(request, "Session expired! Refreshing session...")
        request.session["session_student"] = request.user.id

    # Basic user information
    full_name = request.user.get_full_name() or request.user.username
    
    try:
        student = Student.objects.get(user=request.user)
        
        # Get all active enrollments
        enrollments = Enrollment.objects.filter(student=student, enrollment_status='Active')
        total_courses = enrollments.count()
        
        # Get program information from enrolled courses
        program_info = None
        department_name = None
        if enrollments.exists():
            # Get the first enrollment's course program
            first_course = enrollments.first().sem_course.course
            if hasattr(first_course, 'program'):
                program_info = first_course.program
                department_name = program_info.department.name if program_info.department else None
        
        program_name = program_info.name if program_info else "Not Assigned"
        program_id = program_info.program_id if program_info else "N/A"
        
        # Calculate attendance statistics for enrolled courses
        enrolled_courses = []
        
        for enrollment in enrollments:
            course = enrollment.sem_course.course

            try:
                course_assign = CourseAssign.objects.get(sem_course=enrollment.sem_course)
                faculty_name = course_assign.faculty.faculty.name if course_assign.faculty.faculty else "No faculty assigned"
                schedule = course_assign.schedule
                section = course_assign.section
            except CourseAssign.DoesNotExist:
                faculty_name = "No faculty assigned"
                schedule = "Not scheduled"
                section = "N/A"

            attendance_records = StudentAttendance.objects.filter(enrollment_id=enrollment)
            total_classes = attendance_records.count()
            attended_classes = attendance_records.filter(attendance_status='1').count()
            attendance_percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0

            enrolled_courses.append({
                'course': course,
                'faculty_name': faculty_name,
                'schedule': schedule,
                'section': section,
                'total_classes': total_classes,
                'attended_classes': attended_classes,
                'attendance_percentage': attendance_percentage
            })

        return render(request, "student/dashboard.html", {
            "full_name": full_name,
            "student": student,
            "total_courses": total_courses,
            "enrolled_courses": enrolled_courses,
            "program_name": program_name,
            "program_id": program_id,
            "department_name": department_name or "Not Assigned",
        })
    except Student.DoesNotExist:
        messages.warning(request, "Your student profile has not been created yet. Please contact the administrator.")
        return render(request, "student/dashboard.html", {
            "full_name": full_name,
            "student": None,
            "total_courses": 0,
            "enrolled_courses": [],
            "program_name": "Not Assigned",
            "program_id": "N/A",
            "department_name": "Not Assigned",
        })

@login_required
def student_courses_index(request):
    try:
        # Get the logged-in student
        student = Student.objects.get(user=request.user)
        
        # Fetch the enrollments for this student
        enrollments = Enrollment.objects.filter(student=student, enrollment_status='Active')
        
        # If no enrollments exist, return empty context
        if not enrollments.exists():
            return render(request, 'student/courses/index.html', {
                'enrolled_courses': [],
                'student': student,
                'no_enrollments': True
            })
        
        # Create a list of dictionaries that will hold course and its details
        enrolled_courses = []
        
        for enrollment in enrollments:
            # Get course assignment information if available
            try:
                course_assign = CourseAssign.objects.get(sem_course=enrollment.sem_course)
                faculty_assign = course_assign.faculty
                faculty_name = faculty_assign.faculty.name if faculty_assign.faculty else "No faculty assigned"
                schedule = course_assign.schedule
                section = course_assign.section
            except CourseAssign.DoesNotExist:
                faculty_name = "No faculty assigned"
                schedule = "Not scheduled"
                section = "N/A"
            
            # Get attendance statistics
            attendance_records = StudentAttendance.objects.filter(
                enrollment_id=enrollment
            )
            total_classes = attendance_records.count()
            attended_classes = attendance_records.filter(attendance_status='1').count()
            
            enrolled_courses.append({
                'enrollment': enrollment,
                'course': enrollment.sem_course.course,
                'faculty_name': faculty_name,
                'schedule': schedule,
                'section': section,
                'total_classes': total_classes,
                'attended_classes': attended_classes,
                'attendance_percentage': (attended_classes / total_classes * 100) if total_classes > 0 else 0,
                'has_attendance': total_classes > 0
            })
        
        return render(request, 'student/courses/index.html', {
            'enrolled_courses': enrolled_courses,
            'student': student,
            'no_enrollments': False
        })
        
    except Student.DoesNotExist:
        # Handle case where student profile doesn't exist
        return render(request, 'student/courses/index.html', {
            'enrolled_courses': [],
            'no_enrollments': True,
            'error': 'Student profile not found'
        })
    except Exception as e:
        # Handle any other unexpected errors
        return render(request, 'student/courses/index.html', {
            'enrolled_courses': [],
            'no_enrollments': True,
            'error': str(e)
        })

@login_required
def student_course_detail(request, course_id):
    # Get the logged-in student
    student = Student.objects.get(user=request.user)
    
    # Get the course and verify enrollment
    try:
        course = Course.objects.get(id=course_id)
        enrollment = Enrollment.objects.get(
            student=student,
            sem_course__course=course,
            enrollment_status='Active'
        )
        
        # Get course assignment details
        try:
            course_assign = CourseAssign.objects.get(sem_course=enrollment.sem_course)
            faculty_name = course_assign.faculty.faculty.name if course_assign.faculty.faculty else "No faculty assigned"
            schedule = course_assign.schedule
            section = course_assign.section
        except CourseAssign.DoesNotExist:
            faculty_name = "No faculty assigned"
            schedule = "Not scheduled"
            section = "N/A"
        
        # Get attendance records and calculate stats
        attendance_records = StudentAttendance.objects.filter(
            enrollment_id=enrollment
        ).order_by('-attendance_date')
        
        total_classes = attendance_records.count()
        attended_classes = attendance_records.filter(attendance_status='1').count()
        attendance_percentage = (attended_classes / total_classes * 100) if total_classes > 0 else 0
        
        context = {
            'course': course,
            'enrollment': enrollment,
            'faculty_name': faculty_name,
            'schedule': schedule,
            'section': section,
            'attendance_records': attendance_records,
            'total_classes': total_classes,
            'attended_classes': attended_classes,
            'attendance_percentage': attendance_percentage
        }
        
        return render(request, 'student/courses/detail.html', context)
        
    except (Course.DoesNotExist, Enrollment.DoesNotExist):
        messages.error(request, 'Course not found or you are not enrolled in this course.')
        return redirect('student_courses_index')
