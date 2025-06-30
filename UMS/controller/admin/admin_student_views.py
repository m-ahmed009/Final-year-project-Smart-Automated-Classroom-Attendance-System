import os
from django.conf import settings
import shutil
from django.shortcuts import render, get_object_or_404, redirect
from ...models import Student,StudentImage,CustomUser
from ...forms import StudentForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from PIL import Image  # Image validation
from django.core.files.storage import default_storage


# Student list (index page)
@login_required(login_url='login')
def Students_index(request):
    students = Student.objects.all()
    return render(request, 'Admin/student/index.html', {'students': students})



# Student create
# @login_required(login_url='login')
# def Students_create(request):
#     if request.method == 'POST':
#         images = request.FILES.getlist('images')  # Get uploaded images
#         errors = []  # Collect validation errors

#         # Validate if exactly 2 images are uploaded
#         if len(images) != 2:
#             errors.append('Please upload exactly 2 images.')

#         # Validate image dimensions
#         for image in images:
#             try:
#                 img = Image.open(image)
#                 width, height = img.size

#                 if width != 640 or height != 480:
#                     errors.append(f'Image "{image.name}" must be exactly 640x480 pixels.')
#             except Exception as e:
#                 errors.append(f'Error processing image "{image.name}". Please upload a valid image file.')

#         # Show errors if any
#         if errors:
#             for error in errors:
#                 messages.error(request, error)
#             return redirect('Students_create')       

#         # Process student form
#         form = StudentForm(request.POST, request.FILES)
#         if form.is_valid():
#             student = form.save()  # Save student first
            
#             # Create student-specific folder in MEDIA_ROOT
#             student_folder = os.path.join(settings.MEDIA_ROOT, f'students/{student.name}_{student.student_id}')
#             os.makedirs(student_folder, exist_ok=True)

#             # Save images to both file system and database
#             for image in images:
#                 image_path = os.path.join(student_folder, image.name)
#                 with default_storage.open(image_path, 'wb+') as destination:
#                     for chunk in image.chunks():
#                         destination.write(chunk)

#                 # Save image reference in database
#                 StudentImage.objects.create(student=student, image=f'students/{student.name}_{student.student_id}/{image.name}')

#             messages.success(request, 'Student and images added successfully!')
#             return redirect('Students_index')

#         else:
#             # Handle form validation errors
#             for field, error_list in form.errors.items():
#                 for error in error_list:
#                     messages.error(request, error)

#     else:
#         form = StudentForm()

#     users = CustomUser.objects.filter(is_superuser=False, user_type='student', status='approved')
#     return render(request, 'Admin/student/create.html', {'form': form, 'users': users})

from PIL import Image, UnidentifiedImageError
from io import BytesIO
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.files.storage import default_storage
import os
import pillow_heif

pillow_heif.register_heif_opener()

@login_required(login_url='login')
def Students_create(request):
    if request.method == 'POST':
        images = request.FILES.getlist('images')

        if len(images) != 15:
            messages.error(request, 'Please upload exactly 2 images.')
            return redirect('Students_create')

        form = StudentForm(request.POST, request.FILES)
        if form.is_valid():
            student = form.save()

            student_folder = os.path.join(settings.MEDIA_ROOT, f'students/{student.name}_{student.student_id}')
            os.makedirs(student_folder, exist_ok=True)

            for index, image in enumerate(images):
                try:
                    img = Image.open(image)

                    # Convert non-RGB formats to RGB
                    if img.mode in ("RGBA", "P", "LA", "L", "CMYK"):
                        img = img.convert("RGB")

                    # Resize to 640x480 if needed
                    if img.size != (640, 480):
                        img = img.resize((640, 480))

                    # Save image as JPEG to memory
                    buffer = BytesIO()
                    img.save(buffer, format='JPEG', quality=90)
                    image_file = ContentFile(buffer.getvalue())

                    # Give new name with .jpg extension
                    image_name = f'image_{index + 1}.jpg'
                    image_path = os.path.join(student_folder, image_name)

                    # Save to filesystem
                    with default_storage.open(image_path, 'wb+') as destination:
                        destination.write(image_file.read())

                    # Save in DB
                    StudentImage.objects.create(
                        student=student,
                        image=f'students/{student.name}_{student.student_id}/{image_name}'
                    )

                except UnidentifiedImageError:
                    messages.error(request, f"'{image.name}' is not a valid image.")
                    return redirect('Students_create')
                except Exception as e:
                    messages.error(request, f"Error processing image '{image.name}': {str(e)}")
                    return redirect('Students_create')

            messages.success(request, 'Student and images added successfully!')
            return redirect('Students_index')

        else:
            for field, error_list in form.errors.items():
                for error in error_list:
                    messages.error(request, error)

    else:
        form = StudentForm()

    users = CustomUser.objects.filter(is_superuser=False, user_type='student', status='approved')
    return render(request, 'Admin/student/create.html', {'form': form, 'users': users})


# Show student details
@login_required(login_url='login')
def Students_show(request, pk):
    student = get_object_or_404(Student, pk=pk)
    return render(request, 'Admin/student/show.html', {'student': student})

@login_required(login_url='login')
def Students_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    users = CustomUser.objects.filter(is_superuser=False, user_type='student', status='approved')

    # Step 1️⃣: Store old name and id
    old_name = student.name
    old_id = student.student_id

    if request.method == 'POST':
        form = StudentForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()

            # After save, check if folder needs renaming
            new_name = student.name
            new_id = student.student_id

            old_folder = os.path.join(settings.MEDIA_ROOT, f'students/{old_name}_{old_id}')
            new_folder = os.path.join(settings.MEDIA_ROOT, f'students/{new_name}_{new_id}')

            if old_folder != new_folder and os.path.exists(old_folder):
                shutil.move(old_folder, new_folder)  # Rename the folder

                # Update image paths in DB as well
                student_images = StudentImage.objects.filter(student=student)
                for img in student_images:
                    old_img_path = img.image.name.split('/')[-1]  # Just image name
                    img.image.name = f'students/{new_name}_{new_id}/{old_img_path}'
                    img.save()

            #  Handle Image Update
            if 'images' in request.FILES:
                images = request.FILES.getlist('images')

                #  Get updated student folder
                student_folder = os.path.join(settings.MEDIA_ROOT, f'students/{student.name}_{student.student_id}')

                # Delete Old Images from Database and File System
                old_images = StudentImage.objects.filter(student=student)
                for old_image in old_images:
                    image_path = os.path.join(settings.MEDIA_ROOT, old_image.image.name)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                old_images.delete()

                # Save new images
                for image in images:
                    image_path = os.path.join(student_folder, image.name)
                    if not os.path.exists(student_folder):
                        os.makedirs(student_folder)  # In case folder doesn't exist
                    with default_storage.open(image_path, 'wb+') as destination:
                        for chunk in image.chunks():
                            destination.write(chunk)
                    StudentImage.objects.create(student=student, image=f'students/{student.name}_{student.student_id}/{image.name}')

            return redirect('Students_index')
    else:
        form = StudentForm(instance=student)

    return render(request, 'Admin/student/edit.html', {'form': form, 'student': student, 'users': users})



# Delete specific student (Only deletes selected student and its folder)
@login_required(login_url='login')
def Students_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)

    # Get Student Folder Path
    student_folder = os.path.join(settings.MEDIA_ROOT, f'students/{student.name}_{student.student_id}')
    
    #  Delete All Images from Database
    StudentImage.objects.filter(student=student).delete()

    # Delete Student's Image Folder from File System
    if os.path.exists(student_folder):
        shutil.rmtree(student_folder)  # Delete entire folder

    # Delete Student from Database
    student.delete()

    messages.success(request, 'Student and associated images deleted successfully!')
    return redirect('Students_index')
