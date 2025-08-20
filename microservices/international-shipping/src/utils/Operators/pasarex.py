_HTML_TEMPLATE_PASAREX = """
  <style>
    :root {
      --font-base-pasarex: {{ font }}px; 
    }

    .container-pasarex {
      width: {{ width }}px;
      height: {{ height }}px;
      padding: 5px;
      border: 1px solid black;
      overflow: hidden;
      box-sizing: border-box;
      font-size: var(--font-base-pasarex);
      page-break-inside: avoid !important;
      page-break-after: always !important;
    }

    .encabezado-tabla-pasarex {
      width: 100%;
      border-collapse: collapse;
      margin-bottom: 5px;
      font-size: var(--font-base-pasarex);
    }

    .encabezado-tabla-pasarex td,
    .encabezado-tabla-pasarex th {
      font-size: var(--font-base-pasarex);
    }

    .logo-pasarex img {
      height: 30px;
    }

    .logo-pasarex div {
      font-size: calc(var(--font-base-pasarex) * 1.3);
    }

    .centro-pasarex {
      text-align: center;
      font-size: calc(var(--font-base-pasarex) * 1.8);
      font-weight: bold;
    }

    .derecha-pasarex {
      text-align: right;
      font-size: calc(var(--font-base-pasarex) * 1.5);
    }

    .awb-section-pasarex {
      border: 1px solid black;
      padding: 8px;
      font-size: calc(var(--font-base-pasarex) * 1.8);
      font-weight: bold;
      text-align: center;
      margin-bottom: 5px;
    }

    .info-envio-pasarex {
      display: flex;
      justify-content: space-between;
      margin-bottom: 5px;
      border: 1px solid black;
      font-size: var(--font-base-pasarex);
    }

    .info-envio-pasarex div {
      flex: 1;
      border-right: 1px solid black;
      padding: 5px;
      text-align: center;
      font-size: var(--font-base-pasarex);
    }

    .info-envio-pasarex div:last-child {
      border-right: none;
    }

    .info-envio-pasarex strong {
      display: block;
      font-size: calc(var(--font-base-pasarex) * 1.2);
      color: #333;
    }

    .info-envio-pasarex span {
      font-size: calc(var(--font-base-pasarex) * 1.6);
      font-weight: bold;
      color: #000;
    }

    .content-pasarex {
      margin: 5px 0;
      font-size: var(--font-base-pasarex);
    }

    .content-pasarex strong {
      text-transform: uppercase;
      font-size: calc(var(--font-base-pasarex) * 1.2);
    }

    .seccion-pasarex {
      border: 1px solid black;
      margin-bottom: 4px;
      padding: 8px;
      font-size: var(--font-base-pasarex);
    }

    .titulo-seccion-pasarex {
      font-weight: bold;
      margin-bottom: 2px;
      border-bottom: 1px solid black;
      padding-bottom: 2px;
      text-transform: uppercase;
      font-size: calc(var(--font-base-pasarex) * 1.3);
    }

    .datos-pasarex p {
      margin: 2px 0;
      font-size: var(--font-base-pasarex);
    }

    .codigo-barras-pasarex {
      border: 1px solid black;
      margin-bottom: 2px;
      padding: 4px 0;
      font-size: var(--font-base-pasarex);
    }

    .barcode-pasarex {
      text-align: center;
      margin-top: 2px;
    }

    .barcode-pasarex img {
      height: calc(var(--font-base-pasarex) * 1.5); /* antes fijo 25px */
    }

    .barcode-label-pasarex {
      text-align: center;
      font-size: calc(var(--font-base-pasarex) * 2.2);
      font-weight: bold;
    }

    .footer-pasarex {
      text-align: center;
      font-size: calc(var(--font-base-pasarex) * 1.3);
      margin-top: 2px;
    }

    .footer-pasarex a {
      font-size: calc(var(--font-base-pasarex) * 1.1);
      text-decoration: none;
    }
  </style>
<div class="container-pasarex">

  <!-- Encabezado -->
  <table class="encabezado-tabla-pasarex">
    <tr>
      <td class="logo-pasarex" style="width: 33%;">
        <img src="https://pasarex.com/wp-content/uploads/2024/11/Pasarex.svg" alt="Pasarex Logo">
        <div>Logística de confianza</div>
      </td>
      <td class="centro-pasarex" style="width: 33%;">
        {{ codigo_ruta }}
      </td>
      <td class="derecha-pasarex" style="width: 33%;">
        <div>{{ tipo_paquete }}</div>
        <div>{{ tipo_servicio }}</div>
      </td>
    </tr>
  </table>

  <!-- AWB -->
  <div class="awb-section-pasarex">
    AWB: {{ awb }}
  </div>

  <!-- Info de envío -->
  <div class="info-envio-pasarex">
    <div>
      <strong>Volumetric weight:</strong>
      <span>{{ peso_volumetrico }} kg</span>
    </div>
    <div>
      <strong>Physical weight:</strong>
      <span>{{ peso_fisico }} kg</span>
    </div>
    <div>
      <strong>Pieces:</strong>
      <span>{{ pieza_actual }}/{{ total_piezas }}</span>
    </div>
    <div>
      <strong>Date:</strong>
      <span>{{ fecha_envio }}</span>
    </div>
  </div>

  <!-- Contenido -->
  <div class="content-pasarex">
    <strong>Content:</strong> {{ contenido }}
  </div>

  <!-- Remitente -->
  <div class="seccion-pasarex">
    <div class="titulo-seccion-pasarex">SHIPPER / REMITENTE</div>
    <div class="datos-pasarex">
      <p><strong>Company:</strong> {{ remitente.empresa }}</p>
      <p><strong>Contact:</strong> {{ remitente.nombre }}</p>
      <p><strong>Address:</strong> {{ remitente.direccion }}</p>
      <p><strong>Postal Code:</strong> {{ remitente.codigo_postal }}</p>
      <p><strong>Phone:</strong> {{ remitente.telefono }}</p>
      <p><strong>Origin:</strong> {{ remitente.origen }}</p>
    </div>
  </div>

  <!-- Destinatario -->
  <div class="seccion-pasarex">
    <div class="titulo-seccion-pasarex">CONSIGNEE / DESTINATARIO</div>
    <div class="datos-pasarex">
      <p><strong>Company:</strong> {{ destinatario.empresa }}</p>
      <p><strong>Contact:</strong> {{ destinatario.nombre }}</p>
      <p><strong>Address:</strong> {{ destinatario.direccion }}</p>
      <p><strong>Postal Code:</strong> {{ destinatario.codigo_postal }}</p>
      <p><strong>Phone:</strong> {{ destinatario.telefono }}</p>
      <p><strong>Destination:</strong> {{ destinatario.ciudad }}</p>
    </div>
  </div>

  <!-- Código de barras -->
  <div class="codigo-barras-pasarex">
    <div class="barcode-label-pasarex">{{ pais }}</div>
    <div class="barcode-pasarex">
      {{ barcode_svg | safe }}
    </div>
  </div>

  <!-- Footer -->
  <div class="footer-pasarex">
    <a href="https://pasarex.com" target="_blank">https://pasarex.com</a>
  </div>

</div>
"""
