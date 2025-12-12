from flask import request

class SimpleForm:
    def __init__(self, request_obj=None):
        self.request = request_obj or request
        
    def validate_on_submit(self):
        return self.request.method == 'POST'


class RegistroForm(SimpleForm):
    def __init__(self, data=None):
        super().__init__()
        self.username = type('obj', (object,), {'data': data.get('username', '') if data else ''})()
        self.email = type('obj', (object,), {'data': data.get('email', '') if data else ''})()
        self.senha = type('obj', (object,), {'data': data.get('senha', '') if data else ''})()
        self.confirmar_senha = type('obj', (object,), {'data': data.get('confirmar_senha', '') if data else ''})()


class LoginForm(SimpleForm):
    def __init__(self, data=None):
        super().__init__()
        self.username = type('obj', (object,), {'data': data.get('username', '') if data else ''})()
        self.senha = type('obj', (object,), {'data': data.get('senha', '') if data else ''})()


class CriarProjetoForm(SimpleForm):
    pass


class EditarProjetoForm(SimpleForm):
    pass

