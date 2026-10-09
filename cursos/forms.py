from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import CursosLeccion, CursosModulo

# form para iniciar sesion
class LoginForm(forms.Form):
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ejemplo@correo.com'})
    )
    contrasena = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': '********'})
    )

# form para el registro de los profes o papas (solo pide correo y pass)
class RegistroForm(UserCreationForm):
    username = None # ocultamos el username porque usaremos el correo
    email = forms.EmailField(
        label="Correo",
        widget=forms.EmailInput(attrs={'class': 'form-input', 'placeholder': 'ejemplo@correo.com'})
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("email",) # la pass la pone django automatico

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # aca le pongo la clase de css a todos los inputs para que se vean bien
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-input'})

    def clean_email(self):
        # validar que el correo termine en algo valido
        email = self.cleaned_data.get('email')
        if email:
            dominios = (".com", ".cl", ".net", ".org", ".edu")
            if not email.endswith(dominios):
                raise forms.ValidationError("Usa un correo valido por favor (.com, .cl)")
        
        # revisar si ya existe alguien con este correo
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo ya está registrado.")
            
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.username = user.email # guardamos el correo en el username para que django no reclame
        if commit:
            user.save()
        return user

# form para responder las lecciones
class RespuestaForm(forms.Form):
    OPCIONES = [
        ('verdad', 'Verdad'),
        ('mito', 'Mito'),
    ]
    respuesta = forms.ChoiceField(
        choices=OPCIONES,
        widget=forms.RadioSelect,
        label="¿Mito o Verdad?"
    )


class ModuloAdminForm(forms.ModelForm):
    class Meta:
        model = CursosModulo
        fields = ("titulo", "descripcion", "orden")
        labels = {
            "titulo": "Título",
            "descripcion": "Descripción",
            "orden": "Posición en la ruta",
        }
        help_texts = {
            "orden": "Número que indica cuándo aparece este módulo. Por ejemplo: 1 va primero, 2 va después.",
        }
        widgets = {
            "titulo": forms.TextInput(attrs={"class": "admin-control"}),
            "descripcion": forms.Textarea(attrs={"class": "admin-control", "rows": 3}),
            "orden": forms.NumberInput(attrs={"class": "admin-control", "min": 1}),
        }

    def clean_orden(self):
        orden = self.cleaned_data["orden"]
        if orden < 1:
            raise forms.ValidationError("El orden del módulo debe ser mayor que cero.")
        return orden

    def save(self, commit=True):
        modulo = super().save(commit=False)
        if self.instance._state.adding:
            modulo.icono = "fa-solid fa-puzzle-piece"
        if commit:
            modulo.save()
        return modulo


class LeccionAdminForm(forms.ModelForm):
    class Meta:
        model = CursosLeccion
        fields = ("modulo", "pregunta", "es_verdad", "explicacion")
        labels = {
            "modulo": "Módulo",
            "pregunta": "Afirmación",
            "es_verdad": "La afirmación es verdadera",
            "explicacion": "Explicación",
        }
        widgets = {
            "modulo": forms.Select(attrs={"class": "admin-control"}),
            "pregunta": forms.TextInput(attrs={"class": "admin-control"}),
            "es_verdad": forms.CheckboxInput(attrs={"class": "admin-checkbox"}),
            "explicacion": forms.Textarea(attrs={"class": "admin-control", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["modulo"].empty_label = "Selecciona un módulo"

    def save(self, commit=True):
        leccion = super().save(commit=False)
        if self.instance._state.adding:
            leccion.completada = 0
        if commit:
            leccion.save()
        return leccion
