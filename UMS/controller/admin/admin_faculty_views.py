from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import CourseForm,FacultyForm

# models
from ...models import Program,Course,Faculty,CustomUser


# Faculty index
@login_required(login_url='login')
def faculty_index(request):
    users = CustomUser.objects.filter(is_superuser=False, user_type='faculty', status='approved')
    faculties = Faculty.objects.all()
    return render(request, 'Admin/faculty/index.html', {'users': users, 'faculties': faculties})



# Faculty create
@login_required(login_url='login')
def faculty_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')
        users_id = request.POST.get('user')

        form = FacultyForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Faculty added successfully!')
            return redirect('faculty_index')
        else:
            errors = form.errors.as_data()
            
            if Faculty.objects.filter(id=id).exists():
                messages.error(request, 'This Faculty Code already exists.')
            
            if users_id and Faculty.objects.filter(user_id=int(users_id)).exists():
                messages.error(request, 'This User is already associated with a faculty.')

            if 'name' in errors:
                messages.error(request, 'Faculty Name is required.')
            if 'title' in errors:
                messages.error(request, 'Title is required.')
            if 'email' in errors:
                messages.error(request, 'Email is required.')
            if 'office' in errors:
                messages.error(request, 'Office is required.')

    else:
        form = FacultyForm()

    users = CustomUser.objects.filter(is_superuser=False, user_type='faculty', status='approved')
    return render(request, 'Admin/faculty/create.html', {'form': form, 'users': users})


# Faculty Show
@login_required(login_url='login')
def faculty_show(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    return render(request, 'Admin/faculty/show.html', {'faculty': faculty})

# Faculty Edit
@login_required(login_url='login')
def faculty_edit(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    users = CustomUser.objects.filter(is_superuser=False, user_type='faculty', status='approved')

    if request.method == 'POST':
        form = FacultyForm(request.POST, instance=faculty)
        if form.is_valid():
            form.save()
            messages.success(request, 'Faculty details updated successfully.')
            return redirect('faculty_index')
    else:
        form = FacultyForm(instance=faculty)

    return render(request, 'Admin/faculty/edit.html', {'form': form, 'faculty': faculty, 'users': users})  # Pass users


# Faculty Delete
@login_required(login_url='login')
def faculty_delete(request, pk):
    faculty = get_object_or_404(Faculty, pk=pk)
    if request.method == 'POST':
        faculty.delete()
        messages.success(request, 'Faculty deleted successfully!')
        return redirect('faculty_index')
    return redirect('faculty_index')