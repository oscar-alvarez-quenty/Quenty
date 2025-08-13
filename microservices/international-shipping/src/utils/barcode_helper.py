from barcode import Code128
from barcode.writer import SVGWriter
from io import BytesIO

def generate_barcode_svg(code: str) -> str:
    """
    Genera un código de barras Code128 en formato SVG como string.
    """
    rv = BytesIO()
    barcode_obj = Code128(code, writer=SVGWriter())
    barcode_obj.write(rv)
    svg = rv.getvalue().decode("utf-8")
    # Eliminar la declaración XML para embebido limpio en HTML
    if svg.startswith('<?xml'):
        svg = svg.split('?>',1)[1]
    return svg
