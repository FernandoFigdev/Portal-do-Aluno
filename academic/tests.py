
from django.db import connections
from django.test import override_settings
from rest_framework.test import APITestCase

from core.testing import (
    FAKE_INTEGRATIONS,
    make_secretary,
    make_student,
)

from integrations.models import IntegrationLog


@override_settings(
    INTEGRATIONS=FAKE_INTEGRATIONS,
    CERBRUM_URL="https://cerbrum.exemplo.br",
    SECTRAS_URL="https://sectras.exemplo.br",
)
class AcademicTests(APITestCase):

    databases = {"default", "academico_legado"}

    @classmethod
    def setUpTestData(cls):
        cls.aluno = make_student(
            "20260001",
            external_ids={"moodle": 42}
        )
        cls.outro_aluno = make_student("20260002")

        with connections["academico_legado"].cursor() as cursor:
            cursor.execute("""
                CREATE TABLE core_aluno (
                    usuario_id INTEGER PRIMARY KEY,
                    matricula VARCHAR(50)
                )
            """)

            cursor.execute("""
                CREATE TABLE core_disciplina (
                    id INTEGER PRIMARY KEY,
                    codigo VARCHAR(50),
                    nome VARCHAR(100)
                )
            """)

            cursor.execute("""
                CREATE TABLE core_matricula (
                    id INTEGER PRIMARY KEY,
                    aluno_id INTEGER,
                    disciplina_id INTEGER,
                    ano INTEGER,
                    semestre INTEGER
                )
            """)

            cursor.execute("""
                CREATE TABLE core_nota (
                    id INTEGER PRIMARY KEY,
                    matricula_id INTEGER,
                    avaliacao VARCHAR(100),
                    valor DECIMAL,
                    data DATE
                )
            """)

            cursor.execute("""
                INSERT INTO core_aluno VALUES
                (1, '20260001'),
                (2, '20260002')
            """)

            cursor.execute("""
                INSERT INTO core_disciplina VALUES
                (1, 'ES001', 'Engenharia de Software'),
                (2, 'BD001', 'Banco de Dados')
            """)

            cursor.execute("""
                INSERT INTO core_matricula VALUES
                (1, 1, 1, 2026, 2),
                (2, 2, 2, 2026, 2)
            """)

            cursor.execute("""
                INSERT INTO core_nota VALUES
                (1, 1, 'Prova 1', 8.5, '2026-11-17'),
                (2, 2, 'Prova 1', 9.0, '2026-11-17')
            """)

    def test_exige_autenticacao(self):
        resposta = self.client.get(
            "/api/academico/disciplinas/"
        )
        self.assertEqual(resposta.status_code, 401)

    def test_exige_perfil_aluno(self):
        self.client.force_authenticate(make_secretary())

        resposta = self.client.get(
            "/api/academico/disciplinas/"
        )
        self.assertEqual(resposta.status_code, 403)

    def test_disciplinas(self):
        self.client.force_authenticate(self.aluno)

        resposta = self.client.get(
            "/api/academico/disciplinas/"
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data["results"]), 1)
        self.assertEqual(
            resposta.data["results"][0]["code"],
            "ES001"
        )

    def test_notas(self):
        self.client.force_authenticate(self.aluno)

        resposta = self.client.get(
            "/api/academico/notas/"
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data["results"]), 1)
        self.assertEqual(
            resposta.data["results"][0]["value"],
            "8.5"
        )

    def test_isolamento_entre_alunos(self):
        self.client.force_authenticate(self.outro_aluno)

        resposta = self.client.get(
            "/api/academico/disciplinas/"
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data["results"]), 1)
        self.assertEqual(
            resposta.data["results"][0]["code"],
            "BD001"
        )

        resposta = self.client.get(
            "/api/academico/notas/"
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(len(resposta.data["results"]), 1)
        self.assertEqual(
            float(resposta.data["results"][0]["value"]),
            9.0
        )

    def test_materiais_indisponiveis(self):
        self.client.force_authenticate(self.aluno)

        resposta = self.client.get(
            "/api/academico/materiais/"
        )
        self.assertEqual(resposta.status_code, 503)
        self.assertTrue(
            IntegrationLog.objects.filter(
                operation="materials",
                success=False
            ).exists()
        )

    def test_atalhos(self):
        self.client.force_authenticate(self.aluno)

        resposta = self.client.get(
            "/api/integracoes/atalhos/"
        )
        self.assertEqual(resposta.status_code, 200)
        self.assertEqual(
            {item["key"] for item in resposta.data},
            {"cerbrum", "sectras"}
        )
