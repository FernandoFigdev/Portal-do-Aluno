from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APITestCase

from core.models import AuditLog
from core.testing import PDF_BYTES, PrivateMediaMixin, make_secretary, make_student

from .models import Certificate


def arquivo(name="c.pdf", content=PDF_BYTES):
    return SimpleUploadedFile(name, content)


class CertificateTests(PrivateMediaMixin, APITestCase):
    def setUp(self):
        super().setUp()
        self.ana = make_student("20260001", first="Ana")
        self.bruno = make_student("20260002", first="Bruno")
        self.secretaria = make_secretary()

    def cadastrar(self, matricula="20260001", **extra):
        self.client.force_authenticate(self.secretaria)
        dados = {"student": matricula, "category": "Atividade complementar",
                 "title": "Semana de Tecnologia", "file": arquivo(), **extra}
        return self.client.post("/api/admin/certificados/", dados, format="multipart")

    def test_secretaria_cadastra_e_aluno_baixa(self):
        resp = self.cadastrar()
        self.assertEqual(resp.status_code, 201, resp.data)
        self.assertEqual(resp.data["student"], "20260001")
        self.assertNotIn("file", resp.data)

        self.client.force_authenticate(self.ana)
        lista = self.client.get("/api/certificados/")
        self.assertEqual(lista.data["count"], 1)
        baixar = self.client.get(lista.data["results"][0]["download_url"])
        self.assertEqual(baixar.status_code, 200)
        self.assertEqual(b"".join(baixar.streaming_content), PDF_BYTES)

    def test_aluno_so_ve_os_proprios_certificados(self):
        cert_id = self.cadastrar().data["id"]
        self.client.force_authenticate(self.bruno)
        self.assertEqual(self.client.get("/api/certificados/").data["count"], 0)
        self.assertEqual(self.client.get(f"/api/certificados/{cert_id}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/certificados/{cert_id}/download/").status_code, 404)

    def test_aluno_nao_cadastra_nem_acessa_area_admin(self):
        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get("/api/admin/certificados/").status_code, 403)
        resp = self.client.post(
            "/api/admin/certificados/",
            {"student": "20260001", "category": "x", "title": "y", "file": arquivo()}, format="multipart",
        )
        self.assertEqual(resp.status_code, 403)

    def test_anonimo_nao_acessa(self):
        self.assertEqual(self.client.get("/api/certificados/").status_code, 401)

    def test_matricula_inexistente_e_arquivo_invalido(self):
        self.assertEqual(self.cadastrar(matricula="999").status_code, 400)
        self.client.force_authenticate(self.secretaria)
        ruim = self.client.post(
            "/api/admin/certificados/",
            {"student": "20260001", "category": "x", "title": "y", "file": arquivo("a.pdf", b"texto")},
            format="multipart",
        )
        self.assertEqual(ruim.status_code, 400)
        sem_arquivo = self.client.post(
            "/api/admin/certificados/", {"student": "20260001", "category": "x", "title": "y"}, format="multipart"
        )
        self.assertEqual(sem_arquivo.status_code, 400)
        self.assertEqual(Certificate.objects.count(), 0)

    def test_correcao_reassocia_aluno_e_audita(self):
        cert_id = self.cadastrar().data["id"]
        resp = self.client.patch(f"/api/admin/certificados/{cert_id}/", {"student": "20260002"}, format="json")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.data["student"], "20260002")

        self.client.force_authenticate(self.ana)
        self.assertEqual(self.client.get("/api/certificados/").data["count"], 0)
        self.client.force_authenticate(self.bruno)
        self.assertEqual(self.client.get("/api/certificados/").data["count"], 1)

        log = AuditLog.objects.get(action="CERTIFICATE_UPDATED")
        self.assertEqual(log.details["student_from"], "20260001")
        self.assertEqual(log.details["student_to"], "20260002")

    def test_filtros_da_secretaria(self):
        self.cadastrar()
        self.cadastrar("20260002", category="Evento")
        self.client.force_authenticate(self.secretaria)
        self.assertEqual(self.client.get("/api/admin/certificados/?matricula=20260002").data["count"], 1)
        self.assertEqual(self.client.get("/api/admin/certificados/?categoria=evento").data["count"], 1)

    def test_aceita_png(self):
        png = b"\x89PNG\r\n\x1a\n" + b"0" * 20
        resp = self.cadastrar(file=arquivo("c.png", png))
        self.assertEqual(resp.status_code, 201, resp.data)
