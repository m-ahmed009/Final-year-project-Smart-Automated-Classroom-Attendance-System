from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import SemesterForm
# models
from ...models import Semester

# Semester index
@login_required(login_url='login')
def semester_index(request):
    Semesters = Semester.objects.all()
    return render(request, 'Admin/semester/index.html', {'Semesters':Semesters,})

# Semester create
@login_required(login_url='login')
def semester_create(request):
    if request.method == 'POST':
        form = SemesterForm(request.POST)
        if form.is_valid():
            new_semester = form.save(commit=False)
            
            # If setting as current, unset any existing current semester
            if new_semester.is_current:
                Semester.objects.filter(is_current=True).update(is_current=False)
            
            new_semester.save()
            messages.success(request, 'Semester added successfully!')
            return redirect('semester_index')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    else:
        form = SemesterForm()

    return render(request, 'Admin/semester/create.html', {'form': form})

# Semester Show
@login_required(login_url='login')
def semester_show(request, pk):
    Semesters = get_object_or_404(Semester, pk=pk)
    return render(request, 'Admin/semester/show.html', {'Semesters': Semesters})

# Semester Edit
@login_required(login_url='login')
def semester_edit(request, pk):
    Semesters = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        form = SemesterForm(request.POST, instance=Semesters)
        if form.is_valid():
            form.save()
            messages.success(request, 'Semester details updated successfully.')               
            return redirect('semester_index')
    else:
        form = SemesterForm(instance=Semesters)
    return render(request, 'Admin/semester/edit.html', {'form': form, 'Semesters': Semesters})

# Semester Delete
@login_required(login_url='login')
def semester_delete(request, pk):
    Semesters = get_object_or_404(Semester, pk=pk)
    if request.method == 'POST':
        Semesters.delete()
        messages.success(request, 'Semester Record deleted successfully!')
        return redirect('semester_index')
    return redirect('semester_index')


# Semester status toggle
@login_required(login_url='login')
def semester_toggle(request, id):
    semester = get_object_or_404(Semester, id=id)
    
    # If trying to activate this semester
    if not semester.is_current:
        # Check if any other semester is already active
        active_semesters = Semester.objects.filter(is_current=True).exclude(id=semester.id)
        if active_semesters.exists():
            messages.error(request, 'Cannot activate this semester. Another semester is already active.')
            return redirect('semester_index')
        
        # Deactivate all other semesters (safety measure)
        Semester.objects.filter(is_current=True).update(is_current=False)
    
    # Toggle the status
    semester.is_current = not semester.is_current
    semester.save()
    
    if semester.is_current:
        messages.success(request, 'Semester activated successfully. All other semesters were deactivated.')
    else:
        messages.success(request, 'Semester deactivated successfully.')
    
    return redirect('semester_index')