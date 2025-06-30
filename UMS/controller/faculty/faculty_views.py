from django.shortcuts import render,redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from ...models import Faculty,DepartAssign,CourseAssign,Attendances,SemCourses,Enrollment,Student,StudentAttendance,Camera
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect
from django.http import JsonResponse,StreamingHttpResponse
import json,time,threading
import base64
import numpy as np
import cv2
import os
from ultralytics import YOLO
from django.http import JsonResponse
import json
from tensorflow.keras.models import load_model
from ...forms import AttendanceForm
from django.urls import reverse
from PIL import Image
from tensorflow.keras.preprocessing import image  
import logging

@login_required
def faculty_dashboard(request):
    stored_session_user_id = request.session.get("session_faculty")

    print(f"🔍 Faculty Dashboard - Expected: {request.user.id}, Found: {stored_session_user_id}")

    if stored_session_user_id is None or stored_session_user_id != request.user.id:
        messages.warning(request, "Session expired! Refreshing session...")
        request.session["session_faculty"] = request.user.id

    # Basic user information
    try:
        faculty = Faculty.objects.get(user=request.user)
        full_name = request.user.get_full_name() or request.user.username
    except Faculty.DoesNotExist:
        messages.error(request, "Faculty profile not found.")
        return redirect('login')
    
    try:
        # Get department assignment and courses
        depart_assign = DepartAssign.objects.get(faculty=faculty)
        assigned_courses = CourseAssign.objects.filter(faculty=depart_assign)
        total_courses = assigned_courses.count()
        
        # Get current semester from the first assigned course
        current_semester = None
        if assigned_courses.exists():
            current_semester = assigned_courses.first().sem_course.semester.semester_name
        
        # Calculate attendance statistics
        courses_with_stats = []
        total_attendance_percentage = 0
        courses_with_attendance = 0
        
        for course_assign in assigned_courses:
            course = course_assign.sem_course.course
            schedule = course_assign.schedule
            section = course_assign.section
            
            # Get attendance records for this course
            attendance_sessions = Attendances.objects.filter(
                sem_course_id=course_assign.sem_course
            )
            
            total_sessions = attendance_sessions.count()
            marked_sessions = StudentAttendance.objects.filter(
                attendance_id__in=attendance_sessions,
                is_mark=True
            ).values('attendance_id').distinct().count()
            
            completion_percentage = (marked_sessions / total_sessions * 100) if total_sessions > 0 else 0
            
            if total_sessions > 0:  # Only count courses that have attendance sessions
                total_attendance_percentage += completion_percentage
                courses_with_attendance += 1

            courses_with_stats.append({
                'course': course,
                'schedule': schedule,
                'section': section,
                'total_sessions': total_sessions,
                'marked_sessions': marked_sessions,
                'completion_percentage': completion_percentage
            })
        
        # Calculate overall completion average
        overall_completion = (total_attendance_percentage / courses_with_attendance) if courses_with_attendance > 0 else 0
        
        # Get recent attendance sessions (last 5 records)
        recent_attendance = Attendances.objects.filter(
            sem_course_id__in=[ac.sem_course for ac in assigned_courses]
        ).order_by('-attendance_date')[:5]

        return render(request, "faculty/dashboard.html", {
            "full_name": full_name,
            "faculty": faculty,
            "department": depart_assign.department.name,
            "total_courses": total_courses,
            "current_semester": current_semester or "Awaiting Course",
            "assigned_courses": courses_with_stats,
            "overall_completion": overall_completion,
            "recent_attendance": recent_attendance,
            "depart_assign": depart_assign,
        })
    except DepartAssign.DoesNotExist:
        messages.warning(request, "You have not been assigned to any department yet. Please contact the administrator.")
        return render(request, "faculty/dashboard.html", {
            "full_name": full_name,
            "faculty": faculty,
            "department": "Not Assigned",
            "total_courses": 0,
            "current_semester": "Awaiting Course Assignment",
            "assigned_courses": [],
            "overall_completion": 0,
            "recent_attendance": [],
            "depart_assign": None,
        })


@login_required
def faculty_cources_index(request):
    # Get the logged-in faculty member
    faculty = Faculty.objects.get(user=request.user)

    # Fetch the corresponding DepartAssign instance for the faculty
    depart_assign = DepartAssign.objects.get(faculty=faculty)
    full_name = request.user.get_full_name() or request.user.username

    # Fetch the courses assigned to this faculty via the DepartAssign instance
    courses = CourseAssign.objects.filter(faculty=depart_assign)

    # Create a list of dictionaries that will hold course and its attendance
    course_attendance_list = []
    
    for course in courses:
        attendance = Attendances.objects.filter(sem_course_id=course.sem_course.id).first()  # Fetch attendance for the course
        course_attendance_list.append({
            'course': course,
            'attendance': attendance
        })

    return render(request, 'faculty/courses/index.html', {
        'courses': course_attendance_list,
        'faculty': faculty,
        'full_name':full_name
    })

# helper funtion to  load save model
def get_model_path(sem_course):
    try:
        course_assign = CourseAssign.objects.get(sem_course=sem_course)
        course_name = sem_course.course.name.strip()
        schedule = course_assign.schedule.strip()

        parts = schedule.split()
        if len(parts) != 2:
            raise ValueError("Invalid schedule format")

        day = parts[0]
        time_range = parts[1]
        start_time, end_time = time_range.split('-')
        start_hour = start_time.split(':')[0].zfill(2)
        end_hour = end_time.split(':')[0].zfill(2)

        safe_schedule = f"{day}({start_hour} to {end_hour})"
        model_filename = f"{course_name}-{safe_schedule}.keras"

        model_path = os.path.join(r"D:\MSSQL+SACAS\SACAS\model\savedModels", model_filename)
        print(f"Model path generated: {model_path}")
        return model_path
    except Exception as e:
        print(f"Error generating model path: {e}")
        return None



# camera attendance
yolo_model = YOLO(r"D:\MSSQL+SACAS\SACAS\model\yolov8n-face.pt")
yolo_model.fuse()  # Speed optimization


# @login_required(login_url='login')
# @csrf_exempt
# def camera_attendance(request, sem_course_id, attendance_id):
#     if request.method == 'GET':
#         # Render camera page with required data
#         sem_course = get_object_or_404(SemCourses, id=sem_course_id)
#         course = sem_course.course
#         attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
#         students_with_same_course = Student.objects.filter(
#             enrollment__sem_course=sem_course
#         ).values('student_id', 'name', 'enrollment__id')

#         context = {
#             'course_name': course.name,
#             'students': students_with_same_course,
#             'sem_course_id': sem_course_id,
#             'attendance_id': attendance_id
#         }
#         return render(request, 'faculty/camera/camera_page.html', context)

#     if request.method == 'POST':
#         try:
#             # ✅ FIX: Define sem_course for POST method
#             sem_course = get_object_or_404(SemCourses, id=sem_course_id)

#             # Load frame data from the request
#             data = json.loads(request.body)
#             frame_data = data.get("frame")

#             if not frame_data:
#                 return JsonResponse({"status": "error", "message": "No frame data provided."})

#             # Decode Base64 image data to OpenCV image
#             img_data = base64.b64decode(frame_data.split(",")[1])
#             np_arr = np.frombuffer(img_data, np.uint8)
#             img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

#             # Load YOLO model
#             # yolo_model = YOLO(r"D:\MSSQL+SACAS\SACAS\model\yolov8n-face.pt")
#             results = yolo_model(img)

#             # Load the pre-trained ResNet model
#             model_path = get_model_path(sem_course)
#             if not os.path.exists(model_path):
#                 return JsonResponse({"status": "error", "message": "Trained model not found."})
#             model = load_model(model_path)

#             # Load the names and IDs of enrolled students
#             student_data = [
#                 {"name": student["name"], "student_id": student["student_id"]}
#                 for student in Student.objects.filter(
#                     enrollment__sem_course_id=sem_course_id
#                 ).values('name', 'student_id')
#             ]

#             student_data = sorted(student_data, key=lambda x: x["name"])

#             cropped_faces_dir = r"D:\MSSQL+SACAS\SACAS\model\cropped_faces"
#             os.makedirs(cropped_faces_dir, exist_ok=True)

#             recognized_ids = set()  # Yeh loop ke bahar initialize hoga


#             attendance_status = []
#             for idx, box in enumerate(results[0].boxes.xyxy):
#                 x1, y1, x2, y2 = map(int, box)
#                 cropped_face = img[y1:y2, x1:x2]
#                 # if cropped_face.size > 0:

#                 if cropped_face.size > 0 and cropped_face.shape[0] > 50 and cropped_face.shape[1] > 50:

#                     target_size = (224, 224)
#                     h, w = cropped_face.shape[:2]
#                     scale = min(target_size[1] / h, target_size[0] / w)
#                     resized_h, resized_w = int(h * scale), int(w * scale)
#                     resized_face = cv2.resize(cropped_face, (resized_w, resized_h))

#                     delta_w = target_size[0] - resized_w
#                     delta_h = target_size[1] - resized_h
#                     top, bottom = delta_h // 2, delta_h - (delta_h // 2)
#                     left, right = delta_w // 2, delta_w - (delta_w // 2)

#                     padded_face = cv2.copyMakeBorder(
#                         resized_face, top, bottom, left, right, cv2.BORDER_CONSTANT, value=[0, 0, 0]
#                     )

#                     face_path = os.path.join(cropped_faces_dir, f"face_{idx}.jpg")
#                     cv2.imwrite(face_path, padded_face)

#                     face_img = padded_face / 255.0
#                     face_img = np.expand_dims(face_img, axis=0)


#                 try:
#                     predictions = model.predict(face_img)
#                     predicted_class = np.argmax(predictions, axis=1)[0]
#                     confidence = np.max(predictions) * 100

#                     print(f"Predicted Class: {predicted_class}, Confidence: {confidence}%")

#                     # if confidence >= 60:
#                     #     student = student_data[predicted_class]
#                     #     attendance_status.append({
#                     #         "student_name": student["name"],
#                     #         "student_id": student["student_id"],
#                     #         "status": 1
#                     #     })


#                     if confidence >= 60:
#                         student = student_data[predicted_class]
#                         student_id = student["student_id"]

#                         if student_id not in recognized_ids:

#                             time.sleep(0.5)

#                             attendance_status.append({
#                                 "student_name": student["name"],
#                                 "student_id": student_id,
#                                 "status": 1
#                             })
#                             recognized_ids.add(student_id)

#                     else:
#                         attendance_status.append({
#                             "student_name": "Unknown",
#                             "student_id": "Unknown",
#                             "status": 0
#                         })

#                 else:
#                     attendance_status.append({
#                         "student_name": "Unknown",
#                         "student_id": "Unknown",
#                         "status": 0
#                     })

#             print("Final Attendance Status:", attendance_status)

#             #  Delete all cropped faces after processing
#             for file_name in os.listdir(cropped_faces_dir):
#                 file_path = os.path.join(cropped_faces_dir, file_name)
#                 try:
#                     if os.path.isfile(file_path):
#                         os.remove(file_path)
#                 except Exception as e:
#                     print(f"Error deleting file {file_path}: {e}")

#             return JsonResponse({
#                 "status": "success",
#                 "message": "Faces detected and attendance marked.",
#                 "attendance_status": attendance_status
#             })


#         except Exception as e:
#             return JsonResponse({"status": "error", "message": str(e)})

#     return JsonResponse({"status": "error", "message": "Invalid request method."})

import warnings
warnings.filterwarnings("ignore", category=UserWarning)
@login_required(login_url='login')
@csrf_exempt
def camera_attendance(request, sem_course_id, attendance_id):
    if request.method == 'GET':
        sem_course = get_object_or_404(SemCourses, id=sem_course_id)
        course = sem_course.course
        attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
        students_with_same_course = Student.objects.filter(
            enrollment__sem_course=sem_course
        ).values('student_id', 'name', 'enrollment__id')

        context = {
            'course_name': course.name,
            'students': students_with_same_course,
            'sem_course_id': sem_course_id,
            'attendance_id': attendance_id
        }
        return render(request, 'faculty/camera/camera_page.html', context)

    elif request.method == 'POST':
        try:
            sem_course = get_object_or_404(SemCourses, id=sem_course_id)

            data = json.loads(request.body)
            frame_data = data.get("frame")

            if not frame_data:
                return JsonResponse({"status": "error", "message": "No frame data provided."})

            img_data = base64.b64decode(frame_data.split(",")[1])
            np_arr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

            # results = yolo_model(img)

            results = yolo_model(img, conf=0.5)  # 50% se zyada confidence wale faces


            model_path = get_model_path(sem_course)
            if not os.path.exists(model_path):
                return JsonResponse({"status": "error", "message": "Trained model not found."})
            model = load_model(model_path)

            student_data = [
                {"name": student["name"], "student_id": student["student_id"]}
                for student in Student.objects.filter(
                    enrollment__sem_course_id=sem_course_id
                ).values('name', 'student_id')
            ]
            student_data = sorted(student_data, key=lambda x: x["name"])

            cropped_faces_dir = r"D:\MSSQL+SACAS\SACAS\model\cropped_faces"
            os.makedirs(cropped_faces_dir, exist_ok=True)

            recognized_ids = set()
            attendance_status = []

            for idx, box in enumerate(results[0].boxes.xyxy):
                x1, y1, x2, y2 = map(int, box)
                cropped_face = img[y1:y2, x1:x2]

                if cropped_face.size > 0 and cropped_face.shape[0] > 50 and cropped_face.shape[1] > 50:
                    target_size = (224, 224)
                    h, w = cropped_face.shape[:2]
                    scale = min(target_size[1] / h, target_size[0] / w)
                    resized_h, resized_w = int(h * scale), int(w * scale)
                    resized_face = cv2.resize(cropped_face, (resized_w, resized_h))

                    delta_w = target_size[0] - resized_w
                    delta_h = target_size[1] - resized_h
                    top, bottom = delta_h // 2, delta_h - (delta_h // 2)
                    left, right = delta_w // 2, delta_w - (delta_w // 2)

                    padded_face = cv2.copyMakeBorder(
                        resized_face, top, bottom, left, right,
                        cv2.BORDER_CONSTANT, value=[0, 0, 0]
                    )

                    face_path = os.path.join(cropped_faces_dir, f"face_{idx}.jpg")
                    cv2.imwrite(face_path, padded_face)

                    face_img = padded_face / 255.0
                    face_img = np.expand_dims(face_img, axis=0)

                    try:
                        predictions = model.predict(face_img)
                        predicted_class = np.argmax(predictions, axis=1)[0]
                        confidence = np.max(predictions) * 100

                        print(f"Predicted Class: {predicted_class}, Confidence: {confidence}%")

                        if confidence >= 60:
                            student = student_data[predicted_class]
                            student_id = student["student_id"]

                            if student_id not in recognized_ids:
                                time.sleep(0.5)
                                attendance_status.append({
                                    "student_name": student["name"],
                                    "student_id": student_id,
                                    "status": 1
                                })
                                recognized_ids.add(student_id)
                        else:
                            attendance_status.append({
                                "student_name": "Unknown",
                                "student_id": "Unknown",
                                "status": 0
                            })
                    except Exception as e:
                        print(f"Recognition error: {e}")
                        attendance_status.append({
                            "student_name": "Unknown",
                            "student_id": "Unknown",
                            "status": 0
                        })

            print("Final Attendance Status:", attendance_status)

            # for file_name in os.listdir(cropped_faces_dir):
            #     file_path = os.path.join(cropped_faces_dir, file_name)
            #     try:
            #         if os.path.isfile(file_path):
            #             os.remove(file_path)
            #     except Exception as e:
            #         print(f"Error deleting file {file_path}: {e}")

            return JsonResponse({
                "status": "success",
                "message": "Faces detected and attendance marked.",
                "attendance_status": attendance_status
            })

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})

    return JsonResponse({"status": "error", "message": "Invalid request method."})

   

JPEG_QUALITY = 70
def _source_url(cam: Camera):
    """Return argument for cv2.VideoCapture based on camera_type."""
    if cam.camera_type == 'local':
        # Local camera will be handled by JS, backend streaming not needed
        return None  

    cred = f"{cam.username}:{cam.password}@" if cam.username else ""
    endpoint = cam.endpoint or ("/video" if cam.camera_type == 'ip' else "")
    proto = "http" if cam.camera_type == 'ip' else "rtsp"
    return f"{proto}://{cred}{cam.ip_address}:{cam.port}{endpoint}"


def stream_frame(request):
    active = Camera.objects.filter(is_active=True).first()
    if not active:
        return JsonResponse({'error': 'No active camera', 'type': 'none'}, status=404)

    if active.camera_type == 'local':
        return JsonResponse({'error': 'Local camera stream is handled by browser directly', 'type': 'local'}, status=400)

    source = _source_url(active)
    if not source:
        return JsonResponse({'error': 'Invalid camera source', 'type': 'invalid'}, status=500)

    cap = cv2.VideoCapture(source)
    if not cap.isOpened():
        return JsonResponse({'error': 'Unable to open stream', 'type': 'unavailable'}, status=500)

    def gen():
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            ok, buf = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
            if not ok:
                continue
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' +
                   buf.tobytes() + b'\r\n')
        cap.release()

    return StreamingHttpResponse(
        gen(),
        content_type='multipart/x-mixed-replace; boundary=frame',
        headers={'Cache-Control': 'no-cache'}
    )



# Attendance Save for face recognize
# @login_required(login_url='login')
# def save_camera_attendance(request, sem_course_id, attendance_id):
#     if request.method == 'POST':
#         try:
#             attendance = get_object_or_404(Attendances, attendance_id=attendance_id)

#             # Get all enrollments for the specific sem_course_id
#             enrollments = Enrollment.objects.filter(sem_course_id=sem_course_id,                
#             enrollment_status='Active'
# )

#             # Check if any attendance status has been recorded for each student
#             attendance_statuses = {key.split('_')[1]: value for key, value in request.POST.items() if key.startswith('attendance_')}
            
#             # Validate that at least one status is marked for each student (if the student is not marked, assume absent)
#             for enrollment in enrollments:
#                 student_id = enrollment.student_id
#                 # If no attendance is recorded for the student, mark as absent
#                 if str(student_id) not in attendance_statuses:
#                     attendance_statuses[str(student_id)] = 'A'  # Mark as Absent if no data is provided

#             # Iterate through all the enrollments and create StudentAttendance records
#             for enrollment in enrollments:
#                 student_id = enrollment.student_id
#                 attendance_status = attendance_statuses[str(student_id)]  # 'P' for Present or 'A' for Absent
                
#                 # Create the StudentAttendance entry
#                 StudentAttendance.objects.create(
#                     enrollment_id=enrollment,  # Use the actual Enrollment instance
#                     attendance_id=attendance,
#                     attendance_status=1 if attendance_status == 'P' else 0,  # 1 for Present, 0 for Absent
#                     remarks=request.POST.get('remarks', '').strip(),  # Capture any remarks
#                     attendance_date=attendance.attendance_date  # Add this line

#                 )

#                 print("Enrollments:", enrollments)
#                 print("Attendance statuses from form:", attendance_statuses)


#             return JsonResponse({'status': 'success'})

#         except Exception as e:
#             return JsonResponse({'status': 'error', 'message': str(e)})

#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

# Attendance Save for face recognize
@login_required(login_url='login')
def save_camera_attendance(request, sem_course_id, attendance_id):
    if request.method == 'POST':
        try:
            attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
            attendance_date = attendance.attendance_date
            enrollments = Enrollment.objects.filter(
                sem_course_id=sem_course_id,
                enrollment_status='Active'
            )
            
            # Parse the request data
            try:
                data = json.loads(request.body)
                attendance_statuses = data.get('attendance_status', [])
                remarks = data.get('remarks', '')
                
                # Debug print
                print("Received attendance data:", attendance_statuses)
                
            except json.JSONDecodeError:
                print("JSON decode error - trying form data")
                attendance_statuses = request.POST.getlist('attendance_status[]')
                remarks = request.POST.get('remarks', '')

            # Validate attendance data
            if not attendance_statuses:
                print("No attendance data received")
                return JsonResponse({
                    'status': 'error',
                    'message': 'No students detected for attendance. Please detect faces and try again.'
                })

            if not remarks:
                remarks = "Attendance marked via face recognition"

            # Create a set of marked student IDs for faster lookup
            marked_students = set()
            
            # Process each detected student
            for status in attendance_statuses:
                # Handle both string and dictionary formats
                if isinstance(status, str):
                    student_id = status
                    is_present = True
                else:
                    student_id = status.get('student_id')
                    is_present = status.get('status') == 1
                
                print(f"Processing student: {student_id}, Present: {is_present}")
                
                if student_id and student_id != 'Unknown':
                    try:
                        enrollment = enrollments.get(student__student_id=student_id)
                        StudentAttendance.objects.update_or_create(
                            enrollment_id=enrollment,
                            attendance_id=attendance,
                            defaults={
                                'attendance_status': '1' if is_present else '0',
                                'remarks': remarks,
                                'attendance_date': attendance_date,
                                'is_mark': True
                            }
                        )
                        marked_students.add(student_id)
                        print(f"Marked attendance for student: {student_id}")
                    except Enrollment.DoesNotExist:
                        print(f"Enrollment not found for student: {student_id}")
                        continue

            # Mark absent for students not detected
            for enrollment in enrollments:
                if enrollment.student.student_id not in marked_students:
                    StudentAttendance.objects.update_or_create(
                        enrollment_id=enrollment,
                        attendance_id=attendance,
                        defaults={
                            'attendance_status': '0',  # Mark as absent
                            'remarks': f"{remarks} (Not detected by camera)",
                            'attendance_date': attendance_date,
                            'is_mark': True
                        }
                    )
                    print(f"Marked absent for student: {enrollment.student.student_id}")

            messages.success(request, 'Attendance marked successfully!')
            return JsonResponse({
                'status': 'success',
                'message': 'Attendance saved successfully',
                'redirect_url': reverse('attendance_roaster', args=[sem_course_id])
            })
        except Exception as e:
            print(f"Error in save_camera_attendance: {str(e)}")
            return JsonResponse({
                'status': 'error',
                'message': f'Error saving attendance: {str(e)}'
            })
    return JsonResponse({
        'status': 'error',
        'message': 'Invalid request method'
    })

#-----------------------------------------------------------------------
# manual  attendance
#-----------------------------------------------------------------------
@login_required(login_url='login')
def attendance_page(request, sem_course_id, attendance_id):
    sem_course = get_object_or_404(SemCourses, id=sem_course_id)
    course = sem_course.course  # use related object directly

    # Get the attendance object for the passed attendance_id
    attendance = get_object_or_404(Attendances, attendance_id=attendance_id)


    # Dynamically filter attendance_date from the `attendance` object
    attendance_date = attendance.attendance_date

    # Get all enrollments for this specific course
    enrollments = Enrollment.objects.filter(sem_course=sem_course)
    # Extract student details
    students_with_same_course = Student.objects.filter(enrollment__sem_course=sem_course).values('student_id', 'name', 'enrollment__id')

    context = {
        'course_name': course.name,
        'enrollments': enrollments,
        'students': students_with_same_course,
        'sem_course_id': sem_course_id,
        'attendance': attendance,
        'attendance_id': attendance_id , # Ensure this is not None
        'attendance_date': attendance_date,  # Pass dynamically filtered attendance_date

    }


    return render(request, 'faculty/attendance/mark_attendance.html', context)

# @login_required(login_url='login')
# def save_attendance(request, sem_course_id, attendance_id):
#     if request.method == 'POST':
#         try:
#             attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
#             attendance_date = attendance.attendance_date

#             # Check if any attendance status has been recorded
#             attendance_statuses = [value for key, value in request.POST.items() if key.startswith('attendance_')]
            
#             # Validate that at least one student has been marked present or absent
#             if not any(status in ['0', '1'] for status in attendance_statuses):  # Assuming '0' for Absent and '1' for Present
#                 return JsonResponse({'status': 'error', 'message': 'Please mark attendance for all students before saving.'})
            
#             # Check if remarks are provided
#             remarks = request.POST.get('remarks', '').strip()  # Get remarks and remove extra spaces
#             if not remarks:  # If remarks are empty
#                 return JsonResponse({'status': 'error', 'message': 'Remarks are required.'})            

#             # Iterate through attendance statuses and create records
#             for key, value in request.POST.items():
#                 if key.startswith('attendance_'):
#                     enrollment_id = key.split('_')[1]  # Extract enrollment ID

#                     if not enrollment_id or not enrollment_id.isdigit():  # Check if valid
#                         continue  # Skip if invalid

#                     attendance_status = value  # Attendance status from dropdown

#                     # Create the StudentAttendance entry
#                     StudentAttendance.objects.create(
#                         enrollment_id_id=enrollment_id,
#                         attendance_id=attendance,
#                         attendance_status=attendance_status,
#                         remarks=remarks,  # Use the captured remarks
#                         # attendance_date= attendance_date,
#                         attendance_date=attendance.attendance_date,
#                         is_mark=True,  # 🔽 This is the key line                        
#                     )

#             messages.success(request, 'Attendance saved successfully!')
#             return JsonResponse({'status': 'success'})

#         except Exception as e:
#             messages.error(request, f'Error saving attendance: {str(e)}')
#             return JsonResponse({'status': 'error', 'message': str(e)})

#     # Handle GET requests
#     return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})



@login_required(login_url='login')
def save_attendance(request, sem_course_id, attendance_id):
    if request.method == 'POST':
        try:
            attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
            attendance_date = attendance.attendance_date
            
            # Get all active enrollments for this course
            enrollments = Enrollment.objects.filter(
                sem_course_id=sem_course_id,
                enrollment_status='Active'
            )
            
            # Get attendance statuses from form
            attendance_statuses = {}
            for key, value in request.POST.items():
                if key.startswith('attendance_'):
                    enrollment_id = key.split('_')[1]
                    attendance_statuses[enrollment_id] = value
            
            # Get remarks
            remarks = request.POST.get('remarks', '').strip()
            if not remarks:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Remarks are required.'
                })
            
            # Process each enrollment
            for enrollment in enrollments:
                enrollment_id = str(enrollment.id)
                
                # Get attendance status (default to absent if not marked)
                status = attendance_statuses.get(enrollment_id, '0')
                
                # Create or update attendance record
                StudentAttendance.objects.update_or_create(
                    enrollment_id=enrollment,
                    attendance_id=attendance,
                    defaults={
                        'attendance_status': status,  # Use the status directly
                        'remarks': remarks,
                        'attendance_date': attendance_date,
                        'is_mark': True
                    }
                )

            messages.success(request, 'Attendance marked successfully!')
            return JsonResponse({
                'status': 'success',
                'message': 'Attendance saved successfully',
                'redirect_url': reverse('attendance_roaster', args=[sem_course_id])
            })

        except Exception as e:
            messages.error(request, f'Error saving attendance: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Handle GET requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})

#-----------------------------------------------------------------------
# attendance logs
#-----------------------------------------------------------------------
from django.db.models import Count, Q, Avg

@login_required(login_url='login')
def attendance_log(request):
    # Filters from request
    course_id = request.GET.get('course_id')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    attendance_status = request.GET.get('attendance_status')

    # Handle `low_attendance` parameter
    low_attendance = request.GET.get('low_attendance', '75.0')  # Default to '75.0' as a string
    try:
        low_attendance_threshold = float(low_attendance) if low_attendance else 75.0  # Convert or default to 75.0
    except ValueError:
        low_attendance_threshold = 75.0  # Fallback in case of invalid input

    # Base Query
    logs = StudentAttendance.objects.select_related('enrollment_id__sem_course', 'attendance_id')

    # Apply Filters
    if course_id:
        logs = logs.filter(enrollment_id__sem_course__course_id=course_id)
    if start_date and end_date:
        logs = logs.filter(attendance_date__range=[start_date, end_date])
    if attendance_status:
        logs = logs.filter(attendance_status=attendance_status)

    # Calculate Attendance Percentage for Students
    students = logs.values('enrollment_id', 'enrollment_id__student__name', 'enrollment_id__student__student_id').annotate(
        total_classes=Count('attendance_date', distinct=True),
        classes_attended=Count('attendance_status', filter=Q(attendance_status='Present')),
        attendance_percentage=(Count('attendance_status', filter=Q(attendance_status='Present')) * 100.0) / Count('attendance_date', distinct=True)
    )

    # Calculate Average Attendance
    average_attendance = students.aggregate(average_attendance=Avg('attendance_percentage'))['average_attendance']

    # Filter for Low Attendance if provided
    if low_attendance_threshold:
        students = students.filter(attendance_percentage__lt=low_attendance_threshold)

    context = {
        'logs': logs,  # Detailed logs for the selected filters
        'students': students,  # Filtered students with calculated percentages
        'average_attendance': average_attendance,  # Overall average attendance
        'filters': {
            'course_id': course_id,
            'start_date': start_date,
            'end_date': end_date,
            'attendance_status': attendance_status,
            'low_attendance_threshold': low_attendance_threshold,
        },
    }
    return render(request, 'faculty/logs/logs.html', context)



#-----------------------------------------------------------------------
# attendance logs
#-----------------------------------------------------------------------
@login_required(login_url='login')
def attendance_log(request):
    # Get attendance data for all students
    attendance_data = StudentAttendance.objects.select_related('enrollment_id__student').select_related('attendance_id')

 # Get the course name from the first record (or set it to None if empty)
    course_name = attendance_data[0].enrollment_id.sem_course.course.name if attendance_data else None

    context = {
        'attendance_data': attendance_data,
        'total_students': attendance_data.count(),
        'present_students': attendance_data.filter(attendance_status='1').count(),
        'absent_students': attendance_data.filter(attendance_status='0').count(),
        'course_name': course_name,  # Add course name to context
    }
    return render(request, 'faculty/logs/logs.html', context)

def view_attendance(request, pk):
    attendance = get_object_or_404(StudentAttendance, pk=pk)
    return render(request, 'attendance/view_attendance.html', {'attendance': attendance})

def edit_attendance(request, pk):
    attendance = get_object_or_404(StudentAttendance, pk=pk)
    if request.method == 'POST':
        form = AttendanceForm(request.POST, instance=attendance)
        if form.is_valid():
            form.save()
            return redirect('attendance_log')  # Redirect to attendance log page after saving
    else:
        form = AttendanceForm(instance=attendance)
    return render(request, 'attendance/edit_attendance.html', {'form': form})

def delete_attendance(request, pk):
    attendance = get_object_or_404(StudentAttendance, pk=pk)
    if request.method == 'POST':
        attendance.delete()
        return HttpResponseRedirect(reverse('attendance_log'))  # Redirect to attendance log page
    return render(request, 'attendance/delete_attendance.html', {'attendance': attendance})


@login_required
def attendance_roaster(request, sem_course_id):
    sem_course = get_object_or_404(SemCourses, id=sem_course_id)
    course = sem_course.course
    faculty_assign = CourseAssign.objects.filter(sem_course=sem_course).first()
    faculty_name = faculty_assign.faculty.faculty.name if faculty_assign and faculty_assign.faculty and faculty_assign.faculty.faculty else "No faculty assigned"
    schedule = faculty_assign.schedule if faculty_assign else "Not scheduled"
    section = faculty_assign.section if faculty_assign else "N/A"
    
    # Extract time slots from schedule (format: "Day HH:MM-HH:MM")
    time_slot = schedule.split(' ')[1] if schedule and ' ' in schedule else "00:00-00:00"
    from_time, to_time = time_slot.split('-') if '-' in time_slot else ("00:00", "00:00")
    
    # Get all attendance sessions ordered by date
    attendance_sessions = Attendances.objects.filter(
        sem_course_id=sem_course
    ).order_by('attendance_date')

    
    # Prepare attendance data
    attendance_data = []
    for idx, session in enumerate(attendance_sessions, 1):
        is_marked = StudentAttendance.objects.filter(attendance_id=session, is_mark=True).exists()
                
        attendance_data.append({
            'sr': idx,
            'date': session.attendance_date,
            'day': session.attendance_date.strftime('%A'),
            'from_time': from_time,
            'to_time': to_time,
            'marked': is_marked,
            'session_id': session.attendance_id
        })

    # 🔽 Add this block for modal logic
    first_attendance = Attendances.objects.filter(sem_course_id=sem_course).first()
    course_item = {
        'course': faculty_assign,
        'attendance': first_attendance
    }

    context = {
        'course': course,
        'sem_course': sem_course,
        'faculty_name': faculty_name,
        'schedule': schedule,
        'section': section,
        'attendance_data': attendance_data,
        'item': course_item  # 🔽 You can use this 'item' variable in your modal template as before
    }

    return render(request, 'faculty/courses/attendance_roaster.html', context)  

@login_required(login_url='login')
def mark_attendance_for_date(request, sem_course_id, attendance_id):
    """View to mark attendance for a specific date"""
    sem_course = get_object_or_404(SemCourses, id=sem_course_id)
    course = sem_course.course
    attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
    
    # Get all enrollments for this specific course
    enrollments = Enrollment.objects.filter(
        sem_course=sem_course,
        enrollment_status='Active'
    )
    
    # Get existing attendance records for this session
    existing_attendance = StudentAttendance.objects.filter(
        attendance_id=attendance
    )
    
    # Create a dictionary of enrollment_id to attendance status for quick lookup
    attendance_status_dict = {}
    for record in existing_attendance:
        attendance_status_dict[record.enrollment_id_id] = record.attendance_status
    
    # Get student details
    students = Student.objects.filter(
        enrollment__sem_course=sem_course,
        enrollment__enrollment_status='Active'
    ).values('student_id', 'name', 'enrollment__id')
    
    # Add attendance status to each student
    for student in students:
        enrollment_id = student['enrollment__id']
        student['attendance_status'] = attendance_status_dict.get(enrollment_id, None)
    
    context = {
        'course_name': course.name,
        'sem_course_id': sem_course_id,
        'attendance_id': attendance_id,
        'attendance_date': attendance.attendance_date,
        'students': students,
        'existing_attendance': existing_attendance,
        'page_title': f"Mark Attendance - {course.name} - {attendance.attendance_date}"
    }
    
    return render(request, 'faculty/attendance/mark_attendance.html', context)

@login_required(login_url='login')
def save_attendance(request, sem_course_id, attendance_id):
    if request.method == 'POST':
        try:
            attendance = get_object_or_404(Attendances, attendance_id=attendance_id)
            attendance_date = attendance.attendance_date
            
            # Get all active enrollments for this course
            enrollments = Enrollment.objects.filter(
                sem_course_id=sem_course_id,
                enrollment_status='Active'
            )
            
            # Get attendance statuses from form
            attendance_statuses = {}
            for key, value in request.POST.items():
                if key.startswith('attendance_'):
                    enrollment_id = key.split('_')[1]
                    attendance_statuses[enrollment_id] = value
            
            # Get remarks
            remarks = request.POST.get('remarks', '').strip()
            if not remarks:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Remarks are required.'
                })
            
            # Process each enrollment
            for enrollment in enrollments:
                enrollment_id = str(enrollment.id)
                
                # Get attendance status (default to absent if not marked)
                status = attendance_statuses.get(enrollment_id, '0')
                
                # Create or update attendance record
                StudentAttendance.objects.update_or_create(
                    enrollment_id=enrollment,
                    attendance_id=attendance,
                    defaults={
                        'attendance_status': status,  # Use the status directly
                        'remarks': remarks,
                        'attendance_date': attendance_date,
                        'is_mark': True
                    }
                )

            messages.success(request, 'Attendance marked successfully!')
            return JsonResponse({
                'status': 'success',
                'message': 'Attendance saved successfully',
                'redirect_url': reverse('attendance_roaster', args=[sem_course_id])
            })

        except Exception as e:
            messages.error(request, f'Error saving attendance: {str(e)}')
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Handle GET requests
    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'})