
document.addEventListener('DOMContentLoaded', function () {
    const camposPesquisa = document.querySelectorAll(
        '.search-bar input, #pesquisa-documentos'
    );

    camposPesquisa.forEach(function (campo) {
        campo.addEventListener('input', function () {
            const termo = campo.value.toLowerCase().trim();

            const seletores = [
                '.documents-grid .document-card',
                '.solicitacoes-lista .solicitacao-card',
                '.solicitacoes-grid .solicitacao-card',
                '.grades-table tbody tr',
                '.payments-table tbody tr',
                '.subjects-grid .subject-card'
            ];

            const itens = document.querySelectorAll(
                seletores.join(', ')
            );

            itens.forEach(function (item) {
                const texto = item.textContent.toLowerCase();

                item.style.display = texto.includes(termo) ? '' : 'none';
            });
        });
    });
});
