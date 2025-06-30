from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.contrib import messages

# forms
from ...forms import CameraForm

# models
from ...models import Camera


@login_required
def settings_index(request):

    return render(request, "faculty/settings/index.html")

@login_required(login_url='login')
def camera_settings(request):
    cameras = Camera.objects.all()
    
    if request.method == 'POST':
        form = CameraForm(request.POST)
        if form.is_valid():
            camera = form.save(commit=False)

            if camera.camera_type == 'local':
                camera.device_index = 0  # Default USB webcam
                # Clear fields that are not needed for local camera
                camera.ip_address = None
                camera.port = None
                camera.username = None
                camera.password = None
                camera.endpoint = None

            camera.save()
            messages.success(request, 'Camera added successfully!')
            return redirect('camera_settings')
        else:
            errors = form.errors.as_data()
            if 'name' in errors:
                messages.error(request, 'Camera Name is required.')
            if 'ip_address' in errors:
                messages.error(request, 'IP Address is required.')
            if 'port' in errors:
                messages.error(request, 'Port number is required.')
            if 'username' in errors:
                messages.error(request, 'Username is required.')
            if 'password' in errors:
                messages.error(request, 'Password is required.')
            if 'is_active' in errors:
                messages.error(request, 'Active status is required.')

    else:
        form = CameraForm()

    return render(request, 'faculty/settings/camera_settings.html', {
        'cameras': cameras,
        'form': form
    })

@login_required
def get_camera_data(request, pk):
    try:
        camera = Camera.objects.get(pk=pk)
        data = {
            'id': camera.id,
            'name': camera.name,
            'ip_address': camera.ip_address,
            'port': camera.port,
            'username': camera.username,
            'password': '',  # Optional: don't send password for security, or send masked value
        }
        return JsonResponse(data)
    except Camera.DoesNotExist:
        return JsonResponse({'error': 'Camera not found'}, status=404)

@login_required
def update_camera(request, pk):
    camera = Camera.objects.get(pk=pk)
    if request.method == 'POST':
        form = CameraForm(request.POST, instance=camera)
        if form.is_valid():
            form.save()
            return JsonResponse({'success': True, 'message': 'Camera updated successfully.'})
        else:
            return JsonResponse({'success': False, 'message': 'Invalid data submitted.'})
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def delete_camera(request, pk):
    if request.method == 'POST':
        camera = get_object_or_404(Camera, pk=pk)
        camera.delete()
        return redirect('camera_settings')
    return redirect('camera_settings')


# for active camera
@login_required
def get_active_camera(request):
    camera = Camera.objects.filter(is_active=True).first()
    if camera:
        data = {
            'name': camera.name,
            'ip_address': camera.ip_address,
            'port': camera.port,
            'username': camera.username,
            'password': camera.password,
        }
        return JsonResponse(data)
    return JsonResponse({}, status=404)



@csrf_exempt
@login_required
def toggle_camera_status(request, pk):
    if request.method == 'POST':
        camera = get_object_or_404(Camera, pk=pk)
        camera.is_active = not camera.is_active
        camera.save()
        return JsonResponse({'message': f"Camera {'activated' if camera.is_active else 'deactivated'}."})
    return JsonResponse({'error': 'Invalid request'}, status=400)