import json
import logging
from typing import Optional

import anthropic
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

MODELO = "claude-opus-4-8"
LIMITE_CARACTERES_TEXTO = 15000

_cliente: Optional[anthropic.Anthropic] = None


class ErroDeExtracao(Exception):
    """Erro ao extrair dados estruturados de um concurso via LLM."""


def _obter_cliente() -> anthropic.Anthropic:
    global _cliente
    if _cliente is None:
        _cliente = anthropic.Anthropic()
    return _cliente


ESQUEMA_CONCURSO = {
    "type": "object",
    "properties": {
        "orgao": {"type": "string"},
        "cargo": {"type": "array", "items": {"type": "string"}},
        "numero_vagas": {"type": ["integer", "null"]},
        "remuneracao": {"type": ["string", "null"]},
        "escolaridade_minima": {
            "type": "string",
            "enum": ["fundamental", "medio", "superior", "nao_especifica"],
        },
        "area": {"type": ["string", "null"]},
        "idade_minima": {"type": ["integer", "null"]},
        "idade_maxima": {"type": ["integer", "null"]},
        "data_inscricao_fim": {"type": ["string", "null"]},
        "valor_inscricao": {"type": ["string", "null"]},
        "data_prova": {"type": ["string", "null"]},
        "link_edital": {"type": ["string", "null"]},
        "estado_municipio": {"type": ["string", "null"]},
        "nota_ciencia_computacao": {"type": "integer"},
        "justificativa_nota": {"type": "string"},
    },
    "required": [
        "orgao",
        "cargo",
        "numero_vagas",
        "remuneracao",
        "escolaridade_minima",
        "area",
        "idade_minima",
        "idade_maxima",
        "data_inscricao_fim",
        "valor_inscricao",
        "data_prova",
        "link_edital",
        "estado_municipio",
        "nota_ciencia_computacao",
        "justificativa_nota",
    ],
    "additionalProperties": False,
}

PROMPT_SISTEMA = """Você é um assistente que extrai dados estruturados de textos sobre concursos públicos brasileiros.

Regras:
- escolaridade_minima deve ser "fundamental", "medio", "superior" ou "nao_especifica", conforme o menor requisito de escolaridade citado para qualquer um dos cargos.
- Se houver múltiplos cargos, liste todos em "cargo". Se o texto disser apenas "Vários Cargos" sem detalhar, use esse texto literal como único item.
- numero_vagas é o total de vagas somando todos os cargos, quando informado; caso contrário, use null.
- Datas devem ser normalizadas para o formato DD/MM/AAAA quando possível; se o texto trouxer um intervalo ou "prorrogado até", use a data final de inscrição.
- area só se aplica quando escolaridade_minima for "superior"; se for superior mas a área não for especificada, use "qualquer". Para os demais casos, use null.
- nota_ciencia_computacao é uma nota de 1 a 10 indicando o quão interessante é esse concurso para alguém de 22 anos, recém-formado em Ciência da Computação, considerando remuneração, área de atuação e requisitos de escolaridade. justificativa_nota é uma frase curta explicando a nota.
- Não invente informações que não estejam no texto fornecido. Use null quando a informação não estiver disponível."""


def extrair_dados_concurso(resumo_listagem: str, texto_detalhes: str, link: str) -> dict:
    """Envia o texto do concurso para o Claude e retorna os dados extraídos em um dicionário."""
    cliente = _obter_cliente()

    conteudo_usuario = (
        f"Link do concurso: {link}\n\n"
        f"Resumo da listagem:\n{resumo_listagem}\n\n"
        f"Texto completo da página do concurso:\n{texto_detalhes[:LIMITE_CARACTERES_TEXTO]}"
    )

    try:
        resposta = cliente.messages.create(
            model=MODELO,
            max_tokens=2048,
            system=PROMPT_SISTEMA,
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_CONCURSO}},
            messages=[{"role": "user", "content": conteudo_usuario}],
        )
    except anthropic.APIError as erro:
        raise ErroDeExtracao(f"Falha ao chamar a API da Anthropic: {erro}") from erro

    if resposta.stop_reason == "refusal":
        raise ErroDeExtracao(f"Extração recusada pelo modelo para o link {link}")

    try:
        texto = next(bloco.text for bloco in resposta.content if bloco.type == "text")
        dados = json.loads(texto)
    except (StopIteration, json.JSONDecodeError) as erro:
        raise ErroDeExtracao(f"Resposta do modelo não é um JSON válido para o link {link}: {erro}") from erro

    if not dados.get("link_edital"):
        dados["link_edital"] = link

    return dados
