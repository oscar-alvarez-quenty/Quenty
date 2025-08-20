from jinja2 import Template
from weasyprint import HTML, CSS
from src.utils.Operators.default import _HTML_TEMPLATE_DEFAULT
from src.utils.Operators.deprisa import _HTML_TEMPLATE_DEPRISA
from src.utils.Operators.servientrega import _HTML_TEMPLATE_SERVIENTREGA
from src.utils.Operators.dhl import _HTML_TEMPLATE_DHL
from src.utils.Operators.pasarex import _HTML_TEMPLATE_PASAREX
from src.utils.Operators.fedex import _HTML_TEMPLATE_FEDEX
from src.utils.barcode_helper import generate_barcode_svg

def generate_label_html(data: dict, format_type: int) -> str:
    """
    Genera el HTML para una etiqueta, basado en los datos y formato especificado.
    """

    # 1 pulgada = 96 px
    if format_type == 1:
        width, height = int(4 * 96), int(6 * 96)  # 4x6 pulgadas
    elif format_type == 2:
        width, height = int(7 * 96), int(4.5 * 96)  # 7x4.5 pulgadas
    else:
        width, height = int(7 * 96), int(4.5 * 96)  # fallback

    operador = data.get("shipping_operator", "").strip().lower()
    if operador == "deprisa":
        template_str = _HTML_TEMPLATE_DEPRISA
        font = 9
        if format_type ==2:
            font = 6
    elif operador == "servientrega":
        template_str = _HTML_TEMPLATE_SERVIENTREGA
        font = 9.8
        if format_type ==2:
            font = 6.8
    elif operador == "pasarex":
        template_str = _HTML_TEMPLATE_PASAREX
        font = 10.6
        if format_type ==2:
            font = 6
    elif operador == "dhl":
        template_str = _HTML_TEMPLATE_DHL
        font = 9.5
        if format_type ==2:
            font = 7
    elif operador == "fedex":
        template_str = _HTML_TEMPLATE_FEDEX
        font = 11.5
        if format_type ==2:
           font = 7.5
    else:
        template_str = _HTML_TEMPLATE_DEFAULT
    
    # Generar código de barras en SVG
    barcode_svg = generate_barcode_svg(data.get("barcode", ""))

    template = Template(template_str)
    html_out = template.render(
        operador=data.get("shipping_operator", ""),
        tipo_servicio=data.get("shipping_service", ""),
        tipo_pago=data.get("payment_type", ""),
        no_guide=data.get("no_guide", ""),
        fecha_recepcion=data.get("fecha_recepcion", ""),
        hora_recepcion=data.get("hora_recepcion", ""),
        fecha_estimada_entrega=data.get("fecha_estimada_entrega", ""),
        peso_fisico=data.get("peso_fisico", ""),
        peso_volumetrico=data.get("peso_volumetrico", ""),
        pieza=data.get("pieza", ""),
        total_piezas=data.get("total_piezas", data.get("pieza", 1)),
        descripcion_contenido=data.get("descripcion_contenido", ""),
        destinatario=data.get("destinatario", {}),
        remitente=data.get("remitente", {}),
        barcode_svg=barcode_svg,
        format_type=format_type,
        width=width,
        height=height,
        font =font,
        destino=data.get("destino", ""),
        zona=data.get("zona", ""),
        observaciones=data.get("observaciones", ""),
    )

    return html_out
