from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            if getattr(request.user, 'senha_provisoria', False):
                # Permite acesso às URLs necessárias para concluir a troca de senha ou fazer logout
                allowed_paths = [
                    reverse('usuarios:troca_obrigatoria'),
                    reverse('usuarios:api_alterar_minha_senha'),
                    reverse('usuarios:logout'),
                ]
                
                if not any(request.path.startswith(path) for path in allowed_paths) and not request.path.startswith('/static/'):
                    return redirect('usuarios:troca_obrigatoria')

        response = self.get_response(request)
        return response
