from django.core.management.base import BaseCommand

from documents.models import DocumentType

# Lista inicial PROVISÓRIA: os tipos definitivos devem ser validados com a secretaria (ERS, item 12).
TYPES = [
    ("Declaração de matrícula", "Comprova vínculo ativo com a instituição.", ["finalidade"]),
    ("Histórico escolar", "Histórico acadêmico completo.", ["finalidade"]),
    ("Declaração de conclusão de curso", "Para alunos concluintes.", ["finalidade"]),
]


class Command(BaseCommand):
    help = "Cadastra os tipos de documento iniciais (provisórios)."

    def handle(self, *args, **options):
        for name, description, fields in TYPES:
            _, created = DocumentType.objects.get_or_create(
                name=name, defaults={"description": description, "required_fields": fields}
            )
            self.stdout.write(f"{'criado' if created else 'já existe'}: {name}")
