from django.contrib import admin
from .models import (
    RelatorioTurno, VeiculoAbordado, PessoaAbordada,
    VeiculoRecolhido, PrisaoApreensao, ApreensaoDroga, TesteEtilometrico
)

class VeiculoAbordadoInline(admin.TabularInline):
    model = VeiculoAbordado
    extra = 0

class PessoaAbordadaInline(admin.TabularInline):
    model = PessoaAbordada
    extra = 0

class PrisaoApreensaoInline(admin.TabularInline):
    model = PrisaoApreensao
    extra = 0

class ApreensaoDrogaInline(admin.TabularInline):
    model = ApreensaoDroga
    extra = 0

class TesteEtilometricoInline(admin.StackedInline):
    model = TesteEtilometrico
    
@admin.register(RelatorioTurno)
class RelatorioTurnoAdmin(admin.ModelAdmin):
    list_display = ('data', 'viatura', 'comandante', 'created_at')
    list_filter = ('data', 'viatura')
    search_fields = ('comandante', 'viatura__prefixo')
    inlines = [
        TesteEtilometricoInline,
        VeiculoAbordadoInline, 
        PessoaAbordadaInline, 
        PrisaoApreensaoInline, 
        ApreensaoDrogaInline
    ]
