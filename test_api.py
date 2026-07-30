import os
# pyrefly: ignore [missing-import]
import django
import sys

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# pyrefly: ignore [missing-import]
from django.test import RequestFactory
from frota.views import api_viaturas_operantes
# pyrefly: ignore [missing-import]
from django.contrib.auth import get_user_model
from frota.views import api_salvar_abertura_turno
import json

User = get_user_model()
user, _ = User.objects.get_or_create(username='test_user')

factory = RequestFactory()
payload = {
    'data': '2026-06-22',
    'viaturas': [
        {'id': 1, 'km_inicial': 26000, 'selecionado': True}
    ]
}

request = factory.post('/frota/api/salvar-abertura-turno/', data=json.dumps(payload), content_type='application/json')
request.user = user

response = api_salvar_abertura_turno(request)

print(f"Status Code: {response.status_code}")
print(f"Content: {response.content}")
