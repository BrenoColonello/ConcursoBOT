import logging
import sys

from scraper.pci_concursos import buscar_concursos_abertos, buscar_texto_detalhes

if sys.stdout.encoding.lower() != "utf-8":
    sys.stdout.reconfigure(encoding="utf-8")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")


def main() -> None:
    concursos = buscar_concursos_abertos()
    print(f"\n{len(concursos)} concursos encontrados na listagem.\n")

    for concurso in concursos[:5]:
        print("-" * 80)
        print(f"Órgão: {concurso.orgao}")
        print(f"Estado: {concurso.estado}")
        print(f"Vagas: {concurso.vagas_texto}")
        print(f"Cargo: {concurso.cargo_texto}")
        print(f"Escolaridade: {concurso.escolaridade_texto}")
        print(f"Inscrição até: {concurso.data_inscricao_texto}")
        print(f"Link: {concurso.link}")

    if concursos:
        print("\n--- Testando extração de detalhes do primeiro concurso ---\n")
        texto = buscar_texto_detalhes(concursos[0].link)
        print(texto[:1000])


if __name__ == "__main__":
    main()
