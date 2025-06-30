from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import CampusForm

# models
from ...models import Campus,University

# campus index
@login_required(login_url='login')
def campus_index(request):
    campuses = Campus.objects.all()
    page_title = 'Campus | List'
    return render(request, 'admin/campus/index.html', {'campuses': campuses,'page_title':page_title})

# campus create
@login_required(login_url='login')
def campus_create(request):
    if request.method == 'POST':
        id = request.POST.get('id')        
        form = CampusForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus added successfully!')
            return redirect('campus_index')
        else:
            errors = form.errors.as_data()
            if  'campus_id' in errors:
                messages.error(request, 'Campus Code is required.')
            if 'university' in errors:
                messages.error(request, 'University Name is required.')                         
            if 'name' in errors:
                messages.error(request, 'Campus Name is required.')
            if 'location' in errors:
                messages.error(request, ' Campus Location is required.')
            elif Campus.objects.filter(id=id).exists():
                messages.error(request, 'This University Code already exists.')
    else:

        form = CampusForm()
    universities = University.objects.all()
    page_title = 'Campus | Add'
    return render(request, 'admin/campus/create.html', {'form': form,'universities':universities,'page_title':page_title})


# campus show
@login_required(login_url='login')
def campus_show(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    return render(request, 'admin/campus/show.html', {'campus': campus})

# campus edit
@login_required(login_url='login')
def campus_edit(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        form = CampusForm(request.POST, instance=campus)
        if form.is_valid():
            form.save()
            messages.success(request, 'Campus details updated successfully.')            
            return redirect('campus_index')
    else:
        form = CampusForm(instance=campus)
    universities = University.objects.all()
    return render(request, 'admin/campus/edit.html', {'form': form,'campus':campus,'universities':universities})

# campus delete
@login_required(login_url='login')
def campus_delete(request, pk):
    campus = get_object_or_404(Campus, pk=pk)
    if request.method == 'POST':
        campus.delete()
        messages.success(request, 'Campus deleted successfully!')
        return redirect('campus_index')
    
    return render(request, 'campus/confirm_delete.html', {'campus': campus})