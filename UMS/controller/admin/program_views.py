from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages

# forms
from ...forms import ProgramForm

# models
from ...models import Department,Program


#Program index
@login_required(login_url='login')
def programs_index(request):
    departments = Department.objects.all()
    programs = Program.objects.all()    
    return render(request, 'Admin/program/index.html', {'departments': departments,'programs':programs})


#Program create
@login_required(login_url='login')
def program_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')        
        form = ProgramForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program added successfully!')
            return redirect('programs_index')
        else:
            # Handle form errors here
            errors = form.errors.as_data()
            if 'program_id' in errors:
                messages.error(request, 'Program Code is required.')
            if 'department' in errors:
                messages.error(request, 'Department Name is required.')                         
            if 'name' in errors:
                messages.error(request, 'Program Name is required.')
            if 'duration_year' in errors:
                messages.error(request, 'Duration Year is required.')
            if 'total_credits' in errors:
                messages.error(request, 'Total Credits is required.')
            if 'degree_type' in errors:
                messages.error(request, 'Degree Type is required.')                                             
            if 'program_description' in errors:
                messages.error(request, 'Program Description is required.')
            elif Program.objects.filter(id=id).exists():
                messages.error(request, 'This Program Code already exists.')  
    else:
        form = ProgramForm()
    departments = Department.objects.all()
    programs = Program.objects.all()    
    return render(request, 'Admin/program/create.html', {'form': form, 'departments': departments, 'programs': programs})


#Program Show
@login_required(login_url='login')
def programs_show(request, pk):
    program = get_object_or_404(Program, pk=pk)
    return render(request, 'Admin/program/show.html', {'program': program})



#program edit
@login_required(login_url='login')
def programs_edit(request, pk):
    programs = get_object_or_404(Program, pk=pk)
    
    if request.method == 'POST':
        form = ProgramForm(request.POST, instance=programs)
        if form.is_valid():
            form.save()
            messages.success(request, 'Program details updated successfully.')               
            return redirect('programs_index')
        else:
            # Error messages loop
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")

    else:
        form = ProgramForm(instance=programs)

    departments = Department.objects.all()
    return render(request, 'Admin/program/edit.html', {'form': form, 'programs': programs, 'departments': departments})



#Program Delete
@login_required(login_url='login')
def programs_delete(request, pk):
    program = get_object_or_404(Program, pk=pk)
    if request.method == 'POST':
        program.delete()
        messages.success(request, 'Program deleted successfully!')
        return redirect('programs_index')
    return redirect('programs_index')