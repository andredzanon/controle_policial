from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'usuarios'

urlpatterns = [
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/salvar-usuario/', views.api_salvar_usuario, name='api_salvar_usuario'),
    path('api/alterar-minha-senha/', views.api_alterar_minha_senha, name='api_alterar_minha_senha'),
    path('api/alterar-senha-usuario/', views.api_alterar_senha_usuario, name='api_alterar_senha_usuario'),
    path('troca-obrigatoria/', views.troca_obrigatoria, name='troca_obrigatoria'),
]
