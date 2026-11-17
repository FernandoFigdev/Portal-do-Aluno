from rest_framework.test import APITestCase

from accounts.models import User

from .audit import audit
from .models import AuditLog
from .testing import PrivateMediaMixin, make_secretary, make_student


class AuditTests(APITestCase):
    def test_audit_descarta_segredos_inclusive_aninhados(self):
        actor = make_secretary()
        entry = audit(actor, "X", actor, {
            "ok": 1, "password": "p", "Token": "t",
            "aninhado": {"api_secret": "s", "visivel": 2},
        })
        self.assertEqual(entry.details, {"ok": 1, "aninhado": {"visivel": 2}})

    def test_endpoint_de_auditoria_somente_administrador(self):
        secretaria = make_secretary()
        admin = make_secretary("admin", role=User.Role.ADMIN)
        aluno = make_student("20260001")
        audit(admin, "TESTE", admin)

        self.client.force_authenticate(aluno)
        self.assertEqual(self.client.get("/api/admin/auditoria/").status_code, 403)
        self.client.force_authenticate(secretaria)
        self.assertEqual(self.client.get("/api/admin/auditoria/").status_code, 403)
        self.client.force_authenticate(admin)
        resp = self.client.get("/api/admin/auditoria/?acao=TESTE")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["count"], 1)
        self.assertEqual(AuditLog.objects.count(), 1)


class DashboardTests(PrivateMediaMixin, APITestCase):
    def test_painel_exige_autenticacao(self):
        self.assertEqual(self.client.get("/api/dashboard/").status_code, 401)

    def test_painel_do_aluno_e_da_secretaria(self):
        aluno = make_student("20260001")
        self.client.force_authenticate(aluno)
        resp = self.client.get("/api/dashboard/")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["role"], "STUDENT")
        self.assertEqual(resp.data["requests"]["total"], 0)
        self.assertEqual(resp.data["certificates"], 0)

        self.client.force_authenticate(make_secretary())
        resp = self.client.get("/api/dashboard/")
        self.assertEqual(resp.data["role"], "STAFF")
        self.assertIn("open", resp.data["requests"])
