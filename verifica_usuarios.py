from accounts.models import User

# Lista de campos a verificar
campos = [
    'email', 'full_name', 'first_name', 'last_name', 'company', 'role', 'status', 'language', 'date_joined'
]

usuarios_invalidos = []

for user in User.objects.all():
    for campo in campos:
        valor = getattr(user, campo, None)
        if valor is None or (isinstance(valor, str) and valor.strip() == ''):
            usuarios_invalidos.append((user.email, campo, valor))

if usuarios_invalidos:
    print('Usuarios con campos nulos o vacíos:')
    for email, campo, valor in usuarios_invalidos:
        print(f"Usuario: {email} | Campo: {campo} | Valor: {valor}")
else:
    print('Todos los usuarios tienen los campos requeridos completos.')
