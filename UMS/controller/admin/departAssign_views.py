from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import CourseForm,departAssignForm

# models
from ...models import Department,Program,Faculty,DepartAssign

# departAssign index
@login_required(login_url='login')
def departAssign_index(request):
    departassigns = DepartAssign.objects.all()
    faculties = Faculty.objects.all()
    return render(request, 'Admin/departAssign/index.html', {'departassigns':departassigns,'faculties':faculties})

# departAssign create
@login_required(login_url='login')
def departAssign_create(request):
    if request.method == 'POST':
        form = departAssignForm(request.POST)
        if form.is_valid():
            department = form.cleaned_data['department']
            faculty = form.cleaned_data['faculty']
            
            # Check if the department is already assigned to the same faculty
            if DepartAssign.objects.filter(department=department, faculty=faculty).exists():
                messages.error(request, 'This department is already assigned to this faculty.')
                return redirect('departAssign_create')
            
            form.save()
            messages.success(request, 'Department Assign added successfully!')
            return redirect('departAssign_index')
        else:
            errors = form.errors.as_data()
            if 'department' in errors:
                messages.error(request, 'Department Name is required.')
            if 'faculty' in errors:
                messages.error(request, 'Faculty Name is required.')
            if 'assign_date' in errors:
                messages.error(request, 'Assign Date is required.')
            if 'position' in errors:
                messages.error(request, 'Position is required.')
    else:
        form = departAssignForm()

    departments = Department.objects.all()
    faculties = Faculty.objects.all()
    return render(request, 'Admin/departAssign/create.html', {'form': form, 'departments': departments, 'faculties': faculties})


# departAssign Show
@login_required(login_url='login')
def departAssign_show(request, pk):
    assign = get_object_or_404(DepartAssign, pk=pk)
    return render(request, 'Admin/departAssign/show.html', {'assign': assign})



# departAssign Edit
@login_required(login_url='login')
def departAssign_edit(request, pk):
    assign = get_object_or_404(DepartAssign, id=pk)  # Fetch record
    if request.method == 'POST':
        form = departAssignForm(request.POST, instance=assign)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department details updated successfully.')               
            return redirect('departAssign_index')  # Redirect after saving
    else:
        form = departAssignForm(instance=assign)

    # Fetch department & faculty data for dropdowns
    departments = Department.objects.all()
    faculties = Faculty.objects.all()

    return render(request, 'Admin/departAssign/edit.html', {
        'form': form,
        'assign': assign,
        'departments': departments,
        'faculties': faculties
    })



# departAssign Delete
@login_required(login_url='login')
def departAssign_delete(request, pk):
    departassigns = get_object_or_404(DepartAssign, pk=pk)
    if request.method == 'POST':
        departassigns.delete()
        messages.success(request, 'Record deleted successfully!')
        return redirect('departAssign_index')
    return redirect('departAssign_index')