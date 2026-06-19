import json
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

Usuario = get_user_model()

@login_required
def dashboard(request):
    if request.user.nivel not in ['admin_master', 'administrador']:
        return HttpResponseForbidden("Acesso restrito.")
    
    # Exclude the current logged in user from list or just list everyone? Let's list everyone.
    tropa = Usuario.objects.all().order_by('first_name', 'username')
    return render(request, 'usuarios/dashboard.html', {'tropa': tropa})

@login_required
@require_POST
def api_salvar_usuario(request):
    if request.user.nivel not in ['admin_master', 'administrador']:
        return JsonResponse({'error': 'Acesso negado.'}, status=403)

    try:
        data = json.loads(request.body)
        user_id = data.get('id')
        username = data.get('username', '').strip().lower()
        nome_completo = data.get('first_name', '').strip()
        nivel = data.get('nivel', 'operador')

        if not username or not nome_completo:
            return JsonResponse({'error': 'Preencha Login e Nome.'}, status=400)

        if user_id:
            # Edit
            u = get_object_or_404(Usuario, pk=user_id)
            # Check if trying to edit an admin_master being just admin
            if u.nivel == 'admin_master' and request.user.nivel != 'admin_master':
                 return JsonResponse({'error': 'Permissão insuficiente.'}, status=403)
            
            # Avoid duplicate username
            if Usuario.objects.filter(username=username).exclude(pk=user_id).exists():
                return JsonResponse({'error': 'Este login já está em uso.'}, status=400)

            u.username = username
            u.first_name = nome_completo
            u.nivel = nivel
            u.save()
            msg = 'Usuário atualizado com sucesso.'
        else:
            # Create
            if Usuario.objects.filter(username=username).exists():
                return JsonResponse({'error': 'Este login já está em uso.'}, status=400)

            u = Usuario(
                username=username,
                first_name=nome_completo,
                nivel=nivel
            )
            u.set_password('senha123') # Senha Padrão
            u.save()
            msg = 'Usuário criado com sucesso. Senha padrão: senha123'

        return JsonResponse({'status': 'sucesso', 'message': msg})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Create your views here.
