"""Gera uma cópia estática de https://www.conexaorig.com.br/ em ./site"""
import re, sys, pathlib, urllib.parse, urllib.request, html as htmlmod

ROOT = pathlib.Path(__file__).resolve().parent.parent / "site"
BASE = "https://www.conexaorig.com.br/"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "pt-BR,pt;q=0.9",
}
# chunks JS carregados dinamicamente pelo Elementor (capturados no navegador)
EXTRA = [
    "wp-content/plugins/elementor/assets/js/shared-frontend-handlers.30dc2f9c080845a413a6.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/image-carousel.6167d20b95b33386757b.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/text-editor.c084ef86600b6f11690d.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/counter.12335f45aaa79d244f24.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/nested-tabs.1fde581754604147f6d7.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/accordion.36aa4c8c4eba17bc8e03.bundle.min.js",
    "wp-content/plugins/elementor/assets/js/nested-title-keyboard-handler.fc9d01c2cd0ef46d20fd.bundle.min.js",
] + sys.argv[1:]

done = {}

def fetch(url):
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.read()

def local_path(url):
    p = urllib.parse.urlparse(url)
    return urllib.parse.unquote(p.path.lstrip("/"))

def get_asset(url):
    """Baixa um asset do domínio e devolve o caminho local relativo a ROOT."""
    url = htmlmod.unescape(url)
    rel = local_path(url)
    if rel in done:
        return rel
    done[rel] = None
    dest = ROOT / rel
    try:
        data = fetch(url)
    except Exception as e:
        print("FALHOU", url, e)
        return rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    if rel.endswith(".css"):
        data = process_css(data.decode("utf-8", "replace"), url).encode("utf-8")
    dest.write_bytes(data)
    print("ok", rel)
    return rel

CSS_URL = re.compile(r"""url\(\s*(['"]?)([^'")]+)\1\s*\)""")

def process_css(css, css_url):
    css_rel = local_path(css_url)
    css_dir = pathlib.PurePosixPath(css_rel).parent

    def repl(m):
        q, u = m.group(1), m.group(2).strip()
        if u.startswith("data:") or u.startswith("#"):
            return m.group(0)
        absu = urllib.parse.urljoin(css_url, u)
        if "conexaorig.com.br" not in urllib.parse.urlparse(absu).netloc:
            return m.group(0)
        target = get_asset(absu.split("#")[0])
        frag = "#" + absu.split("#", 1)[1] if "#" in absu else ""
        relp = posix_relpath(target, css_dir)
        return f"url({q}{relp}{frag}{q})"

    return CSS_URL.sub(repl, css)

def posix_relpath(target, start_dir):
    import posixpath
    return posixpath.relpath(target, str(start_dir) if str(start_dir) != "." else ".")

ASSET_RE = re.compile(
    r"""(?:https?:)?(?:\\?/){2}(?:www\.)?conexaorig\.com\.br((?:\\?/)(?:wp-content|wp-includes)[^"'\s<>)\\,]*(?:\\/[^"'\s<>)\\,]*)*)"""
)

def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    page = fetch(BASE).decode("utf-8")

    # lazy-load do Smush -> carregamento normal
    page = re.sub(r'(<img[^>]*?)\ssrc="data:image/gif;base64,[^"]*"', r"\1", page)
    page = page.replace(" data-src=", " src=").replace(" data-srcset=", " srcset=").replace(" data-sizes=", " sizes=")
    page = re.sub(r'(class="[^"]*?)\s?\blazyload\b', r"\1", page)

    def repl(m):
        path = m.group(1)
        escaped = "\\/" in path
        clean = path.replace("\\/", "/")
        url = "https://www.conexaorig.com.br" + clean
        # pula endpoints dinâmicos
        if clean.endswith("/") and "." not in clean.rsplit("/", 2)[-2]:
            rel = clean.lstrip("/")
        else:
            rel = get_asset(url.split("?")[0] if not clean.endswith(".css") else url)
            if "?" in clean:
                rel = rel  # query descartada
        return rel.replace("/", "\\/") if escaped else rel

    page = ASSET_RE.sub(repl, page)

    # links internos -> âncoras locais
    page = re.sub(r'https?://(?:www\.)?conexaorig\.com\.br/(#[^"\']*)', r"\1", page)
    page = re.sub(r'href="https?://(?:www\.)?conexaorig\.com\.br/?"', 'href="./"', page)

    for e in EXTRA:
        get_asset(BASE + e)

    # correções de contraste (site/css/contraste.css)
    page = page.replace("</head>", '<link rel="stylesheet" href="css/contraste.css">\n</head>', 1)

    (ROOT / "index.html").write_text(page, encoding="utf-8")
    print("\nTotal de arquivos:", len(done))

if __name__ == "__main__":
    main()
