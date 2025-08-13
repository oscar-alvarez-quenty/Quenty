from io import BytesIO
import base64
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.graphics.shapes import Drawing, Line
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.responsibility_data_provider import get_responsibility_data
from src.services.signature_service import SignatureService


class ResponsibilityLetterService:
    @staticmethod
    async def generate_pdf(envio_id: str, language: str, db: AsyncSession) -> bytes:
        data = get_responsibility_data(envio_id)

        # 1. Obtener firma
        signature_service = SignatureService(db)
        try:
            signature = await signature_service.get_by_client_id(data["client_name"])
            signature_base64 = signature.image_base64
        except Exception:
            signature_base64 = None

        # 2. Encabezado dinámico según idioma
        if language == "esp":
            header_text = (
                f"{data['shipping_operator']} INTERNACIONAL LTDA advierte a sus usuarios de transporte de "
                "paquetes y muestras que es ilegal y se encuentra sancionado por las leyes de Colombia e "
                "Internacionales, embarcar o transportar drogas heroicas, narcóticos (marihuana, cocaína, "
                "heroína, etc.) o cualquier otro material prohibido por la ley."
            )
        else:
            header_text = (
                f"{data['shipping_operator']} INTERNATIONAL LTD warns its shipping customers that it is "
                "illegal and punishable under Colombian and International law to ship or transport "
                "narcotics (marijuana, cocaine, heroin, etc.) or any other material prohibited by law."
            )

        # 3. Cuerpo de la carta
        if language == "esp":
            letter_text = f"""
{data['ciudad_remitente']}, {data['created_at']}<br/><br/>
<b>CARTA DE RESPONSABILIDAD</b><br/><br/>
Yo, <b>{data["client_name"]}</b> identificado con la {data["client_document_type"]} No. <b>{data["client_document_number"]}</b> expedida en 
{data["ciudad_remitente"]} y actuando como representante de <b>{data["client_name"]}</b> autorizo a {data["shipping_operator"]} Internacional Ltda. 
a efectuar revisión total del contenido si lo considera necesario en sus bodegas y antes del embarque.<br/><br/>
Certifico que el contenido de la presente carga se ajusta a lo declarado en la Guía Número <b>{data["no_guide"]}</b> y de la cual me hago 
directamente responsable ante las autoridades Nacionales y Extranjeras, declarando que el manejo del envío por parte mía, cesa en el momento que hago entrega del mismo a {data["shipping_operator"].upper()} INTERNACIONAL LTDA.<br/><br/>
Declaro conocer las normas postales aplicables a la empresa de Mensajería Especializada y en especial las referentes a la posibilidad 
de que los envíos sean abiertos y revisados por las autoridades aduaneras y de policía.<br/><br/>
Atentamente:<br/><br/>
"""
        else:
            letter_text = f"""
{data['ciudad_remitente']}, {data['created_at']}<br/><br/>
<b>RESPONSIBILITY LETTER</b><br/><br/>
I, <b>{data["client_name"]}</b>, identified with {data["client_document_type"]} No. <b>{data["client_document_number"]}</b> issued in 
{data["ciudad_remitente"]} and acting as representative of <b>{data["client_name"]}</b>, authorize {data["shipping_operator"]} International Ltd. 
to carry out a complete inspection of the contents if deemed necessary in its warehouses and prior to shipment.<br/><br/>
I certify that the contents of this shipment match what is declared in the Waybill Number <b>{data["no_guide"]}</b> and for which I take full 
responsibility before the National and Foreign authorities, declaring that the handling of the shipment on my part ceases at the moment 
I deliver it to {data["shipping_operator"].upper()} INTERNATIONAL LTD.<br/><br/>
I declare that I am aware of the postal regulations applicable to the Specialized Courier Company, particularly those regarding the 
possibility that shipments may be opened and inspected by customs and police authorities.<br/><br/>
Sincerely:<br/><br/>
"""

        # 4. Crear PDF con formato
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=A4,
            rightMargin=50,
            leftMargin=50,
            topMargin=50,
            bottomMargin=50
        )

        styles = getSampleStyleSheet()
        styles.add(ParagraphStyle(name="Justify", alignment=TA_JUSTIFY, leading=14))

        elements = []

        # Encabezado
        elements.append(Paragraph(header_text, styles["Justify"]))
        elements.append(Spacer(1, 20))

        # Cuerpo
        elements.append(Paragraph(letter_text, styles["Justify"]))
        elements.append(Spacer(1, 10))

        # Firma debajo de "Atentamente" / "Sincerely"
        if signature_base64:
            try:
                if signature_base64.startswith("data:image"):
                    signature_base64 = signature_base64.split(",", 1)[1]
                signature_data = base64.b64decode(signature_base64)
                sig_buffer = BytesIO(signature_data)

                signature_img = Image(sig_buffer, width=150, height=50, hAlign='LEFT')
                elements.append(signature_img)
                elements.append(Spacer(1, 5))
            except Exception as e:
                print(f"Error decoding signature: {e}")
                elements.append(Spacer(1, 55))
        else:
            elements.append(Spacer(1, 55))

        # Línea bajo la firma
        line = Drawing(400, 1)
        line.add(Line(0, 0, 200, 0))
        elements.append(line)
        elements.append(Spacer(1, 10))

        # Datos del firmante según idioma
        if language == "esp":
            footer_text = f"""
C.C. No. {data["client_document_number"]}<br/>
Nombre de la Compañía: {data["client_name"]}<br/>
Dirección: {data["client_address"]}<br/>
Teléfono: {data["client_telefono"]}
"""
        else:
            footer_text = f"""
ID No. {data["client_document_number"]}<br/>
Company Name: {data["client_name"]}<br/>
Address: {data["client_address"]}<br/>
Phone: {data["client_telefono"]}
"""
        elements.append(Paragraph(footer_text, styles["Justify"]))

        # Construir PDF
        doc.build(elements)
        buffer.seek(0)
        return buffer.read()
