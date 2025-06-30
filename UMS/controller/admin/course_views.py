from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import CourseForm
# models
from ...models import Program,Course


# Course index
@login_required(login_url='login')
def course_index(request):
    programs = Program.objects.all()
    courses = Course.objects.all()
    return render(request, 'Admin/course/index.html', {'programs':programs,'courses':courses})

# Course create
@login_required(login_url='login')
def course_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')        
        form = CourseForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course added successfully!')
            return redirect('course_index')
        else:
            # Handle form errors here
            errors = form.errors.as_data()
            if  'course_id' in errors:
                messages.error(request, 'Course Code is required.')
            if 'program' in errors:
                messages.error(request, 'Program Name is required.')                         
            if 'name' in errors:
                messages.error(request, 'Course Name is required.')
            if 'credits' in errors:
                messages.error(request, ' Credits is required.')                                            
            if 'course_description' in errors:
                messages.error(request, 'Course Description is required.')
            elif Course.objects.filter(id=id).exists():
                messages.error(request, 'This Course Code already exists.')  
    else:
        form = CourseForm()
    courses = Course.objects.all()
    programs = Program.objects.all()    
    return render(request, 'Admin/course/create.html', {'form': form, 'courses': courses, 'programs': programs})


# Course Show
@login_required(login_url='login')
def course_show(request, pk):
    course = get_object_or_404(Course, pk=pk)
    return render(request, 'Admin/course/show.html', {'course': course})

# Course Edit
@login_required(login_url='login')
def course_edit(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, 'Course details updated successfully.')               
            return redirect('course_index')
    else:
        form = CourseForm(instance=course)
    programs = Program.objects.all()
    return render(request, 'Admin/course/edit.html', {'form': form, 'course': course,'programs':programs})

# Course Delete
@login_required(login_url='login')
def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully!')
        return redirect('course_index')
    return redirect('course_index')