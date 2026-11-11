from django.test import override_settings
from rest_framework.test import APITestCase

from core.testing import FAKE_INTEGRATIONS, make_secretary, make_student
from integrations.models import IntegrationLog


@override_settings(INTEGRATIONS=FAKE_INTEGRATIONS, CERBRUM_URL="https://cerbrum.exemplo.br",
                   SECTRAS_URL="https://sectras.exemplo.br")
class AcademicTests(APITestCase):
    def setUp(self):
        self.ana = make_student("20260001", external_ids={"moodle": 42, "cerbrum": "A-1"})
        self.sem_vinculo = make_student("20260002")

    def test_exige_autenticacao_e_perfil_aluno(self):
        self.assertEqual(self.client.get("/api/academico/disciplinas/").status_code, 401)
        self.client.force_authenticate(make_secretary())
        self.assertEqual(self.client.get("/api/academico/disciplinas/").status_code, 403)

    def test_disciplinas_usam_o_id_externo_do_proprio_aluno(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.get("/api/academico/disciplinas/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["source"], "SECTRAS Online")
        self.assertIn("fetched_at", resp.data)
        self.assertEqual(resp.data["results"][0]["name"], "POO (usuário 42)")
        self.assertTrue(IntegrationLog.objects.filter(system="moodle", success=True).exists())

    def test_notas(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.get("/api/academico/notas/")
        self.assertEqual(resp.data["results"][0]["value"], "8.5")

    def test_fonte_indisponivel_retorna_503_sem_dados_simulados(self):
        self.client.force_authenticate(self.ana)
        resp = self.client.get("/api/academico/materiais/")
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(resp.data["code"], "integration_unavailable")
        self.assertNotIn("results", resp.data)
        self.assertTrue(IntegrationLog.objects.filter(operation="materials", success=False).exists())

    def test_aluno_sem_vinculo_recebe_409(self):
        self.client.force_authenticate(self.sem_vinculo)
        resp = self.client.get("/api/academico/disciplinas/")
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.data["code"], "student_not_linked")

    def test_status_e_atalhos(self):
        self.client.force_authenticate(self.ana)
        self.client.get("/api/academico/disciplinas/")
        status = {s["service"]: s for s in self.client.get("/api/integracoes/status/").data}
        self.assertTrue(status["courses"]["last_check"]["success"])
        self.assertIsNone(status["grades"]["last_check"])
        atalhos = self.client.get("/api/integracoes/atalhos/").data
        self.assertEqual({a["key"] for a in atalhos}, {"cerbrum", "sectras"})

    def test_cerbrum_padrao_retorna_503(self):
        with override_settings(INTEGRATIONS={
            **FAKE_INTEGRATIONS, "grades": "integrations.adapters.cerbrum.CerbrumGradesProvider"}):
            self.client.force_authenticate(self.ana)
            resp = self.client.get("/api/academico/notas/")
        self.assertEqual(resp.status_code, 503)
