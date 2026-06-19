from django.urls import path
from . import views

app_name = 'frota'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/salvar-viatura/', views.api_salvar_viatura, name='api_salvar_viatura'),
    path('api/enviar-manutencao/', views.api_enviar_manutencao, name='api_enviar_manutencao'),
    path('api/retornar-manutencao/', views.api_retornar_manutencao, name='api_retornar_manutencao'),
    path('api/historico-manutencao/<int:viatura_id>/', views.api_historico_manutencao, name='api_historico_manutencao'),
]
