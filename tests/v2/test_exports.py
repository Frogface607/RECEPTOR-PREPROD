from receptor_agent.llm.pipeline import run_pipeline, ProfileInput
from receptor_agent.exports.iiko_csv import techcard_to_csv
from receptor_agent.exports.xlsx import techcard_to_xlsx
from receptor_agent.exports.pdf import techcard_to_pdf
from receptor_agent.exports.zipper import make_zip

def _card():
    p = ProfileInput(name="EDISON", cuisine="мексиканская")
    return run_pipeline(p).card

def test_csv():
    c = _card()
    s = techcard_to_csv(c)
    assert "dish_name" in s and c.meta.name in s

def test_xlsx():
    c = _card()
    b = techcard_to_xlsx(c)
    assert isinstance(b, (bytes, bytearray)) and len(b) > 100

def test_pdf():
    c = _card()
    b = techcard_to_pdf(c)
    assert isinstance(b, (bytes, bytearray)) and len(b) > 1000

def test_zip():
    data = make_zip({"a.txt": b"hello", "b.bin": b"\x01"})
    assert isinstance(data, (bytes, bytearray)) and len(data) > 20