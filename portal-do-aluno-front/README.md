# Portal do Aluno - Front-end (protótipo)

Protótipo navegável com dados fictícios. Ainda não está integrado ao Django.

## Como abrir no VS Code
1. Arquivo > Abrir Pasta... e escolha esta pasta.
2. Instale a extensão "Live Server" e clique em "Go Live" (ou abra o index.html no navegador).

## Login de demonstração
- aluno@portal.com / 123456
- secretaria@portal.com / 123456

## Estrutura
- index.html: telas e estrutura
- css/style.css: estilos
- js/app.js: dados simulados e navegação entre telas

## Para integrar ao Django
- css/ e js/ vão para core/static/core/
- index.html vira template em core/templates/core/ (usar {% load static %})
