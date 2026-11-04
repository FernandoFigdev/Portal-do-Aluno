
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.hashers import check_password, make_password

from .models import (
    Usuario,
    Aluno,
    Matricula,
    Disciplina,
    Nota,
    Pagamento,
    Aviso,
    Documento,
)


# ==== VIEW DE LOGIN ====
def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        senha = request.POST.get('senha')

        try:
            usuario = Usuario.objects.get(email=email)

            # Verifica a senha armazenada em formato hash
            try:
                senha_valida = check_password(senha, usuario.senha)
            except (ValueError, TypeError):
                senha_valida = False

            # Compatibilidade temporária com senhas antigas em texto puro
            if not senha_valida and usuario.senha == senha:
                usuario.senha = make_password(senha)
                usuario.save(update_fields=['senha'])
                senha_valida = True

            if not senha_valida:
                raise Usuario.DoesNotExist

            # Salva os dados do usuário na sessão
            request.session['usuario_id'] = usuario.id
            request.session['usuario_nome'] = usuario.nome
            request.session['usuario_tipo'] = usuario.tipo

            return redirect('dashboard')

        except Usuario.DoesNotExist:
            messages.error(request, 'Email ou senha inválidos.')

    return render(request, 'login.html')


# ==== VERIFICAÇÃO DE ACESSO ====
def verificar_login(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_tipo') != 'aluno':
        return render(request, 'acesso_negado.html')

    return None


# ==== VIEW DO DASHBOARD ====
def dashboard(request):
    if 'usuario_id' not in request.session:
        return redirect('login')

    if request.session.get('usuario_tipo') != 'aluno':
        return render(request, 'acesso_negado.html')

    usuario_id = request.session.get('usuario_id')

    try:
        aluno = Aluno.objects.get(usuario_id=usuario_id)
    except Aluno.DoesNotExist:
        return render(request, 'acesso_negado.html')

    matriculas = Matricula.objects.filter(aluno=aluno)

    disciplinas = Disciplina.objects.filter(
        id__in=matriculas.values_list('disciplina_id', flat=True)
    )

    notas = Nota.objects.filter(matricula__in=matriculas)
    pagamentos = Pagamento.objects.filter(aluno=aluno)
    avisos = Aviso.objects.filter(publico_alvo__in=['todos', 'aluno'])
    documentos = Documento.objects.filter(aluno=aluno)

    context = {
        'nome': request.session.get('usuario_nome'),
        'matricula': aluno.matricula,
        'curso': aluno.curso,
        'periodo': aluno.periodo,
        'disciplinas': disciplinas,
        'notas': notas,
        'pagamentos': pagamentos,
        'avisos': avisos,
        'documentos': documentos,
    }

    return render(request, 'dashboard.html', context)


# ==== VIEW DE PAGAMENTOS ====
def pagamentos(request):
    resposta = verificar_login(request)
    if resposta:
        return resposta

    aluno = Aluno.objects.get(usuario_id=request.session.get('usuario_id'))
    pagamentos = Pagamento.objects.filter(aluno=aluno)

    return render(
        request,
        'pagamentos.html',
        {
            'pagamentos': pagamentos,
            'nome': request.session.get('usuario_nome'),
        }
    )


# ==== VIEW DE DADOS PESSOAIS ====
def dados_pessoais(request):
    resposta = verificar_login(request)
    if resposta:
        return resposta

    aluno = Aluno.objects.get(usuario_id=request.session.get('usuario_id'))

    return render(
        request,
        'dados_pessoais.html',
        {
            'aluno': aluno,
            'nome': request.session.get('usuario_nome'),
        }
    )


# ==== VIEW DE DISCIPLINAS ====
def disciplinas(request):
    resposta = verificar_login(request)
    if resposta:
        return resposta

    aluno = Aluno.objects.get(usuario_id=request.session.get('usuario_id'))
    matriculas = Matricula.objects.filter(aluno=aluno)

    disciplinas = Disciplina.objects.filter(
        id__in=matriculas.values_list('disciplina_id', flat=True)
    )

    return render(
        request,
        'disciplinas.html',
        {
            'disciplinas': disciplinas,
            'nome': request.session.get('usuario_nome'),
        }
    )


# ==== VIEW DE DOCUMENTOS ====
def documentos(request):
    resposta = verificar_login(request)
    if resposta:
        return resposta

    aluno = Aluno.objects.get(usuario_id=request.session.get('usuario_id'))
    documentos = Documento.objects.filter(aluno=aluno)

    return render(
        request,
        'documentos.html',
        {
            'documentos': documentos,
            'nome': request.session.get('usuario_nome'),
        }
    )


# ==== VIEW DE NOTAS ====
def notas(request):
    resposta = verificar_login(request)
    if resposta:
        return resposta

    aluno = Aluno.objects.get(usuario_id=request.session.get('usuario_id'))
    matriculas = Matricula.objects.filter(aluno=aluno)
    notas = Nota.objects.filter(matricula__in=matriculas)

    return render(
        request,
        'notas.html',
        {
            'notas': notas,
            'nome': request.session.get('usuario_nome'),
        }
    )


# ==== VIEW DE LOGOUT ====
def logout_view(request):
    request.session.flush()
    return redirect('login')
