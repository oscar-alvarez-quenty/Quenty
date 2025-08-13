from weasyprint import HTML, CSS
from jinja2 import Template
from src.utils.barcode_helper import generate_barcode_svg

_HTML_TEMPLATE = """

<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <style>
    * { box-sizing: border-box; }
    body { font-family: Arial, sans-serif; margin: 0; padding: 0; }
    .container {
      width: {{ width }}px;
      height: {{ height }}px;
      border: 1px solid #000;
      padding: 2px;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      table-layout: fixed;
    }
    td {
      border: 1px solid #000;
      padding: 2px 4px;
      vertical-align: top;
      word-wrap: break-word;
      overflow-wrap: break-word;
      white-space: normal;
      line-height: 1.1;
    }

    /* ===== Estilos configurables ===== */
    .label-text { font-size: 8px; font-weight: bold; }
    .normal-text { font-size: 9px; font-weight: normal; }
    .title-1 { font-size: 18px; font-weight: bold; text-align: center; }
    .title-2 { font-size: 14px; font-weight: bold; text-align: center; }
    .title-3 { font-size: 12px; font-weight: bold; }
    .title-4 { font-size: 10px; font-weight: bold; }
    .center { text-align: center; }

    /* Barras de código */
    .barcode {
      text-align: center;
      padding-top: 4px;
    }
    .barcode-large {
      text-align: center;
      vertical-align: middle;
    }
    .barcode-large-2 {
      text-align: center;
      vertical-align: middle;
    }

    /* Ajuste automático si el texto es muy largo */
    td.auto-shrink {
      font-size: clamp(7px, 1.5vw, 10px);
    }
  </style>
</head>
<body>
<div class="container">

{% if format_type == 1 %}
<!-- ===== FORMATO 1 (7x4.5 in) ===== -->
<table>
  <!-- Operador y Servicio -->
  <tr>
    <td rowspan="2" colspan="3" class="title-2">{{ operador }}</td>
    <td rowspan="1" colspan="3" class="title-2">{{ tipo_servicio }}</td>
  </tr>

  <!-- Número de guía -->
  <tr>
    <td rowspan="1" colspan="3" class="title-2">{{ tipo_pago }}</td>
  </tr>
  <tr>
    <td colspan="6" class="title-1">{{ no_guide }}</td>
  </tr>

  <!-- Fechas -->
  <tr>
    <td class="label-text center">Recepción</td>
    <td colspan="2" class="normal-text center">{{ fecha_recepcion }} {{ hora_recepcion }}</td>
    <td class="label-text center">Entrega</td>
    <td colspan="2" class="normal-text center">{{ fecha_estimada_entrega }}</td>
  </tr>

  <!-- Pesos y piezas -->
  <tr>
    <td colspan="2" class="label-text center">Peso Físico</td>
    <td colspan="2" class="label-text center">Peso Vol</td>
    <td colspan="2" class="label-text center">Piezas</td>
  </tr>
  <tr>
    <td colspan="2" class="normal-text center">{{ peso_fisico }} Kg</td>
    <td colspan="2" class="normal-text center">{{ peso_volumetrico }} Kg</td>
    <td colspan="2" class="normal-text center">{{ pieza }}/{{ total_piezas }}</td>
  </tr>

  <!-- Contenido -->
  <tr>
    <td colspan="6" class="title-3 center">Contenido</td>
  </tr>
  <tr>
    <td colspan="6" class="normal-text">{{ descripcion_contenido }}</td>
  </tr>

  <!-- Destinatario -->
  <tr>
    <td colspan="6" class="title-3 center">Destinatario</td>
  </tr>
  <tr>
    <td class="label-text">Nombre</td>
    <td colspan="5" class="normal-text">{{ destinatario.nombre }}</td>
  </tr>
  <tr>
    <td class="label-text">Teléfono</td>
    <td colspan="2" class="normal-text">{{ destinatario.telefono }}</td>
    <td class="label-text">Email</td>
    <td colspan="2" class="normal-text">{{ destinatario.email }}</td>
  </tr>
  <tr>
    <td class="label-text">Dirección</td>
    <td colspan="5" class="normal-text">{{ destinatario.direccion }}</td>
  </tr>
  <tr>
    <td class="label-text">País</td>
    <td colspan="2" class="normal-text">{{ destinatario.pais }}</td>
    <td class="label-text">Código Postal</td>
    <td colspan="2" class="normal-text">{{ destinatario.codigo_postal }}</td>
  </tr>
  <tr>
    <td class="label-text">Ciudad</td>
    <td colspan="5" class="normal-text">{{ destinatario.ciudad }}</td>
  </tr>

  <!-- Remitente -->
  <tr>
    <td colspan="6" class="title-3 center">Remitente</td>
  </tr>
  <tr>
    <td class="label-text">Nombre</td>
    <td colspan="5" class="normal-text">{{ remitente.nombre }}</td>
  </tr>
  <tr>
    <td class="label-text">Teléfono</td>
    <td colspan="2" class="normal-text">{{ remitente.telefono }}</td>
    <td class="label-text">Email</td>
    <td colspan="2" class="normal-text">{{ remitente.email }}</td>
  </tr>
  <tr>
    <td class="label-text">Dirección</td>
    <td colspan="5" class="normal-text">{{ remitente.direccion }}</td>
  </tr>
  <tr>
    <td class="label-text">País</td>
    <td colspan="2" class="normal-text">{{ remitente.pais }}</td>
    <td class="label-text">Código Postal</td>
    <td colspan="2" class="normal-text">{{ remitente.codigo_postal }}</td>
  </tr>
  <tr>
    <td class="label-text">Ciudad</td>
    <td colspan="5" class="normal-text">{{ remitente.ciudad }}</td>
  </tr>

  <!-- Barcode -->
  <tr>
    <td colspan="6" class="barcode-large">{{ barcode_svg | safe }}</td>
  </tr>
</table>

{% elif format_type == 2 %}
<table>
  <!-- Operador (2 filas) y Tipo Servicio / Tipo Pago -->
  <tr>
    <td colspan="6" rowspan="2" class="title-2">{{ operador }}</td>
    <td colspan="6" class="title-2">{{ tipo_servicio }}</td>
  </tr>
  <tr>
    <td colspan="6" class="title-2">{{ tipo_pago }}</td>
  </tr>

  <!-- Número de guía -->
  <tr>
    <td colspan="6" class="title-1">{{ no_guide }}</td>

    <!-- Peso Físico y Peso Volumétrico -->
    <td class="label-text center" rowspan="2">Peso Físico</td>
    <td colspan="2" rowspan="2" class="normal-text center">{{ peso_fisico }} Kg</td>
    <td class="label-text center" rowspan="2">Peso Vol</td>
    <td colspan="2" rowspan="2" class="normal-text center">{{ peso_volumetrico }} Kg</td>
  </tr>

  <!-- Datos destinatario fila 1 -->
  <tr>
    <td class="label-text">Nombre</td>
    <td colspan="5" class="normal-text">{{ destinatario.nombre }}</td>
  </tr>

  <!-- Datos destinatario fila 2 -->
  <tr>
    <td class="label-text">Teléfono</td>
    <td colspan="2" class="normal-text">{{ destinatario.telefono }}</td>
    <td class="label-text">Email</td>
    <td colspan="2" class="normal-text">{{ destinatario.email }}</td>

    <!-- Piezas -->
    <td class="label-text center" rowspan="2">Piezas</td>
    <td colspan="2" rowspan="2" class="normal-text center">{{ pieza }}/{{ total_piezas }}</td>

    <!-- Recepción -->
    <td class="label-text center">Recepción</td>
    <td colspan="2" class="normal-text center">{{ fecha_recepcion }} {{ hora_recepcion }}</td>
  </tr>

  <!-- Datos destinatario fila 3 -->
  <tr>
    <td class="label-text">Dirección</td>
    <td colspan="5" class="normal-text">{{ destinatario.direccion }}</td>

    <td class="label-text center">Entrega</td>
    <td colspan="2" class="normal-text center">{{ fecha_estimada_entrega }}</td>
  </tr>

  <!-- Datos destinatario fila 4 -->
  <tr>
    <td class="label-text">País</td>
    <td colspan="2" class="normal-text">{{ destinatario.pais }}</td>
    <td class="label-text">Código Postal</td>
    <td colspan="2" class="normal-text">{{ destinatario.codigo_postal }}</td>

    <!-- Código de barras -->
    <td colspan="6" rowspan="7" class="barcode-large-2">{{ barcode_svg | safe }}</td>
  </tr>

  <!-- Ciudad -->
  <tr>
    <td class="label-text">Ciudad</td>
    <td colspan="5" class="normal-text">{{ destinatario.ciudad }}</td>
  </tr>

  <!-- Remitente -->
  <tr>
    <td colspan="6" class="title-3 center">Remitente</td>
  </tr>
  
  <tr>
    <td class="label-text">Nombre</td>
    <td colspan="5" class="normal-text">{{ remitente.nombre }}</td>
  </tr>

  <tr>
    <td class="label-text">Teléfono</td>
    <td colspan="2" class="normal-text">{{ remitente.telefono }}</td>
    <td class="label-text">Email</td>
    <td colspan="2" class="normal-text">{{ remitente.email }}</td>
  </tr>

  <tr>
    <td class="label-text">Dirección</td>
    <td colspan="5" class="normal-text">{{ remitente.direccion }}</td>
  </tr>

  <tr>
    <td class="label-text">País</td>
    <td colspan="2" class="normal-text">{{ remitente.pais }}</td>
    <td class="label-text">Código Postal</td>
    <td colspan="2" class="normal-text">{{ remitente.codigo_postal }}</td>
  </tr>
</table>

{% endif %}
</div>
</body>
</html>
"""

def generate_label_html(data: dict, format_type: int) -> bytes:
    """
    Genera PDF con WeasyPrint usando plantilla HTML + CSS.
    Incluye código de barras SVG embebido.
    """
    # 1 pulgada = 96 px
    if format_type == 1:
        width, height = int(7 * 96), int(4.5 * 96)
        font_size = 4
    elif format_type == 2:
        width, height = int(4 * 96), int(6 * 96)
        font_size = 4
    else:
        width, height = int(7 * 96), int(4.5 * 96)
        font_size = 4

    barcode_svg = generate_barcode_svg(data.get("barcode", ""))

    template = Template(_HTML_TEMPLATE)
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
        font_size=font_size,
    )

    pdf = HTML(string=html_out).write_pdf(
        stylesheets=[CSS(string=f'@page {{ size: {width}px {height}px; margin: 0 }}')]
    )

    return pdf
