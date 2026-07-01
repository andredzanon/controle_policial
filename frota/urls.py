from django.urls import path
from . import views

app_name = 'frota'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('api/salvar-viatura/', views.api_salvar_viatura, name='api_salvar_viatura'),
    path('api/enviar-manutencao/', views.api_enviar_manutencao, name='api_enviar_manutencao'),
    path('api/retornar-manutencao/', views.api_retornar_manutencao, name='api_retornar_manutencao'),
    path('api/historico-manutencao/<int:viatura_id>/', views.api_historico_manutencao, name='api_historico_manutencao'),
    path('api/manutencao-ativa/<int:viatura_id>/', views.api_manutencao_ativa, name='api_manutencao_ativa'),
    path('abertura-turno/', views.abertura_turno_view, name='abertura_turno'),
    path('api/viaturas-operantes/', views.api_viaturas_operantes, name='api_viaturas_operantes'),
    path('api/salvar-abertura-turno/', views.api_salvar_abertura_turno, name='api_salvar_abertura_turno'),
    path('api/motoristas/', views.api_motoristas, name='api_motoristas'),
    path('api/cancelar-abertura-turno/', views.api_cancelar_abertura_turno, name='api_cancelar_abertura_turno'),
]
