from pathlib import Path
import pytest
from src.pdf_processor import extract_pdf_pages

PDF_DIGITAL = Path(__file__).resolve().parents[1] / "data" / "pdfs" / "atendimentos_digitais.pdf"
PDF_ESCANEADO = Path(__file__).resolve().parents[1] / "data" / "pdfs" / "atendimentos_digitalizados.pdf"

pytestmark = pytest.mark.skipif(not PDF_DIGITAL.exists(), reason="PDFs oficiais não disponíveis neste checkout")


def test_extract_pdf_pages_returns_one_entry_per_page():
    pages = extract_pdf_pages(PDF_DIGITAL)
    assert len(pages) > 0
    for page in pages:
        assert set(page.keys()) == {"pagina", "texto", "metodo"}
        assert page["metodo"] in ("extracao_direta", "ocr_pendente")


def test_pdf_with_selectable_text_uses_direct_extraction():
    pages = extract_pdf_pages(PDF_DIGITAL, min_chars=40)
    assert all(p["metodo"] == "extracao_direta" for p in pages)
    assert all(len(p["texto"]) >= 40 for p in pages)


def test_scanned_pdf_is_routed_to_ocr():
    """atendimentos_digitalizados.pdf é composto por imagens (RF02): sem texto
    selecionável suficiente, toda página deve ser marcada para OCR."""
    if not PDF_ESCANEADO.exists():
        pytest.skip("PDF escaneado não disponível")
    pages = extract_pdf_pages(PDF_ESCANEADO, min_chars=40)
    assert all(p["metodo"] == "ocr_pendente" for p in pages)


def test_min_chars_threshold_controls_routing():
    """Com um limite absurdamente alto, até texto selecionável real vira ocr_pendente."""
    pages = extract_pdf_pages(PDF_DIGITAL, min_chars=10**6)
    assert all(p["metodo"] == "ocr_pendente" for p in pages)
