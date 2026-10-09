from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from . import forms
from .models import CursosLeccion as Leccion, CursosModulo as Modulo

# vista para el login
def login_view(request):
    # si ya inicio sesion lo mandamos al dashboard
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = forms.LoginForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        email = form.cleaned_data['email']
        password = form.cleaned_data['contrasena']
        # Usamos email como username ya que así lo guardamos en el registro
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            form.add_error(None, "Correo o contraseña incorrectos.")
    return render(request, 'login.html', {'form': form})

# vista para registrarse
def register_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')    
    form = forms.RegistroForm(request.POST or None)
    
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user) # iniciamos sesion al tiro
        return redirect('dashboard')
        
    return render(request, 'register.html', {'form': form})

# vista para salir
def logout_view(request):
    logout(request)
    return redirect('login')

# aca va el dashboard, solo entra si estas logueado
@login_required(login_url='login')
def dashboard_view(request):
    usuario = request.user.username
    modulos = Modulo.objects.prefetch_related('cursosleccion_set').order_by('orden', 'id')
    modulos_completados = 0
    modulo_anterior_completo = True

    # sacar el porcentaje de progreso de cada modulo
    for modulo in modulos:
        lecciones = modulo.cursosleccion_set.all()
        total_lecciones = len(lecciones)
        lecciones_completadas = sum(1 for leccion in lecciones if leccion.completada)
        modulo.progreso = int((lecciones_completadas / total_lecciones) * 100) if total_lecciones > 0 else 0
        modulo.esta_completo = (total_lecciones > 0 and lecciones_completadas == total_lecciones)
        modulo.desbloqueado = modulo_anterior_completo
        modulo_anterior_completo = modulo.esta_completo
        if modulo.esta_completo:
            modulos_completados += 1

    total_modulos = len(modulos)
    progreso_general = int((modulos_completados / total_modulos) * 100) if total_modulos > 0 else 0

    # ver en que nivel va
    if progreso_general >= 76: nivel = 'Experto'
    elif progreso_general >= 51: nivel = 'Avanzado'
    elif progreso_general >= 26: nivel = 'Intermedio'
    else: nivel = 'Principiante'
    data = {
        'usuario': usuario,
        'modulos': modulos,
        'progreso_general': progreso_general,
        'nivel': nivel,
    }
    return render(request, 'dashboard.html', data)

# vista para responder cada pregunta
@login_required(login_url='login')
def leccion_view(request, leccion_id):
    leccion = get_object_or_404(Leccion, id=leccion_id)
    form = forms.RespuestaForm(request.POST or None)
    resultado = None

    if request.method == 'POST' and form.is_valid():
        respuesta_es_verdad = (form.cleaned_data['respuesta'] == 'verdad')
        # ver si le achunto
        if respuesta_es_verdad == leccion.es_verdad:
            resultado = 'correcto'
            leccion.completada = True
            leccion.save()
        else:
            resultado = 'incorrecto'

    return render(request, 'leccion.html', {
        'leccion': leccion,
        'form': form,
        'resultado': resultado
    })


def admin_panel_view(request):
    if request.method == 'POST':
        form_type = request.POST.get('form_type')
        object_id = request.POST.get('object_id')
        if form_type == 'modulo':
            instance = get_object_or_404(Modulo, pk=object_id) if object_id else None
            modulo_form = forms.ModuloAdminForm(request.POST, instance=instance)
            leccion_form = forms.LeccionAdminForm()
            if modulo_form.is_valid():
                modulo_form.save()
                messages.success(request, 'Módulo guardado correctamente.')
                return redirect('admin_panel')
        elif form_type == 'leccion':
            instance = get_object_or_404(Leccion, pk=object_id) if object_id else None
            modulo_form = forms.ModuloAdminForm()
            leccion_form = forms.LeccionAdminForm(request.POST, instance=instance)
            if leccion_form.is_valid():
                leccion_form.save()
                messages.success(request, 'Lección guardada correctamente.')
                return redirect('admin_panel')
        else:
            messages.error(request, 'No se pudo identificar el tipo de contenido enviado.')
            return redirect('admin_panel')
    else:
        modulo_id = request.GET.get('editar_modulo')
        leccion_id = request.GET.get('editar_leccion')
        modulo_instance = get_object_or_404(Modulo, pk=modulo_id) if modulo_id else None
        leccion_instance = get_object_or_404(Leccion, pk=leccion_id) if leccion_id else None
        modulo_form = forms.ModuloAdminForm(instance=modulo_instance)
        leccion_form = forms.LeccionAdminForm(instance=leccion_instance)

    return render(request, 'admin_panel.html', {
        'modulo_form': modulo_form,
        'leccion_form': leccion_form,
        'modulos': Modulo.objects.order_by('orden', 'id'),
        'lecciones': Leccion.objects.select_related('modulo').order_by('modulo_id', 'id'),
        'total_modulos': Modulo.objects.count(),
        'total_lecciones': Leccion.objects.count(),
        'editar_modulo': modulo_form.instance.pk,
        'editar_leccion': leccion_form.instance.pk,
    })


@require_POST
def eliminar_contenido_view(request):
    accion = request.POST.get('accion')
    if accion == 'eliminar_modulo':
        modulo = get_object_or_404(Modulo, pk=request.POST.get('modulo_id'))
        if Leccion.objects.filter(modulo_id=modulo.pk).exists():
            messages.error(request, 'No se puede eliminar el módulo mientras tenga lecciones. Elimina o mueve sus lecciones primero.')
        else:
            modulo.delete()
            messages.success(request, 'Módulo eliminado correctamente.')
    elif accion == 'eliminar_leccion':
        leccion = get_object_or_404(Leccion, pk=request.POST.get('leccion_id'))
        leccion.delete()
        messages.success(request, 'Lección eliminada correctamente.')
    else:
        messages.error(request, 'No se pudo identificar el contenido a eliminar.')
    return redirect('admin_panel')
