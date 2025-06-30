from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
# forms
from ...forms import UniversityForm
# models
from ...models import University


# university views

#university index page
@login_required(login_url='login')
def university_index(request):
    universities = University.objects.all()
    page_title = "University | List"
    return render(request, 'Admin/university/index.html', {'universities': universities, 'page_title': page_title})

# university create
@login_required(login_url='login')
def university_create(request):
    if request.method == "POST":
        id = request.POST.get('id')
        form = UniversityForm(request.POST)

        # Check if the University ID already exists
        if id and University.objects.filter(id=id).exists():
            messages.error(request, 'This University Code already exists.')
        elif form.is_valid():
            form.save()
            messages.success(request, 'University added successfully!')
            return redirect('university_index')
        else:
            # Handle form validation errors
            errors = form.errors.as_data()
            if 'uni_id' in errors:
                messages.error(request, 'University Code field is required.')
            if 'name' in errors:
                messages.error(request, 'University Name field is required.')
            if 'location' in errors:
                messages.error(request, 'Location field is required.')
    else:
        form = UniversityForm()
    
    page_title = "University | Add"
    return render(request, 'Admin/university/create.html', {'form': form, 'page_title': page_title})


# university show
@login_required(login_url='login')
def university_show(request, pk):
    university = get_object_or_404(University, pk=pk)
    page_title = "University | Show"
    return render(request, 'Admin/university/show.html', {'university': university,'page_title': page_title})


# university edit logic
@login_required(login_url='login')
def university_edit(request, pk):
    university = get_object_or_404(University, pk=pk)
    
    if request.method == 'POST':
        form = UniversityForm(request.POST, instance=university)
        if form.is_valid():
            form.save()
            messages.success(request, 'University details updated successfully.')
            return redirect('university_index')
    else:
        form = UniversityForm(instance=university)
    
    return render(request, 'Admin/university/edit.html', {'form': form, 'university': university})



#university delete
@login_required(login_url='login')
def university_delete(request, pk):
    university = get_object_or_404(University, pk=pk)
    if request.method == 'POST':
        university.delete()
        messages.success(request, 'University deleted successfully!')
        return redirect('university_index')
    return redirect('university_index')