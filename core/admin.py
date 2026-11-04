
from django.contrib import admin
from django.contrib.auth.hashers import make_password, identify_hasher

from .models import (
    Usuario,
    Aluno,
    Professor,
    Disciplina,
    Matricula,
    Nota,
    Pagamento,
    Aviso,
    Documento,
)


class UsuarioAdmin(admin.ModelAdmin):

    def save_model(self, request, obj, form, change):
        # Evita armazenar a senha em texto puro
        try:
            identify_hasher(obj.senha)
        except (ValueError, TypeError):
            obj.senha = make_password(obj.senha)

        super().save_model(request, obj, form, change)


admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Aluno)
admin.site.register(Professor)
admin.site.register(Disciplina)
admin.site.register(Matricula)
admin.site.register(Nota)
admin.site.register(Pagamento)
admin.site.register(Aviso)
admin.site.register(Documento)
