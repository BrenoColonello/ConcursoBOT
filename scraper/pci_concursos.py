import logging
from typing import Optional

import requests
from bs4 import BeautifulSoup, Tag

from scraper.models import ConcursoResumo

logger = logging.getLogger(__name__)

URL_CONCURSOS_ABERTOS = "https://www.pciconcursos.com.br/concursos/"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    )
}

TIMEOUT_SEGUNDOS = 20


class ErroDeScraping(Exception):
    """Erro ao buscar ou interpretar páginas do PCI Concursos."""


def _buscar_html(url: str) -> str:
    try:
        resposta = requests.get(url, headers=HEADERS, timeout=TIMEOUT_SEGUNDOS)
        resposta.raise_for_status()
    except requests.RequestException as erro:
        raise ErroDeScraping(f"Falha ao acessar {url}: {erro}") from erro

    resposta.encoding = "utf-8"
    return resposta.text


def _texto(elemento: Optional[Tag]) -> str:
    return elemento.get_text(" ", strip=True) if elemento else ""


def _parsear_linha(linha: Tag) -> Optional[ConcursoResumo]:
    bloco = linha.select_one("div.ca")
    if bloco is None:
        return None

    link_tag = bloco.find("a", href=True)
    if link_tag is None:
        return None

    titulo_orgao = _texto(link_tag)
    link = link_tag["href"]
    estado = _texto(bloco.select_one("div.cc")) or None

    bloco_vagas = bloco.select_one("div.cd")
    vagas_texto = ""
    cargo_texto = ""
    escolaridade_texto = ""
    if bloco_vagas is not None:
        primeiro_conteudo = bloco_vagas.contents[0] if bloco_vagas.contents else ""
        vagas_texto = str(primeiro_conteudo).strip()

        spans = bloco_vagas.find_all("span")
        if len(spans) >= 1 and spans[0].contents:
            cargo_texto = str(spans[0].contents[0]).strip()
        if len(spans) >= 2:
            escolaridade_texto = _texto(spans[1])

    data_inscricao_texto = _texto(bloco.select_one("div.ce"))

    if not link or not titulo_orgao:
        return None

    return ConcursoResumo(
        titulo=titulo_orgao,
        orgao=titulo_orgao,
        link=link,
        estado=estado,
        vagas_texto=vagas_texto,
        cargo_texto=cargo_texto,
        escolaridade_texto=escolaridade_texto,
        data_inscricao_texto=data_inscricao_texto,
    )


def buscar_concursos_abertos() -> list[ConcursoResumo]:
    """Coleta a listagem de concursos abertos na página principal do PCI Concursos."""
    logger.info("Buscando lista de concursos abertos em %s", URL_CONCURSOS_ABERTOS)
    html = _buscar_html(URL_CONCURSOS_ABERTOS)
    soup = BeautifulSoup(html, "lxml")

    container = soup.find(id="concursos")
    if container is None:
        raise ErroDeScraping("Container #concursos não encontrado — o layout do site pode ter mudado")

    linhas = container.select("div.da, div.na, div.ea")
    concursos = []
    for linha in linhas:
        concurso = _parsear_linha(linha)
        if concurso is not None:
            concursos.append(concurso)

    logger.info("Encontrados %d concursos na listagem", len(concursos))
    return concursos


def buscar_texto_detalhes(url: str) -> str:
    """Acessa a página de detalhes de um concurso e retorna o texto completo do artigo."""
    logger.info("Buscando detalhes do concurso: %s", url)
    html = _buscar_html(url)
    soup = BeautifulSoup(html, "lxml")

    artigo = soup.find("article")
    if artigo is None:
        logger.warning("Tag <article> não encontrada em %s", url)
        return ""

    return _texto(artigo)
