from typing import List
from src.utils.guia_provider import get_data
from src.utils.pdf_generator import _HTML_TEMPLATE  # plantilla HTML completa
from jinja2 import Template
from weasyprint import HTML, CSS
from src.utils.barcode_helper import generate_barcode_svg

class LabelService:
    @staticmethod
    async def generate_labels(envio_ids: List[int], format_type: int) -> bytes:
        if not envio_ids:
            raise ValueError("No se recibieron IDs de envíos")

        etiquetas_html = []
        # Medidas para formato (alto x ancho) en px (96 dpi)
        if format_type == 1:
            height, width = 7 * 96, 4.5 * 96
            font_size = 10
        elif format_type == 2:
            height, width = 4 * 96, 6 * 96
            font_size = 8
        else:
            height, width = 7 * 96, 4.5 * 96
            font_size = 10

        for envio_id in envio_ids:
            data = await get_data(str(envio_id))
            if "total_piezas" not in data:
                data["total_piezas"] = data.get("pieza", 1)

            barcode_svg = generate_barcode_svg(data.get("barcode", ""))

            template = Template(_HTML_TEMPLATE)
            html_etiqueta = template.render(
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
                font_size=font_size,
                # Añadimos una clase para salto de página en cada etiqueta menos la última
                page_break_style="page-break-after: always;" 
            )
            etiquetas_html.append(f'<div style="width:{width}px; height:{height}px; { "page-break-after: always;" if envio_id != envio_ids[-1] else "" }">{html_etiqueta}</div>')

        # Unir todas las etiquetas en un solo HTML padre
        html_unido = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
        <meta charset="UTF-8" />
        <style>
            @page {{ size: {width}px {height}px; margin: 0; }}
            body {{ margin: 0; padding: 0; }}
        </style>
        </head>
        <body>
            {''.join(etiquetas_html)}
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_unido).write_pdf()
        return pdf_bytes
