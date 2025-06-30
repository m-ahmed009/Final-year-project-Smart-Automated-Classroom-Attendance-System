from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import DepartmentForm

# models
from ...models import Campus,Department


#department index
@login_required(login_url='login')
def department_index(request):
    departments = Department.objects.all()
    return render(request, 'Admin/department/index.html', {'departments': departments})


#department create
@login_required(login_url='login')
def department_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')    
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department Added successfully!')            
            return redirect('department_index')
        else:
            # Handle form errors here
            errors = form.errors.as_data()
            if 'department_id' in errors:
                messages.error(request, 'Department Code is required.')
            if 'campus' in errors:
                messages.error(request, 'Campus Name is required.')                         
            if 'name' in errors:
                messages.error(request, 'Department Name is required.')
            if 'description' in errors:
                messages.error(request, 'Department Description is required.')
            elif Department.objects.filter(id=id).exists():
                messages.error(request, 'This Department Code already exists.')                
    else:
        form = DepartmentForm()
    campuses = Campus.objects.all()
    departments= Department.objects.all()
    page_title = 'Department | Add'        
    return render(request, 'Admin/department/create.html', {'form': form,'campuses':campuses,'page_title':page_title,'departments':departments})



#department Show
@login_required(login_url='login')
def department_show(request, pk):
    department = get_object_or_404(Department, pk=pk)
    return render(request, 'Admin/department/show.html', {'department': department})


#department Edit
@login_required(login_url='login')
def department_edit(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department details updated successfully.')               
            return redirect('department_index')
    else:
        form = DepartmentForm(instance=department)
    campuses = Campus.objects.all()
    return render(request, 'Admin/department/edit.html', {'form': form, 'department': department,'campuses':campuses})



#department Delete
@login_required(login_url='login')
def department_delete(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, 'Department deleted successfully!')
        return redirect('department_index')
    return redirect('department_index')
