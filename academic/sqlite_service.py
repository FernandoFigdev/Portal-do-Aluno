
from django.db import connections


def listar_disciplinas(matricula):
    with connections["academico_legado"].cursor() as cursor:
        cursor.execute("""
            SELECT DISTINCT d.codigo, d.nome
            FROM core_disciplina d
            JOIN core_matricula m
                ON m.disciplina_id = d.id
            JOIN core_aluno a
                ON a.usuario_id = m.aluno_id
            WHERE a.matricula = %s
            ORDER BY d.nome
        """, [matricula])

        return [
            {"code": str(codigo), "name": nome}
            for codigo, nome in cursor.fetchall()
        ]


def listar_notas(matricula):
    with connections["academico_legado"].cursor() as cursor:
        cursor.execute("""
            SELECT d.codigo, d.nome,
                   m.ano, m.semestre, n.valor
            FROM core_nota n
            JOIN core_matricula m
                ON m.id = n.matricula_id
            JOIN core_aluno a
                ON a.usuario_id = m.aluno_id
            JOIN core_disciplina d
                ON d.id = m.disciplina_id
            WHERE a.matricula = %s
            ORDER BY n.data DESC
        """, [matricula])

        return [
            {
                "course_code": str(codigo),
                "course_name": nome,
                "period": f"{ano}/{semestre}",
                "value": str(valor)
            }
            for codigo, nome, ano, semestre, valor
            in cursor.fetchall()
        ]
