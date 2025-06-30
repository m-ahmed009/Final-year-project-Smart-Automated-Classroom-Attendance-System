import os,shutil
from django.conf import settings
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages
# forms
from ...forms import EnrollmentForm

# models
from ...models import Enrollment,Student,SemCourses,StudentImage,CourseAssign

@login_required(login_url='login')
def enrollment_card(request):
    # Get all enrollments for the logged-in student
    enrollments = Enrollment.objects.all()

    # Create a dictionary to hold courses and their corresponding enrollments
    course_enrollments = {}

    for enrollment in enrollments:
        course_name = enrollment.sem_course.course.name

        # Attempt to get the schedule from CourseAssign
        try:
            # Get the CourseAssign for the sem_course
            course_assign = CourseAssign.objects.get(sem_course=enrollment.sem_course)
            schedule = course_assign.schedule  # Get the schedule from CourseAssign
            faculty_assign = course_assign.faculty  # Get the DepartAssign instance

            # Access Faculty name and faculty_id through DepartAssign (faculty is a ForeignKey to Faculty)
            faculty_name = faculty_assign.faculty.name if faculty_assign.faculty else "No faculty assigned"
            faculty_id = faculty_assign.faculty.faculty_id if faculty_assign.faculty else "No faculty assigned"

        except CourseAssign.DoesNotExist:
            schedule = "No schedule."  # Handle case where CourseAssign does not exist
            faculty_name = "No faculty assigned"
            faculty_id = "No faculty assigned"
        except Exception as e:
            schedule = f"Error retrieving schedule: {str(e)}"  # Include exception message for debugging
            faculty_name = "Error in fetching faculty"
            faculty_id = "Error in fetching faculty"

        # Print the schedule for debugging purposes
        # print(f"Course: {course_name}, Schedule: {schedule}, Faculty Name: {faculty_name}, Faculty ID: {faculty_id}")

        # Add data to course_enrollments
        if course_name not in course_enrollments:
            course_enrollments[course_name] = {
                'enrollments': [],
                'schedule': schedule,  # Store the schedule here
                'faculty_name': faculty_name,  # Store the faculty name here
                'faculty_id': faculty_id  # Store the faculty ID here
            }
        course_enrollments[course_name]['enrollments'].append(enrollment)

    return render(request, 'Admin/enrollment/enrollcard.html', {'course_enrollments': course_enrollments})



# enrollments index
@login_required(login_url='login')
def enrollment_index(request):
    enrollments = Enrollment.objects.all()
    return render(request, 'Admin/enrollment/index.html', {'enrollments':enrollments})



# enrollment show after clicking the view button
@login_required(login_url='login')
def enrollment_indexs(request, sem_course_id):
    sem_course = get_object_or_404(SemCourses, id=sem_course_id)
    course = sem_course.course  # ✅ Direct access
    

    enrollments = Enrollment.objects.filter(sem_course=sem_course)
    students_with_same_course = Student.objects.filter(enrollment__sem_course=sem_course)

    context = {
        'course_name': course.name,
        'enrollments': enrollments,
        'students': students_with_same_course,
    }

    return render(request, 'Admin/enrollment/index.html', context)

#enrollment create
@login_required(login_url='login')
def enrollment_create(request):
    students = Student.objects.all()
    sem_courses = SemCourses.objects.all()

    if request.method == 'POST':
        student_id = request.POST.get('student')
        sem_course_id = request.POST.get('sem_course')
        enrollment_status = request.POST.get('enrollment_status')

        try:
            # Use student_id to fetch the student, not the 'id'
            student = Student.objects.get(id=student_id)  # Use student.id here
            sem_course = SemCourses.objects.get(id=sem_course_id)

            # Check if the student is already enrolled in the course with active status
            active_enrollment = Enrollment.objects.filter(
                student=student,
                sem_course=sem_course,
                enrollment_status='Active'
            ).exists()

            if active_enrollment and enrollment_status == 'Active':
                messages.error(request, 'Student is already actively enrolled in this course.')
                form = EnrollmentForm(request.POST, student=student)
            else:
                form = EnrollmentForm(request.POST, student=student)
                if form.is_valid():
                    # Save the enrollment if the form is valid
                    enrollment = form.save(commit=False)
                    enrollment.student = student
                    enrollment.sem_course = sem_course
                    enrollment.save()
                    form.save_m2m()

                    messages.success(
                        request,
                        f'Student: {student.name} - {student.student_id} enrolled successfully in Course: {sem_course.course.name}!'
                    )
                    return redirect('enrollment_card')
                else:
                    messages.error(request, f'Form Errors: {form.errors}')  # Show form-specific errors

        except Student.DoesNotExist:
            # If student does not exist, show error message
            messages.error(request, 'Invalid student selected.')
            form = EnrollmentForm(request.POST)  # Re-render form with the existing data

        except SemCourses.DoesNotExist:
            # If course does not exist, show error message
            messages.error(request, 'Invalid course selected.')
            form = EnrollmentForm(request.POST)  # Re-render form with the existing data

    else:
        form = EnrollmentForm()

    return render(request, 'Admin/enrollment/create.html', {
        'form': form,
        'students': students,
        'sem_courses': sem_courses
    })

# enrollment images
@login_required(login_url='login')
def get_student_images(request):
    student_id = request.GET.get('student_id')
    images = StudentImage.objects.filter(student_id=student_id).values('id', 'image')
    
    image_data = [{'id': image['id'], 'url': image['image'], 'description': f"Image {image['id']}"} for image in images]
    
    return JsonResponse({'images': image_data})



# enrollments Show
@login_required(login_url='login')
def enrollment_show(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    return render(request, 'Admin/enrollment/show.html', {'enrollment': enrollment})



@login_required(login_url='login')
def enrollment_edit(request, pk):
    enrollment = get_object_or_404(Enrollment, pk=pk)
    students = Student.objects.all()
    sem_courses = SemCourses.objects.all()

    # Fetch the selected images for the current enrollment
    selected_images = enrollment.images.all()  # Assuming ManyToManyField named `images`
    selected_image_ids = [img.id for img in selected_images]

    # Load images of the selected student
    student_images = []
    if enrollment.student:
        student_images = StudentImage.objects.filter(student=enrollment.student)

    if request.method == 'POST':
        form = EnrollmentForm(request.POST, instance=enrollment)
        if form.is_valid():
            # Process the selected images from the form
            selected_image_ids_from_form = request.POST.getlist('images')

            # Remove the old images from enrollment (clear relation)
            for image in selected_image_ids:
                image_instance = StudentImage.objects.get(id=image)
                if image_instance not in selected_image_ids_from_form:
                    # If the image is not selected anymore, delete it
                    image_instance.delete()

            # Clear all images and add the new selected images
            enrollment.images.clear()  # Remove all images from this enrollment
            for image_id in selected_image_ids_from_form:
                image = StudentImage.objects.get(id=image_id)
                enrollment.images.add(image)  # Add the selected images

            form.save()  # Save the enrollment with the updated images
            messages.success(request, 'Student enrollment updated successfully.')               
            return redirect('enrollment_index')
    else:
        form = EnrollmentForm(instance=enrollment)

    return render(request, 'Admin/enrollment/edit.html', {
        'form': form,
        'enrollment': enrollment,
        'students': students,
        'sem_courses': sem_courses,
        'student_images': student_images,
        'selected_image_ids': selected_image_ids
    })


# #helper function for enrollment_delete this function will be called for enrollment_delete
# def delete_course_enrollment(course_name):
#     """
#     Delete course-related folders from train, val, and test directories.
#     """
#     base_dirs = ['model/train', 'model/val', 'model/test']

#     for base_dir in base_dirs:
#         course_path = os.path.join(settings.BASE_DIR, base_dir, course_name)

#         if os.path.exists(course_path):
#             try:
#                 shutil.rmtree(course_path)
#                 print(f"Deleted: {course_path}")
#             except Exception as e:
#                 print(f"Failed to delete {course_path}: {e}")


# # enrollments Delete for card
# @login_required(login_url='login')
# def enrollment_delete(request, pk):
#     # Get the enrollment to delete
#     enrollment = get_object_or_404(Enrollment, pk=pk)

#     if request.method == 'POST':
#         # Find all enrollments related to the same sem_course
#         enrollments = Enrollment.objects.filter(sem_course=enrollment.sem_course)

#         # Get course name and schedule to build the path for deletion
#         course_assign = CourseAssign.objects.filter(sem_course=enrollment.sem_course).first()
#         schedule = course_assign.schedule if course_assign else 'NoSchedule'

#         # Define the base path for enrollments folder
#         base_dir = os.path.join(settings.BASE_DIR, 'model/enrollments')

#         # Define the course folder path
#         course_folder = os.path.join(base_dir, f'{enrollment.sem_course.course.name}-({schedule})')

#         # Delete all associated enrollments and their specific directories
#         for enrollment in enrollments:
#             # Define the student folder to delete
#             student_folder = os.path.join(course_folder, f'{enrollment.student.name}({enrollment.student.student_id})')

#             # Check if the student folder exists and delete it
#             if os.path.exists(student_folder):
#                 shutil.rmtree(student_folder)

#             # Delete the enrollment record
#             # Call the delete_course_enrollment function to clean up other directories
#             delete_course_enrollment(enrollment.sem_course.course.name)  # Delete from train, val, and test directories
#             enrollment.delete()

#         # Check if the course folder is empty after deletion
#             if not os.listdir(course_folder):  # Check if the course folder is empty
#                 shutil.rmtree(course_folder)  # Remove the course folder if empty
#                 print(f"Deleted course directory: {course_folder}")



#         messages.success(request, f'All records for the course "{enrollment.sem_course.course.name}" have been deleted successfully!')
#         return redirect('enrollment_card')

#     return redirect('enrollment_card')


# # single enrollment delete and if last student deleted so course folder should be deleted as well.
# @login_required(login_url='login')
# def single_enrollment_delete(request, pk):
#     # Get the specific enrollment to delete
#     enrollment = get_object_or_404(Enrollment, pk=pk)

#     if request.method == 'POST':
#         # Base directory for enrollments
#         base_dir = os.path.join(settings.BASE_DIR, 'model', 'enrollments')

#         # Get course schedule to build path to the student's specific folder
#         course_assign = CourseAssign.objects.filter(sem_course=enrollment.sem_course).first()
#         schedule = course_assign.schedule if course_assign else 'NoSchedule'

#         # Define the paths for the course folder and student folder
#         course_folder = os.path.join(base_dir, f'{enrollment.sem_course.course.name}-({schedule})')
#         student_folder = os.path.join(course_folder, f'{enrollment.student.name}({enrollment.student.student_id})')

#         # Delete student folder if it exists
#         if os.path.exists(student_folder) and os.path.isdir(student_folder):
#             try:
#                 shutil.rmtree(student_folder)
#                 print(f"Deleted specific student directory: {student_folder}")
#             except Exception as e:
#                 print(f"Error deleting student folder: {e}")
#         else:
#             print(f"Student directory not found: {student_folder}")

#         # Delete the enrollment record from the database
#         enrollment.delete()

#         # Check if any enrollments remain for this course
#         remaining_enrollments = Enrollment.objects.filter(sem_course=enrollment.sem_course).exists()

#         if not remaining_enrollments:
#             # If no enrollments remain, delete the whole course folder
#             if os.path.exists(course_folder) and os.path.isdir(course_folder):
#                 try:
#                     shutil.rmtree(course_folder)
#                     print(f"Deleted course directory: {course_folder}")
#                 except Exception as e:
#                     print(f"Error deleting course folder: {e}")

#         # Add a success message
#         messages.success(request, 'Enrollment deleted successfully!')
#         return redirect('enrollment_card')

#     return redirect('enrollment_card')

import warnings
warnings.filterwarnings("ignore", category=UserWarning, message="Your `PyDataset` class should call `super().__init__.*")

# helper fuction for formatted schedule
def format_schedule_for_path(schedule):
    """Consistent schedule formatting for folder paths"""
    try:
        if not schedule or schedule == 'NoSchedule':
            return 'NoSchedule'
        
        parts = schedule.split()
        if len(parts) < 2:
            return schedule
        
        day = parts[0]
        time_range = parts[1]
        
        if '-' not in time_range:
            return f"{day}(Unknown)"
        
        start_time, end_time = time_range.split('-')
        start_hour = start_time.split(':')[0] if ':' in start_time else start_time
        end_hour = end_time.split(':')[0] if ':' in end_time else end_time
        
        return f"{day}({start_hour} to {end_hour})"
    except Exception as e:
        print(f"Error formatting schedule: {e}")
        return schedule

# helper function for Delete individual student folder
def delete_student_folder(course_name, schedule, student):
    """Delete individual student folder from enrollments and splitfaces"""
    formatted_schedule = format_schedule_for_path(schedule)

    # Folders to delete from
    base_paths = [
        os.path.join(settings.BASE_DIR, 'model', 'enrollments'),
        os.path.join(settings.BASE_DIR, 'model', 'splitfaces', f"{course_name}-{formatted_schedule}", 'train'),
        os.path.join(settings.BASE_DIR, 'model', 'splitfaces', f"{course_name}-{formatted_schedule}", 'val'),
        os.path.join(settings.BASE_DIR, 'model', 'splitfaces', f"{course_name}-{formatted_schedule}", 'test'),
    ]

    # Folder name format: Name(ID)
    student_folder_name = f"{student.name}({student.student_id})"
    deletion_success = True

    for base_path in base_paths:
        student_folder = os.path.join(base_path, student_folder_name)
        if os.path.exists(student_folder):
            try:
                shutil.rmtree(student_folder)
            except Exception as e:
                print(f"Error deleting student folder at {student_folder}: {e}")
                deletion_success = False

    return deletion_success

# helper function for delete course data
def delete_course_data(course_name, schedule):
    """Delete all course-related data across all directories"""
    formatted_schedule = format_schedule_for_path(schedule)
    dirs_to_clean = [
        os.path.join('model', 'enrollments'),
        os.path.join('model', 'splitfaces'),      
        os.path.join('model', 'train'),
        os.path.join('model', 'val'),
        os.path.join('model', 'test')
    ]
    
    for base_dir in dirs_to_clean:
        full_path = os.path.join(settings.BASE_DIR, base_dir, f"{course_name}-{formatted_schedule}")
        if os.path.exists(full_path):
            try:
                shutil.rmtree(full_path)
            except Exception as e:
                print(f"Error deleting {full_path}: {e}")

# for individual student delete with directory if  this student is last also delete course folder
@login_required(login_url='login')
def single_enrollment_delete(request, pk):
    """Delete single student enrollment"""
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    if request.method == 'POST':
        try:
            course = enrollment.sem_course.course
            student = enrollment.student
            course_assign = CourseAssign.objects.filter(sem_course=enrollment.sem_course).first()
            schedule = course_assign.schedule if course_assign else 'NoSchedule'
            
            # Delete student folder
            if not delete_student_folder(course.name, schedule, student):
                messages.warning(request, "Student data deleted but some files couldn't be removed")
            
            # Delete enrollment record
            enrollment.delete()
            
            # Check if this was the last enrollment
            remaining = Enrollment.objects.filter(sem_course=enrollment.sem_course).exists()
            if not remaining:
                delete_course_data(course.name, schedule)
                messages.success(request, 'Last student removed - all course data deleted')
            else:
                messages.success(request, 'Student enrollment deleted successfully')
                
        except Exception as e:
            messages.error(request, f'Error deleting enrollment: {str(e)}')
        
        return redirect('enrollment_card')
    
    return redirect('enrollment_card')

# delete enrollment for card
@login_required(login_url='login')
def enrollment_delete(request, pk):
    """Delete entire course with all enrollments"""
    enrollment = get_object_or_404(Enrollment, pk=pk)
    
    if request.method == 'POST':
        try:
            course = enrollment.sem_course.course
            course_assign = CourseAssign.objects.filter(sem_course=enrollment.sem_course).first()
            schedule = course_assign.schedule if course_assign else 'NoSchedule'
            
            # Delete all enrollments
            Enrollment.objects.filter(sem_course=enrollment.sem_course).delete()
            
            # Delete all course data
            delete_course_data(course.name, schedule)
            
            messages.success(request, f'All data for {course.name} deleted successfully')
            
        except Exception as e:
            messages.error(request, f'Error deleting course: {str(e)}')
        
        return redirect('enrollment_card')
    
    return redirect('enrollment_card')



# +---------------------------------------------------------------------------+
##   Model Training Code
# +---------------------------------------------------------------------------+
import os
import cv2
import random
import numpy as np
from ultralytics import YOLO
from tensorflow.keras.preprocessing import image
from tensorflow.keras.preprocessing.image import ImageDataGenerator
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Dense, Flatten, Dropout, BatchNormalization
from tensorflow.keras.optimizers import Adamax
from tensorflow.keras.callbacks import EarlyStopping
import tensorflow as tf
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json 

# Function to create directory if it does not exist
def create_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

# Crop the face using YOLO from image path
def crop_face(image_path):
    img = cv2.imread(image_path)
    if img is None:
        print(f"Error: Could not load image {image_path}")
        return None

    # Load YOLOv8 face detection model
    yolo_model = YOLO(r"D:\MSSQL+SACAS\SACAS\model\yolov8n-face.pt")

    # Perform detection
    results = yolo_model(img)
    detections = results[0].boxes.xyxy.cpu().numpy()

    if len(detections) > 0:
        for box in detections:
            x1, y1, x2, y2 = [max(0, int(coord)) for coord in box[:4]]
            face_img = img[y1:y2, x1:x2]
            if face_img.size == 0:
                print(f"Warning: Face cropping failed for {image_path}")
                return None
            
            # Resize to 224x224
            resized_face = cv2.resize(face_img, (224, 224))
            return resized_face

    print(f"No face detected in image: {image_path}")
    return None


# Crop the face using YOLO from image array (for augmented images)
def crop_face_from_array(img_array):
    """Crop face from image array instead of file path"""
    if img_array is None:
        print("Error: Empty image array provided")
        return None

    # Load YOLOv8 face detection model
    yolo_model = YOLO(r"D:\MSSQL+SACAS\SACAS\model\yolov8n-face.pt")

    # Perform detection
    results = yolo_model(img_array)
    detections = results[0].boxes.xyxy.cpu().numpy()

    if len(detections) > 0:
        for box in detections:
            x1, y1, x2, y2 = [max(0, int(coord)) for coord in box[:4]]
            face_img = img_array[y1:y2, x1:x2]
            if face_img.size == 0:
                print("Warning: Face cropping failed from array")
                return None
            
            # Resize to 224x224
            resized_face = cv2.resize(face_img, (224, 224))
            return resized_face

    print("No face detected in image array")
    return None


def format_schedule_for_folder(schedule):
    """
    Convert 'Tuesday 13:23-14:24' to 'Tuesday(13 to 14)'.
    Handles various input formats gracefully.
    """
    try:
        if not schedule or schedule == 'Default_Schedule':
            return 'Default_Schedule'
            
        parts = schedule.split()
        if len(parts) < 2:
            return schedule
            
        day = parts[0]
        time_range = parts[1]
        
        if '-' not in time_range:
            return f"{day}(Unknown)"
            
        start_time, end_time = time_range.split('-')
        start_hour = start_time.split(':')[0] if ':' in start_time else start_time
        end_hour = end_time.split(':')[0] if ':' in end_time else end_time
        
        return f"{day}({start_hour} to {end_hour})"
    except Exception as e:
        print(f"Error formatting schedule '{schedule}': {str(e)}")
        return schedule


def get_course_details_from_post(request):
    """
    Fetch course_name and schedule from POST request.
    """
    if request.method == 'POST':
        try:
            # Handle JSON payload
            data = json.loads(request.body.decode('utf-8'))
            course_name = data.get('course_name', 'Default_Course')
            raw_schedule  = data.get('schedule', 'Default_Schedule')
        except json.JSONDecodeError:
            # Handle application/x-www-form-urlencoded format
            course_name = request.POST.get('course_name', 'Default_Course')
            raw_schedule = request.POST.get('schedule', 'Default_Schedule')
        
        formatted_schedule = format_schedule_for_folder(raw_schedule)
        return course_name, formatted_schedule

def load_images_from_directory(directory, target_size=(224, 224)):
    try:
        images = []
        class_names = sorted(os.listdir(directory))  # Ensure consistent class assignment
        for class_name in class_names:
            class_folder = os.path.join(directory, class_name)
            if os.path.isdir(class_folder):
                for img_name in os.listdir(class_folder):
                    img_path = os.path.join(class_folder, img_name)
                    if img_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                        img = image.load_img(img_path, target_size=target_size)
                        img_array = image.img_to_array(img) / 255.0  # Normalize image
                        images.append(img_array)
        images = np.array(images)
        return images, class_names
    except Exception as e:
        print(f"Error loading images from directory {directory}: {str(e)}")
        return [], []

# GPU configuration
def configure_gpu():
    physical_devices = tf.config.list_physical_devices('GPU')
    if physical_devices:
        try:
            tf.config.experimental.set_memory_growth(physical_devices[0], True)
            print("GPU detected and configured.")
        except Exception as e:
            print(f"Error configuring GPU: {str(e)}")
    else:
        print("No GPU detected. Training will proceed on CPU.")



# Helper function to clear all files in a directory (without deleting the directory itself)
def clear_student_folder(path):
    if os.path.exists(path):
        for file in os.listdir(path):
            file_path = os.path.join(path, file)
            if os.path.isfile(file_path):
                os.remove(file_path)



# 15 images process dataset

def process_dataset(course_name_with_schedule, request):
    # Log the incoming request details
    print(f"Processing dataset for: {course_name_with_schedule}")

    base_path = r"D:\MSSQL+SACAS\SACAS\model\enrollments"
    output_path = r"D:\MSSQL+SACAS\SACAS\model\splitfaces"
    course_output_path = os.path.join(output_path, course_name_with_schedule)  # Dynamic formatting

    # Define train, validation, and test paths
    train_path = os.path.join(course_output_path, "train")
    val_path = os.path.join(course_output_path, "val")
    test_path = os.path.join(course_output_path, "test")

    # Validate if the base course path exists
    course_path = os.path.join(base_path, course_name_with_schedule)
    if not os.path.exists(course_path):
        raise FileNotFoundError(f"Error: Course directory '{course_name_with_schedule}' not found.")


    student_names = sorted(os.listdir(course_path))  # Sorted list for consistent label mapping




    # Create required directories for train, validation, and test datasets
    for path in [train_path, val_path, test_path]:
        create_dir(path)

    try:
        # Process the dataset and create splits
        for student_name in student_names:
            student_folder = os.path.join(course_path, student_name)

            if os.path.isdir(student_folder):
                # Create directories for each student in train/val/test
                for folder in [train_path, val_path, test_path]:
                    create_dir(os.path.join(folder, student_name))

                images = sorted(os.listdir(student_folder))  # Sorted to maintain consistency
                random.shuffle(images)

                # Ensure we have at least 15 images to split correctly
                if len(images) < 15:
                    raise ValueError(f"Not enough images in folder {student_folder}. At least 15 images are required.")

                # Define train, validation, and test splits dynamically
                train_images = images[:9]
                val_images = images[9:12]
                test_images = images[12:15]

                splits = {
                    "train": train_images,
                    "val": val_images,
                    "test": test_images
                }

                # Process images for each split
                for split, split_images in splits.items():
                    for img_name in split_images:
                        img_path = os.path.join(student_folder, img_name)
                        cropped_face = crop_face(img_path)
                        if cropped_face is not None:
                            save_path = os.path.join(
                                {"train": train_path, "val": val_path, "test": test_path}[split],
                                student_name,
                                img_name
                            )
                            cv2.imwrite(save_path, cropped_face)
                            print(f"Saved cropped face to: {save_path}")
        return train_path, val_path, test_path
    except Exception as e:
        raise RuntimeError(f"Error processing dataset: {str(e)}")




# Augmentation setup
def load_datasets_with_augmentation(train_path, val_path, test_path, target_size=(224, 224), batch_size=32):
    train_datagen = ImageDataGenerator(

        rescale=1.0/255.0,
        rotation_range=20,
        width_shift_range=0.2,
        height_shift_range=0.2,
        shear_range=0.2,
        zoom_range=0.2,
        horizontal_flip=True,
        fill_mode="nearest"

    )

    

    val_test_datagen = ImageDataGenerator(rescale=1.0/255.0)

    train_generator = train_datagen.flow_from_directory(
        train_path,
        target_size=target_size,
        batch_size=batch_size,
        class_mode='categorical'
    )

    val_generator = val_test_datagen.flow_from_directory(

        
        val_path,
        target_size=target_size,
        batch_size=batch_size,
        class_mode='categorical'
    )

    test_generator = val_test_datagen.flow_from_directory(
        test_path,
        target_size=target_size,
        batch_size=batch_size,
        class_mode='categorical',
        shuffle=False  # Ensure deterministic results for evaluation
    )

    return train_generator, val_generator, test_generator


def create_model(num_classes):
    """
    Create a ResNet152V2-based model for multi-class classification.
    """
    base_model = tf.keras.applications.ResNet152V2(
        weights='imagenet',
        include_top=False,
        input_shape=(224, 224, 3)
    )
    
    for layer in base_model.layers:  # Last 50 layers unfrozen
        layer.trainable = False

    x = Flatten()(base_model.output)
    x = Dense(1024, activation='relu')(x)
    x = BatchNormalization()(x)
    x = Dropout(0.5)(x)  # Increase dropout to 50%
    output = Dense(num_classes, activation='softmax')(x)
    model = Model(inputs=base_model.input, outputs=output)
    return model


@csrf_exempt
def initiate_training(request):

    if request.method == 'POST':

        try:
            print("Raw request body:", request.body)  # Debug what's being received
            course_name, schedule = get_course_details_from_post(request)
            print(f"Processing training for: {course_name} with schedule: {schedule}")
            course_name_with_schedule = f"{course_name}-{schedule}"
            print(f"Full course path identifier: {course_name_with_schedule}")
          
            if not course_name:
                raise ValueError("Error: Course name not found in the request.")

            # Configure GPU
            configure_gpu()

            train_path, val_path, test_path = process_dataset(course_name_with_schedule, request)

            # Load augmented datasets
            train_generator, val_generator, test_generator = load_datasets_with_augmentation(
                train_path, val_path, test_path
            )

            # Update number of classes
            num_classes = train_generator.num_classes
            print(f"Number of classes: {num_classes}")

            # Create the model
            model = create_model(num_classes)
            model.compile(
                optimizer=Adamax(learning_rate=0.0001),
                loss='categorical_crossentropy',
                metrics=['accuracy']
            )

            # Train the model
            early_stopping = EarlyStopping(
                monitor='val_loss',
                patience=15,
                restore_best_weights=True
            )

            history = model.fit(
                train_generator,
                validation_data=val_generator,
                epochs=25,
                callbacks=[early_stopping]
            )

            # Extract accuracy metrics
            training_accuracy = max(history.history['accuracy']) * 100
            validation_accuracy = max(history.history['val_accuracy']) * 100

            # Evaluate the model
            test_loss, test_acc = model.evaluate(test_generator)
            print(f"Train Accuracy: {training_accuracy:.2f}%")
            print(f"Validation Accuracy: {validation_accuracy:.2f}%")
            print(f"Test Accuracy: {test_acc * 100:.2f}%")

            # Set the path for saving the model
            base_model_dir = r"D:\MSSQL+SACAS\SACAS\model\savedModels"
            model_save_path = os.path.join(base_model_dir, f"{course_name}-{schedule}.keras")

            # Ensure the directory exists
            os.makedirs(os.path.dirname(model_save_path), exist_ok=True)

            # Save the model
            model.save(model_save_path)
            print(f"Model saved at {model_save_path}")
           
            return JsonResponse({
                'status': 'success',
                'message': 'Model trained and saved successfully.',
                'training_accuracy': training_accuracy,
                'validation_accuracy': validation_accuracy,
                'test_accuracy': test_acc * 100
            })

        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

    return JsonResponse({'status': 'error', 'message': 'Invalid request method.'}, status=400)


# +---------------------------------------------------------------------------+
##    Model Prediction Code
# +---------------------------------------------------------------------------+

# import numpy as np
# from tensorflow.keras.preprocessing import image
# from tensorflow.keras.models import load_model
# from PIL import Image
# from ultralytics import YOLO
# import os

# # --- Step 1: Paths ---
# test_image_path = r"C:\Users\HP\Documents\image\WhatsApp Image 2025-05-16 at 10.32.15 PM.jpeg"
# model_path = r"D:\MSSQL+SACAS\SACAS\model\savedModels\Compiler construction-Wednesday(08 to 09).keras"
# specific_train_path = r"D:\MSSQL+SACAS\SACAS\model\splitfaces\Compiler construction-Wednesday(08 to 09)\train"
# yolo_model_path = r"D:\MSSQL+SACAS\SACAS\model\yolov8n-face.pt"

# # --- Step 2: Load Models ---
# model = load_model(model_path)
# yolo_model = YOLO(yolo_model_path)

# # --- Step 3: Detect and Crop Face using YOLO ---
# def detect_and_crop_face(image_path):
#     results = yolo_model(image_path)
#     for result in results:
#         boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2
#         if len(boxes) > 0:
#             x1, y1, x2, y2 = map(int, boxes[0])  # first detected face
#             img = Image.open(image_path)
#             face = img.crop((x1, y1, x2, y2))
#             return face
#     return None

# # --- Step 4: Preprocess Image for CNN ---
# def preprocess_image(img):
#     img = img.resize((224, 224))
#     img_array = image.img_to_array(img)
#     img_array = np.expand_dims(img_array, axis=0)
#     img_array = img_array / 255.0
#     return img_array

# # --- Step 5: Run Prediction ---
# cropped_face = detect_and_crop_face(test_image_path)
# if cropped_face:
#     test_image = preprocess_image(cropped_face)
#     predictions = model.predict(test_image)
#     predicted_class = np.argmax(predictions, axis=1)[0]
#     confidence = predictions[0][predicted_class]
#     print(f"predicted class:{predicted_class}")
#     student_names = sorted(os.listdir(specific_train_path))
#     predicted_student_name = student_names[predicted_class]

#     if confidence >= 0.50:
#         print(f"The predicted student is: {predicted_student_name} (Confidence: {confidence*100:.2f}%)")
#     else:
#         print("This student does not exist in our records.")
# else:
#     print("No face detected in the image.")
