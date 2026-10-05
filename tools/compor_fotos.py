"""Remonta as imagens de fundo das seções com as fotos novas da Andréa.

As fotos originais do site estão "assadas" nos fundos das seções (foto + fundo
escuro + brilhos + mockup de dispositivos). Este script apaga a pessoa antiga
reconstruindo o fundo, aplica a foto nova (recorte com transparência) e, na
seção "Como funciona", devolve o mockup de dispositivos por cima.

Entrada:  fotos/andrea-1.webp, fotos/andrea-2.webp
Saída:    site/img/*.webp
"""
import pathlib
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = pathlib.Path(__file__).resolve().parent.parent
UP = ROOT / "site/wp-content/uploads/2023"
OUT = ROOT / "site/img"
FOTO1 = Image.open(ROOT / "fotos/andrea-1.webp").convert("RGBA")
FOTO2 = Image.open(ROOT / "fotos/andrea-2.webp").convert("RGBA")


def limpar_fundo(img, caixa, raio, passo=16):
    """Apaga o que está dentro de `caixa` (elipse) e recria o fundo liso por
    difusão a partir das bordas, em baixa resolução (o fundo é um degradê)."""
    rgb = np.asarray(img.convert("RGB"), dtype=np.float32)
    h, w = rgb.shape[:2]
    m = Image.new("L", (w, h), 255)
    ImageDraw.Draw(m).ellipse(caixa, fill=0)
    conhecido = np.asarray(m, dtype=np.float32) / 255.0

    # reduz por média de blocos (em float, sem perder os tons escuros)
    gh, gw = h // passo, w // passo
    def reduz(a):
        a = a[: gh * passo, : gw * passo]
        return a.reshape(gh, passo, gw, passo, *a.shape[2:]).mean(axis=(1, 3))
    k = reduz(conhecido)
    fixo = k > 0.999
    low = reduz(rgb * conhecido[..., None]) / np.maximum(k, 1e-6)[..., None]
    low[~fixo] = low[fixo].mean(axis=0)
    for _ in range(4000):  # Jacobi: cada célula livre vira a média dos vizinhos
        p = np.pad(low, ((1, 1), (1, 1), (0, 0)), mode="edge")
        viz = (p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 4
        low = np.where(fixo[..., None], low, viz)

    # amplia suavemente cada canal
    up = np.stack(
        [np.asarray(Image.fromarray(low[..., c].astype(np.float32), "F").resize((w, h), Image.BICUBIC)) for c in range(3)],
        -1,
    )
    # mistura com borda bem suave
    mk = np.asarray(m.filter(ImageFilter.GaussianBlur(raio / 3)), dtype=np.float32)[..., None] / 255.0
    mk = np.minimum(mk, conhecido[..., None])  # dentro da elipse é sempre o fundo novo
    out = rgb * mk + up * (1 - mk)
    out += np.random.default_rng(1).normal(0, 1.0, out.shape)  # leve granulado
    return Image.fromarray(np.clip(out, 0, 255).astype(np.uint8)).convert("RGBA")


def brilho(base, centro, raio, cor, forca):
    """Adiciona um brilho radial (screen) como os do original."""
    w, h = base.size
    yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xx - centro[0]) ** 2 + (yy - centro[1]) ** 2) / raio
    a = np.clip(1 - d, 0, 1) ** 2 * forca
    arr = np.asarray(base, dtype=np.float32)
    c = np.array(cor, dtype=np.float32)
    arr[..., :3] = 255 - (255 - arr[..., :3]) * (1 - a[..., None] * c / 255)
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def preparar_foto(foto, escala, fade_ini, fade_fim, laterais=0.0, tom=0.9):
    """Redimensiona, escurece levemente e esmaece embaixo/nas laterais."""
    f = foto.resize((round(foto.width * escala), round(foto.height * escala)), Image.LANCZOS)
    arr = np.asarray(f, dtype=np.float32)
    arr[..., :3] *= tom
    h, w = arr.shape[:2]
    ys = np.arange(h, dtype=np.float32)[:, None]
    fade = np.clip((fade_fim - ys) / max(fade_fim - fade_ini, 1), 0, 1)
    if laterais:
        xs = np.arange(w, dtype=np.float32)[None, :]
        lw = w * laterais
        fade = fade * np.clip(xs / lw, 0, 1) * np.clip((w - 1 - xs) / lw, 0, 1)
    arr[..., 3] *= fade
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))


def mascara_dispositivos(size, retangulos):
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    for r in retangulos:
        d.rounded_rectangle(r, radius=6, fill=255)
    return m


def sombra(base, foto, pos, raio=40, forca=110):
    """Sombra suave da silhueta, para a foto 'assentar' no fundo escuro."""
    a = Image.new("L", base.size, 0)
    a.paste(foto.getchannel("A"), pos)
    a = a.filter(ImageFilter.GaussianBlur(raio)).point(lambda v: v * forca // 255)
    preto = Image.new("RGBA", base.size, (0, 0, 0, 255))
    return Image.composite(preto, base, a)


# ---------------------------------------------------------------- seção 1
def secao1():
    orig = Image.open(UP / "10/Slice-10121.webp").convert("RGBA")
    # dispositivos (laptop, tablet, celular) recortados do original
    disp = [(397, 816, 787, 1060), (785, 866, 957, 1063), (742, 899, 829, 1074)]
    mdisp = mascara_dispositivos(orig.size, disp)

    base = limpar_fundo(orig, (360, 60, 1080, 1180), 90)
    foto = preparar_foto(FOTO1, 0.62, 560, 780, laterais=0.08)
    pos = (330, 92)
    base.alpha_composite(foto, pos)
    base.paste(orig, (0, 0), mdisp)
    base.convert("RGB").save(OUT / "andrea-como-funciona.webp", quality=88)

    # versão celular: mesma composição reduzida, sobre o fundo do celular
    mob = Image.open(UP / "10/Frame-6811123.webp").convert("RGBA")
    mbase = limpar_fundo(mob, (270, 50, 500, 390), 40)
    s, ox, oy = 0.305, 172, 39
    camada = Image.new("RGBA", orig.size, (0, 0, 0, 0))
    camada.alpha_composite(foto, pos)
    camada.paste(orig, (0, 0), mdisp)
    a = np.asarray(camada.getchannel("A")).copy()
    a[np.asarray(mdisp) > 0] = 255
    camada.putalpha(Image.fromarray(a))
    cx0, cy0, cx1, cy1 = 300, 60, 1000, 1080
    peq = camada.crop((cx0, cy0, cx1, cy1))
    peq = peq.resize((round(peq.width * s), round(peq.height * s)), Image.LANCZOS)
    mbase.alpha_composite(peq, (round(ox + cx0 * s), round(oy + cy0 * s)))
    mbase.convert("RGB").save(OUT / "andrea-como-funciona-mobile.webp", quality=88)


# ---------------------------------------------------------------- seção 2
def secao2():
    orig = Image.open(UP / "09/Slice-7.webp").convert("RGBA")
    base = limpar_fundo(orig, (180, 40, 1200, 1300), 110)
    base = brilho(base, (300, 520), 520, (150, 20, 200), 0.42)
    base = brilho(base, (930, 460), 480, (20, 70, 255), 0.42)
    foto = preparar_foto(FOTO2, 0.94, 900, 1060)
    pos = (-10, 85)
    base.alpha_composite(foto.crop((-pos[0], 0, foto.width, foto.height)), (0, pos[1]))
    base.convert("RGB").save(OUT / "andrea-fundadora.webp", quality=88)

    tab = Image.open(UP / "09/Frame-67.webp").convert("RGBA")
    tbase = limpar_fundo(tab, (200, 0, 640, 470), 50)
    tbase = brilho(tbase, (275, 200), 150, (150, 20, 200), 0.5)
    tbase = brilho(tbase, (520, 190), 140, (20, 70, 255), 0.5)
    foto = preparar_foto(FOTO2, 0.42, 200, 400, laterais=0.06)
    pos = (154, 12)
    tbase.alpha_composite(foto, pos)
    tbase.convert("RGB").save(OUT / "andrea-fundadora-mobile.webp", quality=88)


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    secao1()
    secao2()
    print("ok:", sorted(p.name for p in OUT.glob("andrea-*.webp")))
