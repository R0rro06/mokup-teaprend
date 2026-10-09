from django.contrib import admin
from django.urls import path
from cursos.views import (
    admin_panel_view,
    dashboard_view,
    eliminar_contenido_view,
    leccion_view,
    login_view,
    logout_view,
    register_view,
)

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', login_view, name='login'),
    path('registro/', register_view, name='registro'),
    path('logout/', logout_view, name='logout'),
    path('dashboard/', dashboard_view, name='dashboard'),
    path('leccion/<int:leccion_id>/', leccion_view, name='leccion'),
    path('panel-administracion/', admin_panel_view, name='admin_panel'),
    path('panel-administracion/eliminar/', eliminar_contenido_view, name='eliminar_contenido'),
]
