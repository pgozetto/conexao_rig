# Conexão RIG

Versão estática do site **[conexaorig.com.br](https://www.conexaorig.com.br/)**, o maior hub de conteúdo sobre Relações Institucionais e Governamentais (RIG) do país.

O site original foi feito em WordPress + Elementor, e o cliente perdeu o acesso ao painel e à hospedagem. Este repositório é uma reconstrução fiel do design publicado, em HTML/CSS/JS estático, que pode ser hospedada em qualquer lugar sem WordPress nem banco de dados.

## Estrutura

```
conexao_rig/
├── site/                  # o site pronto para publicar
│   ├── index.html         # página única (landing page)
│   ├── css/contraste.css  # ajustes de legibilidade sobre o original
│   └── wp-content/ ...    # CSS, JS, fontes e imagens do tema/Elementor
└── tools/
    └── mirror.py          # script que gera a cópia a partir do site no ar
```

## Rodando localmente

Precisa só de Python 3:

```bash
python -m http.server 8765 --directory site
```

Depois é só abrir <http://localhost:8765>.

## Publicando

A pasta `site/` é autossuficiente. Basta enviá-la para a raiz de qualquer hospedagem estática:

- **GitHub Pages / Netlify / Vercel / Cloudflare Pages:** diretório de publicação `site`, sem comando de build.
- **cPanel / Hostinger / FTP:** envie o conteúdo de `site/` para `public_html/`.

## Ajustes feitos em relação ao original

| Ajuste | Onde |
|---|---|
| Parágrafos em cinza-escuro (`#333`) sobre fundo escuro passaram para cinza-claro/branco | Hero, cards "Como funciona", planos, bio da fundadora, FAQ |
| Texto animado "Para quem quer…" ficou azul-claro | Seção "O ConexãoRIG foi desenvolvido…" |
| Degradê da marca clareado no texto sobre fundo escuro | Bio da fundadora |
| Lazy-load do Smush trocado por carregamento normal das imagens | Todas as imagens |
| Fotos novas da Andréa Gozetto (desktop e celular) | Seções "Como funciona" e "Sobre a fundadora" |
| Preços: trimestral R$ 73,73/mês (R$ 207 à vista), anual R$ 61,38/mês (R$ 597 à vista), Express R$ 30,54/mês | "Escolha seu plano" |
| Botão do Express passou a levar ao checkout (antes abria um popup que não funcionava) | "Escolha seu plano" |

Todas as mudanças visuais ficam em [`site/css/contraste.css`](site/css/contraste.css), sem alterar os arquivos originais do tema.

## Fotos das seções

As fotos da Andréa nas seções "Como funciona" e "Sobre a fundadora" fazem parte das imagens de fundo, junto com o fundo escuro, os brilhos e o mockup de dispositivos. Para trocá-las:

1. Coloque as fotos recortadas (PNG/WebP com fundo transparente) em `fotos/andrea-1.webp` e `fotos/andrea-2.webp`.
2. Rode `python tools/compor_fotos.py` (precisa de `pip install pillow numpy`).
3. O script gera `site/img/andrea-*.webp` (versões desktop e celular), já usadas pelo `index.html`.

## Integrações a revisar

Os links abaixo continuam apontando para as contas originais e devem ser conferidos com o cliente (todos em `site/index.html`):

| Onde | Link atual |
|---|---|
| Botão **ENTRAR** (área de membros) | `http://conexaorig.astronmembers.com/` |
| Plano trimestral | `https://payfast.greenn.com.br/34557/offer/s3NGIx?cupom=RIG90` |
| Plano anual | `https://payfast.greenn.com.br/34413?cupom=RIG365` |
| Plano Express | `https://payfast.greenn.com.br/34415` |
| WhatsApp (botão "Entrar em contato") | `https://wa.me/5511981112451` (+55 11 98111-2451) |
| Cursos avulsos (Greenn) | `payfast.greenn.com.br/34415`, `34421`, `34422`, `34424` a `34430` |
| Link externo | `http://ricardowebm.com.br/lp` |
| Pixel do Facebook (PixelYourSite) | ID `671927501267047`, no bloco `pysOptions` e no `<noscript>` |

## Regerando a cópia

Se o site original mudar e você quiser capturar a versão nova:

```bash
python tools/mirror.py
```

O script baixa o HTML e todos os assets do domínio (incluindo os referenciados dentro dos CSS), reescreve os caminhos para relativos e injeta o `contraste.css` de novo.

## Observações conhecidas

- O site original já apresenta um erro de JavaScript do Elementor Pro (versão 3.11 com o Elementor 3.29). A cópia mantém o mesmo comportamento, e o erro não afeta o visual.
- O PixelYourSite tenta chamar `wp-admin/admin-ajax.php` no servidor antigo. Fora do domínio original essa chamada é bloqueada por CORS, sem impacto visual. Ao reconfigurar o pixel, esse bloco pode ser removido.
- Os links `/feed/`, `/wp-json/` e `xmlrpc.php` no `<head>` são resquícios do WordPress e podem ser apagados.
