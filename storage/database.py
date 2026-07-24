import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)

CAMINHO_BANCO = Path(__file__).resolve().parent.parent / "dados" / "concursos.db"


@contextmanager
def _conexao() -> Iterator[sqlite3.Connection]:
    CAMINHO_BANCO.parent.mkdir(parents=True, exist_ok=True)
    conexao = sqlite3.connect(CAMINHO_BANCO)
    try:
        yield conexao
        conexao.commit()
    finally:
        conexao.close()


def inicializar_banco() -> None:
    """Cria a tabela de controle de concursos já processados, se ainda não existir."""
    with _conexao() as conexao:
        conexao.execute(
            """
            CREATE TABLE IF NOT EXISTS concursos_processados (
                link TEXT PRIMARY KEY,
                orgao TEXT NOT NULL,
                processado_em TEXT NOT NULL DEFAULT (datetime('now'))
            )
            """
        )
    logger.info("Banco de dados pronto em %s", CAMINHO_BANCO)


def ja_processado(link: str) -> bool:
    """Verifica se um concurso (identificado pelo link) já foi processado antes."""
    with _conexao() as conexao:
        cursor = conexao.execute(
            "SELECT 1 FROM concursos_processados WHERE link = ?", (link,)
        )
        return cursor.fetchone() is not None


def marcar_como_processado(link: str, orgao: str) -> None:
    """Registra um concurso como processado, para não ser reenviado em execuções futuras."""
    with _conexao() as conexao:
        conexao.execute(
            "INSERT OR IGNORE INTO concursos_processados (link, orgao) VALUES (?, ?)",
            (link, orgao),
        )
    logger.debug("Marcado como processado: %s (%s)", orgao, link)
