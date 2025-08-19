from typing import List
from src.utils.guia_provider import get_data
from jinja2 import Template
from weasyprint import HTML, CSS
from src.utils.pdf_generator import generate_label_html

class LabelService:
    @staticmethod
    async def generate_labels(envio_ids: List[int], format_type: int) -> bytes:
        if not envio_ids:
            raise ValueError("No se recibieron IDs de envíos")

        etiquetas_html = []

        # Medidas por formato en píxeles (1 in = 96 px)
        if format_type == 1:
            width, height = int(4 * 96), int(6 * 96)  # 4x6 pulgadas
        elif format_type == 2:
            width, height = int(7 * 96), int(4.5 * 96)  # 7x4.5 pulgadas
        else:
            width, height = int(7 * 96), int(4.5 * 96)  # fallback

        for i, envio_id in enumerate(envio_ids):
            data = await get_data(str(envio_id))

            if "total_piezas" not in data:
                data["total_piezas"] = data.get("pieza", 1)

            html_etiqueta = generate_label_html(data, format_type)

            # Cada etiqueta se renderiza en su propio contenedor del mismo tamaño de página
            etiquetas_html.append(
                f'''
                <div style="width:{width}px; height:{height}px; page-break-after: always;">
                    {html_etiqueta}
                </div>
                '''
            )

        # Documento HTML completo
        html_unido = f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8" />
            <style>
                @page {{ size: {width}px {height}px; margin: 0; }}
                body {{ margin: 0; padding: 0; }}
                div {{ margin: 0; padding: 0; }}
            </style>
        </head>
        <body>
            {''.join(etiquetas_html)}
        </body>
        </html>
        """

        pdf_bytes = HTML(string=html_unido).write_pdf()
        return pdf_bytes
