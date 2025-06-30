from django.contrib.auth.models import AbstractUser, Group, Permission
from django.db import models
from django.conf import settings
from django.dispatch import receiver
import os
import shutil

# Custom user for users: admin, faculty, student
class CustomUser(AbstractUser):
    unique_id = models.CharField(max_length=10, unique=True, blank=True, null=True)

    USER_TYPE_CHOICES = [
        ('student', 'Student'),
        ('faculty', 'Faculty'),
    ]
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, blank=True, null=True)

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
    ]
    
    # Allow NULL for status
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, blank=True, null=True, default=None
    )
    # Define Email Field Explicitly
    email = models.EmailField(unique=True, blank=False, null=False)

    # Fix reverse accessor conflicts
    groups = models.ManyToManyField(Group, related_name="customuser_groups", blank=True)
    user_permissions = models.ManyToManyField(Permission, related_name="customuser_permissions", blank=True)

    def __str__(self):
        return self.username


    def __str__(self):
        return self.email  # Return email 
    

# university model
class University(models.Model):
    id = models.AutoField(primary_key=True)
    uni_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
    


# campus model
class Campus(models.Model):
    id = models.AutoField(primary_key=True)
    campus_id = models.CharField(max_length=255, unique=True, default='TEMP_ID')  
    university = models.ForeignKey(University, on_delete=models.CASCADE, related_name='campuses')  # <-- Reference id instead of uni_id
    name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)  
    address = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']



# department model
class Department(models.Model):
    id = models.AutoField(primary_key=True)
    department_id = models.CharField(max_length=255, unique=True)
    campus = models.ForeignKey(Campus, on_delete=models.CASCADE, related_name='departments')  # <-- Reference id instead of campus_id
    name = models.CharField(max_length=255)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['id']
    
# program model
class Program(models.Model):
    id = models.AutoField(primary_key=True)
    program_id = models.CharField(max_length=255, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='programs')  # <-- Reference id instead of department_id
    name = models.CharField(max_length=255)
    duration_year = models.PositiveIntegerField()
    total_credits = models.PositiveIntegerField()
    degree_type = models.CharField(max_length=255)
    program_description = models.TextField()
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Meta:
    ordering = ['id']



# course model
class Course(models.Model):
    id = models.AutoField(primary_key=True)
    course_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    course_description = models.TextField()
    program = models.ForeignKey(Program,on_delete=models.CASCADE, related_name='courses')
    credits = models.PositiveIntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']


# Faculty model with approved user relation
class Faculty(models.Model):
    id = models.AutoField(primary_key=True)
    faculty_id = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        limit_choices_to={'user_type': 'faculty', 'status': 'approved'},  # Only approved faculty users
        related_name='faculty_profile'
    )    
    name = models.CharField(max_length=100)
    title = models.CharField(max_length=100)
    email = models.EmailField(max_length=100, unique=True)  # Ensures email is unique
    office = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.name} - {self.title}"
    


# DepartAssign model
class DepartAssign(models.Model):
    id = models.AutoField(primary_key=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE)
    assign_date = models.DateField()
    position = models.CharField(max_length=100)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']


  
# Student Model
class Student(models.Model):
    id = models.AutoField(primary_key=True)
    student_id = models.CharField(max_length=255, unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'user_type': 'student', 'status': 'approved'},
        related_name='student_profile'
    )
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def student_directory(self):
        """ Returns the student's directory path dynamically """
        return os.path.join(settings.MEDIA_ROOT, 'students', f"{self.name}-{self.student_id}")

    def __str__(self):
        return f"{self.name} - {self.student_id}"

# ✅ New Model for Storing Student Images
class StudentImage(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='students/images/')

    def __str__(self):
        return f"{self.student.name} - {self.image.name}"



# Delete student directory if student is deleted
@receiver(models.signals.post_delete, sender=Student)
def delete_student_directory(sender, instance, **kwargs):
    """
    Deletes the student's directory from media/students/ when a student is deleted.
    """
    student_folder = instance.student_directory()
    
    if os.path.exists(student_folder):
        shutil.rmtree(student_folder)  # Deletes the whole folder




# semester model
class Semester(models.Model):
    id = models.AutoField(primary_key=True)    
    semester_name = models.CharField(max_length=100, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return f"{self.semester_name} ({self.start_date} to {self.end_date})"
        

# semester course model
class SemCourses(models.Model):
    id = models.AutoField(primary_key=True)
    sem_course_id = models.CharField(max_length=255, unique=True)
    semester = models.ForeignKey(Semester, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    max_students = models.IntegerField()

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']

def save(self, *args, **kwargs):
        # Print or log the course name for debugging purposes
        if self.course:
            print(self.course.name)  # Access the course name correctly
        super().save(*args, **kwargs)  # Call the original save method    


# CourseAssign  model
class CourseAssign(models.Model):
    id = models.AutoField(primary_key=True)    
    sem_course = models.ForeignKey(SemCourses, on_delete=models.CASCADE)
    faculty = models.ForeignKey(DepartAssign, on_delete=models.CASCADE)
    section = models.CharField(max_length=10, unique=True)
    schedule = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        

# Enrollment model
class Enrollment(models.Model):
    id = models.AutoField(primary_key=True)
    enrollment_date =models.DateTimeField(auto_now_add=True)
    sem_course = models.ForeignKey(SemCourses, on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    images = models.ManyToManyField('StudentImage')  # Link to images uploaded for this enrollment
    enrollment_status = models.CharField(
        max_length=20,
        choices=[('Active', 'Active'), ('Withdrawn', 'Withdrawn')],
        default='Active'
    )    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        constraints = [
            models.UniqueConstraint(fields=['student', 'sem_course'], name='unique_student_semcourse'),
        ]
    
    def __str__(self):
        return f"{self.student.name} - {self.sem_course.course.name}"

    @property
    def course(self):
        """Helper property to access course through sem_course"""
        return self.sem_course.course

    def save(self, *args, **kwargs):
        # Define the base path
        base_dir = os.path.join(settings.BASE_DIR, 'model/enrollments')
        
        # Ensure base directory exists
        os.makedirs(base_dir, exist_ok=True)

        # Get course and schedule
        course = self.sem_course.course
        course_assign = CourseAssign.objects.filter(sem_course=self.sem_course).first()
        schedule = course_assign.schedule if course_assign else 'NoSchedule'

        # Format the schedule for folder name
        try:
            day, time_range = schedule.split(' ')
            start_time, end_time = time_range.split('-')
            start_hour = start_time.split(':')[0]  # Get hour from start time
            end_hour = end_time.split(':')[0]      # Get hour from end time
            safe_schedule = f"{day}({start_hour} to {end_hour})"
        except Exception as e:
            safe_schedule = "UnknownSchedule"
            print(f"Error formatting schedule: {e}")

        # Create folder paths
        course_folder = os.path.join(base_dir, f'{course.name}-{safe_schedule}')
        student_folder = os.path.join(course_folder, f'{self.student.name}({self.student.student_id})')

        # Create directories if they don't exist
        os.makedirs(course_folder, exist_ok=True)
        os.makedirs(student_folder, exist_ok=True)

        # Copy student images
        for student_image in self.student.images.all():
            source_path = student_image.image.path
            destination_path = os.path.join(student_folder, os.path.basename(source_path))
            if not os.path.exists(destination_path):
                shutil.copy(source_path, destination_path)

        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        # Get course info before deletion
        course = self.sem_course.course
        course_assign = CourseAssign.objects.filter(sem_course=self.sem_course).first()
        schedule = course_assign.schedule if course_assign else 'NoSchedule'
        
        try:
            # Format schedule for folder name
            day, time_range = schedule.split(' ')
            start_time, end_time = time_range.split('-')
            start_hour = start_time.split(':')[0]
            end_hour = end_time.split(':')[0]
            safe_schedule = f"{day}({start_hour} to {end_hour})"
        except Exception:
            safe_schedule = "UnknownSchedule"

        # Define paths
        base_dir = os.path.join(settings.BASE_DIR, 'model/enrollments')
        course_folder = os.path.join(base_dir, f'{course.name}-{safe_schedule}')
        student_folder = os.path.join(course_folder, f'{self.student.name}({self.student.student_id})')

        # Delete student folder if exists
        if os.path.exists(student_folder):
            try:
                shutil.rmtree(student_folder)
            except Exception as e:
                print(f"Error deleting student folder: {e}")

        # Delete course folder if empty
        if os.path.exists(course_folder) and not os.listdir(course_folder):
            try:
                shutil.rmtree(course_folder)
            except Exception as e:
                print(f"Error deleting course folder: {e}")

        super().delete(*args, **kwargs)


# Attendance model
class Attendances(models.Model):   
    attendance_id = models.AutoField(primary_key=True)  # Primary key
    sem_course_id = models.ForeignKey('SemCourses', on_delete=models.CASCADE)  # Foreign key to SemCourses
    attendance_date = models.DateField()  # Date of attendance
    remarks = models.TextField(blank=True, null=True)  # Additional remarks, optional
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True) 



# Student Attendance model
class StudentAttendance(models.Model):
    stud_attendance_id = models.AutoField(primary_key=True)  # Primary key
    enrollment_id = models.ForeignKey('Enrollment', on_delete=models.CASCADE)  # Foreign key to Enrollment
    attendance_id = models.ForeignKey(Attendances, on_delete=models.CASCADE)  # Foreign key to Attendance
    remarks = models.TextField(blank=True, null=True)  # Additional remarks, optional
    attendance_status = models.CharField(max_length=20)  # Update max_length to 1
    attendance_date = models.DateField()
    student_name = models.CharField(max_length=255, blank=True)
    course_name = models.CharField(max_length=255, blank=True)
    is_mark = models.BooleanField(default=False)      
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Fill student name from enrollment
        if self.enrollment_id and self.enrollment_id.student:
            self.student_name = self.enrollment_id.student.name

        # Fill course name from enrollment → sem_course → course
        if self.enrollment_id and self.enrollment_id.sem_course and self.enrollment_id.sem_course.course:
            self.course_name = self.enrollment_id.sem_course.course.name

        super(StudentAttendance, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.student_name} - {self.course_name} - {self.attendance_status}"
    

# camera model
# class Camera(models.Model):
#     name = models.CharField(max_length=100)
#     ip_address = models.CharField(max_length=100)
#     port = models.IntegerField(default=80)
#     username = models.CharField(max_length=100, blank=True, null=True)
#     password = models.CharField(max_length=100, blank=True, null=True)
#     is_active = models.BooleanField(default=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     def __str__(self):
#         return f"{self.name} ({self.ip_address})"

class Camera(models.Model):
    CAMERA_TYPE_CHOICES = [
        ('local', 'Local '),
        ('ip',    'DroidCam'),
        ('rtsp',  'RTSP stream '),
    ]

    name = models.CharField(max_length=100)
    camera_type = models.CharField(max_length=10, choices=CAMERA_TYPE_CHOICES, default='local')
    ip_address = models.CharField(max_length=100, blank=True, null=True)
    port = models.IntegerField(default=80, blank=True, null=True)
    username = models.CharField(max_length=100, blank=True, null=True)
    password = models.CharField(max_length=100, blank=True, null=True)
    endpoint = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
         return f"{self.name} ({self.camera_type})"
