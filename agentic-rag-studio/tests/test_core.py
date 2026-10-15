import io
import pytest
from pypdf import PdfWriter
from agentic_rag import Page, Evidence, read_pdfs, split_pages, evaluate_retrieval

def test_reject_non_pdf():
    with pytest.raises(ValueError, match="only PDF"):
        read_pdfs([("notes.txt", b"not pdf")])

def test_empty_pdf():
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buffer = io.BytesIO()
    writer.write(buffer)
    with pytest.raises(ValueError, match="readable text"):
        read_pdfs([("blank.pdf", buffer.getvalue())])

def test_chunk_metadata():
    chunks = split_pages([Page("report.pdf", 3, "finance " * 200)], 180, 40)
    assert len(chunks) > 3
    assert all(c.page == 3 and c.source == "report.pdf" for c in chunks)
    assert len(set(c.id for c in chunks)) == len(chunks)

class FakeIndex:
    def search(self, question, k=5):
        return [Evidence("id", "report.pdf", 2, "revenue was 42 million", 0.1)]

def test_retrieval_metrics():
    metrics, rows = evaluate_retrieval(FakeIndex(), [{"question":"Revenue?","expected_text":"revenue"}, {"question":"Risk?","expected_source":"else.pdf"}])
    assert metrics["hit_at_k"] == 0.5
    assert metrics["mrr_at_k"] == 0.5
    assert rows[0]["rank"] == 1

def test_missing_labels():
    with pytest.raises(ValueError, match="expected label"):
        evaluate_retrieval(FakeIndex(), [{"question":"Question"}])
