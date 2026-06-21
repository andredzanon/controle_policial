from django.urls import path
from . import views

app_name = 'ocorrencias'

urlpatterns = [
    path('', views.index, name='index'),
    path('api/gerar-relatorio/', views.api_gerar_relatorio, name='api_gerar_relatorio'),
    path('api/salvar-relatorio/', views.api_salvar_relatorio, name='api_salvar_relatorio'),
    path('historico/', views.historico, name='historico'),
    path('deletar/<int:pk>/', views.deletar_relatorio, name='deletar_relatorio'),
    path('api/texto-relatorio/<int:pk>/', views.api_obter_texto_relatorio, name='api_obter_texto_relatorio'),
    path('api/json-relatorio/<int:pk>/', views.api_obter_dados_relatorio_json, name='api_obter_dados_relatorio_json'),
    path('estatisticas/', views.estatisticas_view, name='estatisticas'),
    path('api/estatisticas/', views.api_estatisticas, name='api_estatisticas'),
]
