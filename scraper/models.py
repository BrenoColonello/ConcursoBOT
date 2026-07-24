from dataclasses import dataclass
from typing import Optional


@dataclass
class ConcursoResumo:
    """Dados extraídos da listagem de concursos abertos do PCI Concursos."""

    titulo: str
    orgao: str
    link: str
    estado: Optional[str]
    vagas_texto: str
    cargo_texto: str
    escolaridade_texto: str
    data_inscricao_texto: str
