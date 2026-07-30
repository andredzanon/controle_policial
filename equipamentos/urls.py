from django.urls import path
from . import views

app_name = 'equipamentos'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('api/salvar-equipamento/', views.api_salvar_equipamento, name='api_salvar_equipamento'),
    path('api/excluir-equipamento/', views.api_excluir_equipamento, name='api_excluir_equipamento'),
]

