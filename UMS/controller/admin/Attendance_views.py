from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# models
from ...models import Attendances,SemCourses

# forms
from ...forms import AttendanceForm

# Index view to list all attendances
@login_required(login_url='login')
def attendance_index(request):
    attendances = Attendances.objects.all()
    page_title = "Attendance | List"
    return render(request, 'admin/attendance/index.html', {'attendances': attendances,'page_title': page_title})

# Create view for new attendance
@login_required(login_url='login')
def attendance_create(request):
    sem_courses = SemCourses.objects.all()
    if request.method == 'POST':
        sem_course_id = request.POST.get('sem_course_id')
        
        if not sem_course_id:
            messages.error(request, "Please select a course.")
            return redirect('attendance_create')
        
        # Check if `sem_course_id` is provided and get the object
        try:
            sem_course = SemCourses.objects.get(id=sem_course_id)
        except SemCourses.DoesNotExist:
            messages.error(request, "The selected course does not exist.")
            return redirect('attendance_create')
        
        form = AttendanceForm(request.POST)
        if form.is_valid():
            attendance = form.save(commit=False)
            attendance.sem_course_id = sem_course
            attendance.save()
            messages.success(request, 'Attendance added successfully!')
            return redirect('attendance_index')
        else:
            for field, errors in form.errors.items():
                label = form.fields[field].label  # Get the label for the field
                for error in errors:
                    messages.error(request, f"{label}: {error}")
    else:
        form = AttendanceForm()

    page_title = "Attendance | Add"
    return render(request, 'admin/attendance/create.html', {
        'form': form,
        'sem_courses': sem_courses,
        'page_title': page_title,
    })
    


# attendance show
@login_required(login_url='login')
def attendance_show(request, id):
    # Use `attendance_id` if that's the correct field
    attendance = get_object_or_404(Attendances, attendance_id=id)
    
    return render(request, 'Admin/attendance/show.html', {'attendance': attendance})



@login_required(login_url='login')
def attendance_edit(request, pk):
    # Get the attendance record by pk
    attendance = get_object_or_404(Attendances, attendance_id=pk)
    sem_courses = SemCourses.objects.all()  # Get all available SemCourses
    
    if request.method == 'POST':
        # Retrieve the updated sem_course_id from the form
        sem_course_id = request.POST.get('sem_course_id')
        
        if not sem_course_id:
            messages.error(request, "Please select a course.")
            return redirect('attendance_edit', pk=attendance.attendance_id)
        
        try:
            sem_course = SemCourses.objects.get(id=sem_course_id)
        except SemCourses.DoesNotExist:
            messages.error(request, "The selected course does not exist.")
            return redirect('attendance_edit', pk=attendance.attendance_id)
        
        # Update the attendance object
        attendance.sem_course_id = sem_course
        attendance.attendance_date = request.POST.get('attendance_date')
        attendance.remarks = request.POST.get('remarks')
        attendance.save()
        
        messages.success(request, 'Attendance updated successfully!')
        return redirect('attendance_index')
    else:
        form = AttendanceForm(instance=attendance)
    
    page_title = "Edit Attendance"
    return render(request, 'admin/attendance/edit.html', {
        'form': form,
        'attendance': attendance,
        'sem_courses': sem_courses,
        'page_title': page_title,
    })




# Delete view for attendance
@login_required(login_url='login')
def attendance_delete(request, pk):
    attendance = get_object_or_404(Attendances, attendance_id=pk)
    if request.method == 'POST':
        attendance.delete()
        return redirect('attendance_index')
    return render(request, 'attendance_confirm_delete.html', {'attendance': attendance})
