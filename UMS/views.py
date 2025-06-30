from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.views import View
from .models import CustomUser,Department,Campus,Program
from .forms import RegisterUserForm
from django.views.decorators.cache import never_cache, cache_control
from django.contrib.auth import logout
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.forms import SetPasswordForm
from UMS.utils import send_reset_password_email  # Import from utils.py
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.core.paginator import Paginator




# Return Home Page
def home(request):
    return render(request, 'home.html')


# Define Login page for users (admin,faculty,student)
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            request.session.flush()  # ✅ Purana session clear kar do
            login(request, user)  # ✅ Naya user login kar do

            # ✅ Alag-alag session keys har user ke liye
            if user.is_superuser:
                request.session["session_admin"] = user.id
                print(f"✅ Admin session set: {request.session['session_admin']}")
                return redirect(reverse("admin_dashboard"))

            elif user.user_type == "student":
                request.session["session_student"] = user.id
                print(f"✅ Student session set: {request.session['session_student']}")
                return redirect(reverse("student_dashboard"))

            elif user.user_type == "faculty":
                request.session["session_faculty"] = user.id
                print(f"✅ Faculty session set: {request.session['session_faculty']}")
                return redirect(reverse("faculty_dashboard"))

        return render(request, 'login.html', {'error': 'Invalid Credentials'})

    return render(request, 'login.html')




# Return Admin Dashboard
@login_required
def admin_dashboard(request):
    stored_session_user_id = request.session.get("session_admin")

    print(f"🔍 Admin Dashboard - Expected: {request.user.id}, Found: {stored_session_user_id}")

    if stored_session_user_id is None or stored_session_user_id != request.user.id:
        messages.warning(request, "Session expired! Refreshing session...")
        request.session["session_admin"] = request.user.id  # ✅ Refresh session instead of logout
    
    users = CustomUser.objects.filter(is_superuser=False)
    total_users = users.count()  # Total number of users excluding superusers
    student_users = CustomUser.objects.filter(user_type='student').count()
    faculty_users = CustomUser.objects.filter(user_type='faculty').count()
    departments = Department.objects.filter().count()
    programs = Program.objects.filter().count()
    campuses = Campus.objects.filter().count()         
    

    form = RegisterUserForm()

    return render(request, 'Admin/dashboard.html', {
        'student_users': student_users,
        'faculty_users': faculty_users,
        'form': form,
        'departments':departments,
        'programs':programs,
        'users':users,
        'campuses':campuses,
        'total_users':total_users
    })


#logout for users(admin,faculty and student)

def Logout(request):
    request.session.flush()  # ✅ Pura session clear karna zaroori hai
    logout(request)
    return redirect("login")





# email page where user inputs the email for password reset
def request_password_reset(request):
    """ Handles user password reset request """
    if request.method == "POST":
        email = request.POST.get("email")
        
        if not email:
            return render(request, "resetpassword.html", {"error": "Email is required."})

        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            return render(request, "resetpassword.html", {"error": "Invalid email address."})

        # Send reset email
        send_reset_password_email(user, request)

        return redirect("password_reset_done")

    return render(request, "resetpassword.html")



#when the password has sent at email,then msg will be render
class CustomPasswordResetDoneView(View):
    """ View to show success message after email is sent """
    def get(self, request, *args, **kwargs):
        messages.success(request, "Password reset email has been sent successfully.")
        return redirect("login")


#after the email send ,click on url then render the page of password reset confirm 
#where user enter the new password 2 times
def password_reset_confirm(request, uidb64, token):
    """ Handles password reset confirmation """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = CustomUser.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
        messages.error(request, "Invalid reset link.")
        return redirect("password_reset")

    if not default_token_generator.check_token(user, token):
        messages.error(request, "Invalid or expired reset link.")
        return redirect("password_reset")

    if request.method == "POST":
        form = SetPasswordForm(user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Password reset successful. You can now log in.")
            return redirect("login")
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = SetPasswordForm(user)

    return render(request, "password_reset_confirm.html", {"form": form})


#when the password reset then success message renders
def custom_password_reset_complete(request):
    """ Handles final step after password reset """
    messages.success(request, "Your password has been reset successfully!")
    return redirect("login")