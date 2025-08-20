_HTML_TEMPLATE_FEDEX = """
  <style>
    :root {
      --font-base-fedex: {{ font }}px; 
    }

    .container-fedex {
      width: {{ width }}px;
      height: {{ height }}px;
      padding: 10px;
      border: 1px solid black;
      box-sizing: border-box;
      font-size: var(--font-base-fedex);
    }

    .bold-fedex {
      font-weight: bold;
    }

    .large-fedex {
      font-size: calc(var(--font-base-fedex) * 1.8);
    }

    .medium-fedex {
      font-size: calc(var(--font-base-fedex) * 1.2);
    }

    .small-fedex {
      font-size: calc(var(--font-base-fedex) * 0.9);
    }

    .small-xs-fedex {
      font-size:  6px;
    }

    .section-table-fedex {
      width: 100%;
      border-collapse: collapse;
      
    }

    .section-table-fedex td{
      font-size: var(--font-base-fedex);
    }

    .barcode-fedex img {
      width: 100%;
      height: auto;
    }

    .right-fedex {
      text-align: right;
      font-size: var(--font-base-fedex);
    }

    .center-fedex {
      text-align: center;
      font-size: var(--font-base-fedex);
    }

    .border-box-fedex {
      border: 1px solid black;
      padding: 4px;
      margin: 4px 0;
      font-size: var(--font-base-fedex);
    }

    .barcode-label-fedex {
      font-weight: bold;
      text-align: center;
      font-size: calc(var(--font-base-fedex) * 1.5);
    }

    hr {
      border: none;
      border-top: 1px solid black;
      margin: 4px 0;
    }

    .logo-fedex img {
      height: 30px;
    }
  </style>
<div class="container-fedex">

  <!-- Header -->
  <table class="section-table-fedex">
    <tr>
      <td>
        ORIGIN ID: VCCA 3202734562<br>
        {{ remitente.empresa }}<br>
        {{ remitente.direccion }}<br>
        {{ remitente.codigo_postal }}<br>
        {{ remitente.ciudad }}<br>
        {{ remitente.origen }}
      </td>
      <td class="right-fedex">
        SHIP DATE: {{ fecha_recepcion }}<br>
        ACTWGT: {{ peso_fisico }}<br>
        CAD: 258427326/NET4535<br>
        BILL {{ tipo_pago }}<br>
        ENVÍVAT:
      </td>
    </tr>
  </table>

  <!-- Address -->
  <table class="section-table-fedex" style="margin-top: 4px;">
    <tr>
      <td>
        <span class="bold-fedex">TO: {{ destinatario.nombre }}</span><br>
        {{ destinatario.direccion }}<br>
        {{ destinatario.codigo_postal }}<br>
        <span class="bold-fedex">{{ destino }}</span><br>
        {{ destinatario.ciudad }}
      </td>
      <td class="right-fedex logo-fedex" style="vertical-align: top;">
        <div class="bold-fedex">{{ destinatario.telefono }}</div>
        <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSDo7qkmw-2kXwZVPmbl95_vEI1cbTlpiUe0g&s" alt="FedEx Logo">
        <div>({{ destinatario.pais or 'US' }})</div>
        <div class="bold-fedex large-fedex">E</div>
      </td>
    </tr>
  </table>

  <!-- Barcode + Tracking -->
  <table class="section-table-fedex" style="margin-top: 4px;">
    <tr>
      <td style="width: 70%;" rowspan="2">
        <div class="barcode-fedex">
          {{ barcode_svg | safe }}
        </div>
      </td>
      <td class="right-fedex bold-fedex">{{ operador }}</td>
    </tr>
    <tr>
      <td class="right-fedex medium-fedex bold-fedex">PKG: {{ tipo_paquete or 'PAK' }}</td>
    </tr>
    <tr>
      <td colspan="2">
        <table class="section-table-fedex" style="margin-top: 2px;">
          <tr>
            <td class="bold-fedex">TRK#</td>
            <td>{{ no_guide }}</td>
            <td class="right-fedex">Form<br>0430</td>
          </tr>
        </table>
      </td>
    </tr>
  </table>

  <!-- Time -->
  <div style="margin-top: 4px; font-size: var(--font-base-fedex);">
    <div class="bold-fedex">{{ hora_recepcion }}</div>
    <div class="bold-fedex">{{ tipo_servicio }}</div>
  </div>

  <!-- Description -->
  <div class="border-box-fedex">
    <div class="bold-fedex">REF:</div>
    <div>DESC1: {{ descripcion_contenido }}</div>
    <div>DESC2:</div>
    <div>DESC3:</div>
    <div>DESC4:</div>
  </div>

  <!-- Bottom Info -->
  <table class="section-table-fedex small-fedex">
    <tr>
      <td style="width: 55%;">
        CTRY/TERR MFR: {{ remitente.origen }}<br>
        CARRIAGE VALUE: 90.00 USD<br>
        CUSTOMS VALUE: 90.00 USD
      </td>
      <td>
        SIGN: {{ remitente.empresa }}<br>
        T/C: S 201439381<br>
        D/T: R
      </td>
    </tr>
  </table>

  <hr>

  <!-- Footer -->
  <div class="small-xs-fedex">
    For all commodities, technology or software previously exported from the United States, the exporter certifies that it complies with the Export Administration Regulations. Diversion contrary to U.S. law is prohibited.
    The Material is licensed by the United States and may be reexported in most cases without further authorization as long as it is not destined for certain restricted countries or end users or for prohibited end uses.
    For further information, contact the U.S. Department of Commerce, Bureau of Industry and Security.
  </div>

</div>
"""
