
from django.contrib import messages
import random,string
from ...utils import send_approval_email
from django.utils.crypto import get_random_string
from django.shortcuts import render, redirect,get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password

# forms
from ...forms import RegisterUserForm
# models
from ...models import CustomUser


"""
Users | Start
"""

#user index page
@login_required
def user_index(request):
    student_users = CustomUser.objects.filter(user_type='student')
    faculty_users = CustomUser.objects.filter(user_type='faculty')
    form = RegisterUserForm()
    
    return render(request, 'admin/users/index.html', {
        'student_users': student_users,  
        'faculty_users': faculty_users, 
        'form': form
    })



# Generate Unique Username
def generate_username(first_name):
    while True:
        unique_id = get_random_string(length=5, allowed_chars='0123456789')  # 5-digit unique ID
        username = f"{first_name.lower()}{unique_id}"

        # Ensure unique_id is actually unique in the database
        if not CustomUser.objects.filter(unique_id=unique_id).exists():
            return username, unique_id

# Generate Random Password
def generate_random_password():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=10))

# register user
def register_user(request):
    if request.method == "POST":
        form = RegisterUserForm(request.POST)
        if form.is_valid():
            if CustomUser.objects.filter(email=form.cleaned_data['email']).exists():
                messages.error(request, "User with this email already exists.")
                return render(request, "admin/users/create.html", {"form": form})

            user = form.save(commit=False)
            user.username, user.unique_id = generate_username(user.first_name)
            random_password = generate_random_password()
            user.password = make_password(random_password)
            
            try:
                user.save()
                if user.status == "approved":
                    send_approval_email(user, random_password)
                    messages.success(request, "Email send successfully.")
                return redirect('user_index')
            except Exception as e:
                messages.error(request, f"Error saving user: {e}")
        
    else:
        form = RegisterUserForm()

    
    return render(request, "admin/users/create.html", {"form": form})


# approve user
def approve_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    print(user)

    # Generate Username & Unique ID
    user.username, user.unique_id = generate_username(user.first_name)
    print(f"✅ Generated Username: {user.username}, Unique ID: {user.unique_id}") 

    # Generate & Hash Password
    random_password = generate_random_password()
    user.password = make_password(random_password)
    print(f"✅ Generated Password (Hashed): {user.password}") 

    # Update status to approved
    user.status = "approved"  # Ensure status is updated
    user.save()  # Save changes


    print(f"User Status: {user.status}")  # Debugging step

    # Send email if approved
    if user.status == "approved":
        send_approval_email(user, random_password)
        messages.success(request, "Email sent successfully")
        print("✅ Approval Email Sent!")  # Debugging confirmation

    return redirect('user_index')


#delete users
@login_required
def delete_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.delete()
    messages.success(request, "User successfully deleted.")
    return redirect('user_index')


"""
Users | End
"""