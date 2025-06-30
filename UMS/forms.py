from django import forms
from .models import  CustomUser,University, Campus,Department,Program,Course,Faculty,DepartAssign,Student,Semester,SemCourses,CourseAssign,Enrollment,StudentImage,Attendances,StudentAttendance,Camera
from .utils import send_approval_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class RegisterUserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['first_name', 'last_name', 'email', 'user_type', 'status']

    def save(self, commit=True):
        user = super().save(commit=False)
        

        if commit:
            user.save()
            if user.status == 'Approved':  # ✅ Email Only if Approved
                send_approval_email(user)
        
        return user


# university form
class UniversityForm(forms.ModelForm):
    class Meta:
        model = University
        fields = ['uni_id','name', 'location']


# campus form
class CampusForm(forms.ModelForm):
    class Meta:
        model = Campus
        fields = ['campus_id', 'name', 'location', 'university']


# department form
class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['department_id', 'name', 'description', 'campus']


# program form
class ProgramForm(forms.ModelForm):
    class Meta:
        model = Program
        fields = '__all__'


# Course form
class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = '__all__'


# faculty form
class FacultyForm(forms.ModelForm):
    class Meta:
        model = Faculty
        fields = '__all__'


# departAssign form
class departAssignForm(forms.ModelForm):
    class Meta:
        model = DepartAssign
        fields = '__all__'


# students form
class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'


 # Semester  form       
class SemesterForm(forms.ModelForm):
    class Meta:
        model = Semester
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        semester_name = cleaned_data.get('semester_name')
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        is_current = cleaned_data.get('is_current')  # Using is_current to match model

        today = timezone.now().date()

        # Auto-calculate end_date if not provided
        if semester_name and start_date and not end_date:
            if semester_name.lower() == 'summer':
                cleaned_data['end_date'] = start_date + relativedelta(months=2)
            elif semester_name.lower() in ['fall', 'spring']:
                cleaned_data['end_date'] = start_date + relativedelta(months=4)
            else:
                raise ValidationError("Unknown semester name. Please choose Summer, Fall, or Spring.")

        # Basic date validations
        if not semester_name or not start_date or not end_date:
            return cleaned_data

        if start_date < today:
            raise ValidationError("Start date cannot be in the past.")

        if end_date < today:
            raise ValidationError("End date cannot be in the past.")

        if start_date >= end_date:
            raise ValidationError("End date must be after the start date.")

        # Prevent overlapping semesters
        overlapping = Semester.objects.filter(
            start_date__lte=end_date,
            end_date__gte=start_date
        ).exclude(id=self.instance.id if self.instance else None)

        if overlapping.exists():
            raise ValidationError("A semester already exists that overlaps with the selected date range.")

        # Prevent same semester name in same year
        year = start_date.year
        same_semester = Semester.objects.filter(
            semester_name=semester_name,
            start_date__year=year
        ).exclude(id=self.instance.id if self.instance else None)

        if same_semester.exists():
            raise ValidationError(f"A '{semester_name}' semester already exists for the year {year}.")

        # Only one current semester allowed (changed is_active to is_current)
        if is_current:
            current_exists = Semester.objects.filter(
                is_current=True
            ).exclude(id=self.instance.id if self.instance else None)

            if current_exists.exists():
                raise ValidationError("Only one semester can be current at a time. Please make another semester non-current first.")

        # Prevent exact duplicates
        exact_match = Semester.objects.filter(
            semester_name=semester_name,
            start_date=start_date,
            end_date=end_date
        ).exclude(id=self.instance.id if self.instance else None)

        if exact_match.exists():
            raise ValidationError("A semester with the same name and date range already exists.")

        return cleaned_data


# semester course form
class SemesterCourseForm(forms.ModelForm):
    class Meta:
        model = SemCourses
        fields = '__all__'




class CourseAssignForm(forms.ModelForm):
    day = forms.ChoiceField(choices=[
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday')
    ])
    start_time = forms.TimeField()
    end_time = forms.TimeField()

    class Meta:
        model = CourseAssign
        fields = ['sem_course', 'faculty', 'section', 'day', 'start_time', 'end_time']  # Include only relevant fields

    def save(self, commit=True):
        # Get the cleaned data for day, start_time, and end_time
        day = self.cleaned_data['day']
        start_time = self.cleaned_data['start_time']
        end_time = self.cleaned_data['end_time']

        # Combine the day and time into the required format
        schedule = f"{day.capitalize()} {start_time.strftime('%H:%M')}-{end_time.strftime('%H:%M')}"

        # Create an instance of the model but don't save it yet
        course_assign = super().save(commit=False)
        course_assign.schedule = schedule  # Save the combined schedule string

        if commit:
            course_assign.save()

        return course_assign



class EnrollmentForm(forms.ModelForm):
    images = forms.ModelMultipleChoiceField(
        queryset=StudentImage.objects.none(),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Enrollment
        exclude = ['enrollment_status']  # exclude it explicitly

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)

        if student:
            self.fields['images'].queryset = StudentImage.objects.filter(student=student)
            self.fields['student'].queryset = Student.objects.filter(id=student.id)  # ✅ Add this line


# Attendance
class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendances
        fields = ['sem_course_id', 'attendance_date', 'remarks']

    remarks = forms.CharField(
        required=True,
        label="Remarks",
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4})
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)



# Student Attendance
class StudentAttendanceForm(forms.ModelForm):
    class Meta:
        model = StudentAttendance
        fields = ['attendance_status', 'remarks']     


#faculty  camera settings
# class CameraForm(forms.ModelForm):
#     class Meta:
#         model = Camera
#         fields = ['name', 'camera_type', 'ip_address', 'port', 'username', 'password']
#         widgets = {
#             'password': forms.PasswordInput(render_value=True),
#             'camera_type': forms.Select(attrs={'required': 'required'}),
#             # 'camera_type': forms.Select(attrs={'class': 'form-control'}),
#         }

#     def __init__(self, *args, **kwargs):
#         super(CameraForm, self).__init__(*args, **kwargs)
#         for field in self.fields.values():
#             field.required = True
#             field.widget.attrs['required'] = 'required'


class CameraForm(forms.ModelForm):
    class Meta:
        model = Camera
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        camera_type = cleaned_data.get("camera_type")

        if camera_type != 'local':
            if not cleaned_data.get("ip_address"):
                self.add_error('ip_address', "IP address is required for IP/RTSP cameras.")
            if not cleaned_data.get("port"):
                self.add_error('port', "Port is required for IP/RTSP cameras.")

        return cleaned_data