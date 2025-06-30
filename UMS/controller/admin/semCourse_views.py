from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import SemesterCourseForm
# models
from ...models import SemCourses,Semester,Course

# Semester course index
@login_required(login_url='login')
def semesterCourse_index(request):
    Scourses = SemCourses.objects.all()
    return render(request, 'Admin/semCourse/index.html', {'Scourses':Scourses})

# Semester course  create
@login_required(login_url='login')
def semesterCourse_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        form = SemesterCourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester Course added successfully!')
            return redirect('semesterCourse_index')
        else:          
            errors = form.errors.as_data()
            if 'sem_course_id' in errors:
                messages.error(request, 'Semester course Code is required.')
            if 'semester' in errors:
                messages.error(request, 'Semester Name is required.')
            if 'course' in errors:
                messages.error(request, 'Course Name is required.')
            if 'max_students' in errors:
                messages.error(request, 'Max Students is required.')                
            elif SemCourses.objects.filter(sem_course_id='sem_course_id').exists():
                messages.error(request, 'Semester course Code is already exists.')
    else:
        form = SemesterCourseForm()
    Scourses = SemCourses.objects.all()
    semesters = Semester.objects.all()
    courses = Course.objects.all()
    return render(request, 'Admin/semCourse/create.html', {'form': form, 'Scourses': Scourses,'semesters':semesters,'courses':courses})


# Semester course  Show
@login_required(login_url='login')
def semesterCourse_show(request, pk):
    Scourses = get_object_or_404(SemCourses, pk=pk)
    return render(request, 'Admin/semCourse/show.html', {'Scourses': Scourses})




# Semester course Edit
@login_required(login_url='login')
def semesterCourse_edit(request, pk):
    Scourses = get_object_or_404(SemCourses, pk=pk)
    if request.method == 'POST':
        form = SemesterCourseForm(request.POST, instance=Scourses)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester Course details updated successfully.')
            return redirect('semesterCourse_index')
    else:
        form = SemesterCourseForm(instance=Scourses)
    
    semesters = Semester.objects.all()
    courses = Course.objects.all()

    return render(request, 'Admin/semCourse/edit.html', {
        'form': form, 
        'Scourses': Scourses,
        'semesters': semesters,
        'courses': courses
    })




# Semester course  Delete
@login_required(login_url='login')
def semesterCourse_delete(request, pk):
    Scourses = get_object_or_404(SemCourses, pk=pk)
    if request.method == 'POST':
        Scourses.delete()
        messages.success(request, 'Semester Course deleted successfully!')
        return redirect('semesterCourse_index')
    return redirect('semesterCourse_index')