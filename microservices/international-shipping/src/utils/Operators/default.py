_HTML_TEMPLATE_DEFAULT = """
  <style>
    .logo-container {
      text-align: right;
      margin-right: 10px; /* Ajusta según lo necesites */
      margin-top: 5px;
      margin-bottom: 10px;
    }

    .logo-container img {
      height: 25px; /* Ajusta el tamaño del logo si es necesario */
    }
  </style>
  
  <style>
    * {
      box-sizing: border-box;
    }

    body {
      font-family: Arial, sans-serif;
      margin: 0;
      padding: 0;
    }

    .container {
      width: {{width}}

      px;

      height: {{height}}

      px;
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
      margin-top: 2px !important;
      margin-bottom: 2px !important;
    }

    /* ===== Estilos configurables ===== */
    .label-text-2 {
      font-size: 7px !important;
      font-weight: bold;
    }
    .label-text-3 {
      font-size: 6.5px !important;
      font-weight: bold;
    }

    .label-text {
      font-size: 8px !important;
      font-weight: bold;
    }

    .normal-text {
      font-size: 10px !important;
      font-weight: normal;
    }

    .peso-text {
      font-size: 18px !important;
      font-weight: bold;
    }

    .title-1 {
      font-size: 22px !important;
      font-weight: bold;
      text-align: center;
    }

    .title-2 {
      font-size: 18px !important;
      font-weight: bold;
      text-align: center;
    }

    .title-3 {
      font-size: 14px !important;
      font-weight: bold;
    }

    .title-4 {
      font-size: 11px !important;
      font-weight: bold;
    }

    .center {
      text-align: center;
    }

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

<body>
  <div class="container">
    <div class="logo-container">
      <img src="https://quenty.co/wp-content/uploads/2024/01/logo-quenty.svg" alt="Logo Quenty">
    </div>

    {% if format_type == 1 %}
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

        <td class="label-text-3 center">Contenido</td>
        <td colspan="5" class="normal-text">{{ descripcion_contenido }}</td>
      </tr>

      <!-- Datos destinatario fila 1 -->
      <tr>
        <td colspan="6" class="title-3 center">Destinatario</td>
        <!-- Peso Físico y Peso Volumétrico -->
        <td class="label-text-2 center" rowspan="2">Peso Físico</td>
        <td colspan="2" rowspan="2" class="peso-text center">{{ peso_fisico }}</td>
        <td class="label-text-2 center" rowspan="2">Peso Vol</td>
        <td colspan="2" rowspan="2" class="peso-text center">{{ peso_volumetrico }}</td>
      </tr>
      <tr>
        <td class="label-text-2">Nombre</td>
        <td colspan="5" class="normal-text">{{ destinatario.nombre }}</td>
      </tr>

      <!-- Datos destinatario fila 2 -->
      <tr>
        <td class="label-text-2">Teléfono</td>
        <td colspan="2" class="normal-text">{{ destinatario.telefono }}</td>
        <td class="label-text-2">Email</td>
        <td colspan="2" class="normal-text">{{ destinatario.email }}</td>

        <!-- Piezas -->
        <td class="label-text-2 center" rowspan="2">Piezas</td>
        <td colspan="2" rowspan="2" class="peso-text center">{{ pieza }}/{{ total_piezas }}</td>

        <!-- Recepción -->
        <td class="label-text-2 center">Recepción</td>
        <td colspan="2" class="normal-text center">{{ fecha_recepcion }} {{ hora_recepcion }}</td>
      </tr>

      <!-- Datos destinatario fila 3 -->
      <tr>
        <td class="label-text-2">Dirección</td>
        <td colspan="5" class="normal-text">{{ destinatario.direccion }}</td>

        <td class="label-text-2 center">Entrega</td>
        <td colspan="2" class="normal-text center">{{ fecha_estimada_entrega }}</td>
      </tr>

      <!-- Datos destinatario fila 4 -->
      <tr>
        <td class="label-text-2">País</td>
        <td colspan="2" class="normal-text">{{ destinatario.pais }}</td>
        <td class="label-text-2">Código Postal</td>
        <td colspan="2" class="normal-text">{{ destinatario.codigo_postal }}</td>

        <!-- Código de barras -->
        <td colspan="6" rowspan="8" class="barcode-large-2">{{ barcode_svg | safe }}</td>
      </tr>

      <!-- Ciudad -->
      <tr>
        <td class="label-text-2">Ciudad</td>
        <td colspan="5" class="normal-text">{{ destinatario.ciudad }}</td>
      </tr>

      <!-- Remitente -->
      <tr>
        <td colspan="6" class="title-3 center">Remitente</td>
      </tr>

      <tr>
        <td class="label-text-2">Nombre</td>
        <td colspan="5" class="normal-text">{{ remitente.nombre }}</td>
      </tr>

      <tr>
        <td class="label-text-2">Teléfono</td>
        <td colspan="2" class="normal-text">{{ remitente.telefono }}</td>
        <td class="label-text-2">Email</td>
        <td colspan="2" class="normal-text">{{ remitente.email }}</td>
      </tr>

      <tr>
        <td class="label-text-2">Dirección</td>
        <td colspan="5" class="normal-text">{{ remitente.direccion }}</td>
      </tr>

      <tr>
        <td class="label-text-2">País</td>
        <td colspan="2" class="normal-text">{{ remitente.pais }}</td>
        <td class="label-text-2">Código Postal</td>
        <td colspan="2" class="normal-text">{{ remitente.codigo_postal }}</td>
      </tr>
      <tr>
        <td class="label-text-2">Ciudad</td>
        <td colspan="5" class="normal-text">{{ remitente.ciudad }}</td>
      </tr>
    </table>
    {% elif format_type == 2 %}
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
        <td colspan="2" class="peso-text center">{{ peso_fisico }}</td>
        <td colspan="2" class="peso-text center">{{ peso_volumetrico }}</td>
        <td colspan="2" class="peso-text center">{{ pieza }}/{{ total_piezas }}</td>
      </tr>

      <!-- Contenido -->
      <tr>
        <td colspan="1" class="label-text">Contenido</td>
        <td colspan="5" class="normal-text">{{ descripcion_contenido }}</td>
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
    
    {% endif %}
  </div>
"""