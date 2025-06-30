from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import CourseAssignForm
# models
from ...models import CourseAssign,Faculty,SemCourses,DepartAssign


# AssignCourse index
@login_required(login_url='login')
def Assigncourse_index(request):
    CoursesAssign = CourseAssign.objects.all()
    faculties = DepartAssign.objects.all()
    SemCourse = SemCourses.objects.all()
    return render(request, 'Admin/CoursesAssign/index.html', {'CoursesAssign':CoursesAssign,'faculties':faculties,'SemCourse':SemCourse})


@login_required(login_url='login')
def Assigncourse_create(request):
    if request.method == 'POST':
        day = request.POST.get('day')
        start_time = request.POST.get('start_time')
        end_time = request.POST.get('end_time')
        form = CourseAssignForm(request.POST)

        if form.is_valid():
            # Combine the day and time into the required format
            schedule = f"{day.capitalize()} {start_time}-{end_time}"

            # Save the schedule into the form instance
            course_assign = form.save(commit=False)
            course_assign.schedule = schedule
            course_assign.save()

            messages.success(request, 'Assign Course added successfully!')
            return redirect('Assigncourse_index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = CourseAssignForm()

    faculties = DepartAssign.objects.all()
    SemCourse = SemCourses.objects.all()

    return render(request, 'Admin/CoursesAssign/create.html', {'form': form, 'faculties': faculties, 'SemCourse': SemCourse})



# AssignCourse Show
@login_required(login_url='login')
def Assigncourse_show(request, pk):
    CoursesAssign = get_object_or_404(CourseAssign, pk=pk)
    return render(request, 'Admin/CoursesAssign/show.html', {'CoursesAssign': CoursesAssign})



# AssignCourse Edit
@login_required(login_url='login')
def Assigncourse_edit(request, pk):
    CoursesAssign = get_object_or_404(CourseAssign, pk=pk)
    faculties = DepartAssign.objects.all()
    SemCourse = SemCourses.objects.all()

    # Default values
    initial_day = ''
    start_time = ''
    end_time = ''

    # Parse the schedule string to get day, start_time, end_time
    if CoursesAssign.schedule:
        try:
            # Example: "Monday 10:00-12:00"
            day_part, time_part = CoursesAssign.schedule.split(' ', 1)
            start_time, end_time = time_part.split('-')
            initial_day = day_part.lower()
        except Exception as e:
            # Agar koi parsing error ho jaye toh skip kar do
            pass

    if request.method == 'POST':
        form = CourseAssignForm(request.POST, instance=CoursesAssign)
        if form.is_valid():
            # Recreate schedule string from POST data
            day = request.POST.get('day')
            start = request.POST.get('start_time')
            end = request.POST.get('end_time')
            schedule = f"{day.capitalize()} {start}-{end}"
            
            course_assign = form.save(commit=False)
            course_assign.schedule = schedule
            course_assign.save()

            messages.success(request, 'Course Assign details updated successfully.')
            return redirect('Assigncourse_index')
    else:
        form = CourseAssignForm(instance=CoursesAssign)

    context = {
        'form': form,
        'CoursesAssign': CoursesAssign,
        'faculties': faculties,
        'SemCourse': SemCourse,
        'initial_day': initial_day,
        'start_time': start_time,
        'end_time': end_time,
    }
    return render(request, 'Admin/CoursesAssign/edit.html', context)


# AssignCourse Delete
@login_required(login_url='login')
def Assigncourse_delete(request, pk):
    CoursesAssign = get_object_or_404(CourseAssign, pk=pk)
    if request.method == 'POST':
        CoursesAssign.delete()
        messages.success(request, 'Course Assign deleted successfully!')
        return redirect('Assigncourse_index')
    return redirect('Assigncourse_index')




