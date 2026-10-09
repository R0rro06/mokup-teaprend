from django.contrib import admin
from .models import CursosLeccion, CursosModulo


class LeccionInline(admin.TabularInline):
    model = CursosLeccion
    extra = 1


@admin.register(CursosModulo)
class ModuloAdmin(admin.ModelAdmin):
    list_display = ('orden', 'titulo')
    inlines = [LeccionInline]


@admin.register(CursosLeccion)
class LeccionAdmin(admin.ModelAdmin):
    list_display = ('pregunta', 'modulo', 'es_verdad', 'completada')
