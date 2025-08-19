_HTML_TEMPLATE_DHL = """
  <style>
    :root {
      --font-base-dhl: {{ font }}px;
    }

    .container-dhl {
      width: {{ width }}px;
      height: {{ height }}px;
      padding: 8px;
      border: 1px solid black;
      box-sizing: border-box;
      font-size: var(--font-base-dhl);
    }

    .section-table-dhl {
      width: 100%;
      border-collapse: collapse;
    }

    .bold-dhl {
      font-weight: bold;
    }

    .small-dhl {
      font-size: calc(var(--font-base-dhl) * 0.9);
    }

    .medium-dhl {
      font-size: calc(var(--font-base-dhl) * 1.2);
    }

    .large-dhl {
      font-size: calc(var(--font-base-dhl) * 1.5);
    }

    .logo-dhl img {
      height: 18px;
    }

    .barcode-dhl img {
      width: auto;
      height: 29px;
    }

    .black-box-dhl {
      background-color: black;
      color: white;
      padding: 4px;
      font-weight: bold;
      font-size: calc(var(--font-base-dhl) * 1.2);
    }

    .right-dhl {
      text-align: right;
    }

    .center-dhl {
      text-align: center;
    }

    .border-top-dhl {
      border-top: 1px solid black;
    }

    .border-bottom-dhl {
      border-bottom: 1px solid black;
    }

    .padding-dhl {
      padding: 5px;
    }
  </style>
<div class="container-dhl">
  <!-- Header -->
  <table class="section-table-dhl border-bottom-dhl">
    <tr>
      <td class="padding-dhl">
        <span class="bold-dhl medium-dhl">EXPRESS WORLDWIDE</span><br>
        <span class="small-dhl">{{ fecha_recepcion }} MYDHL+ 1.0 / *30.0821*</span>
      </td>
      <td class="padding-dhl right-dhl logo-dhl">
        <img src="https://cdn.worldvectorlogo.com/logos/dhl-logo-1.svg" alt="DHL">
      </td>
    </tr>
  </table>

  <!-- Remitente -->
  <table class="section-table-dhl border-bottom-dhl">
    <tr>
      <td class="padding-dhl small-dhl">
        <span class="bold-dhl">From:</span><br>
        {{ remitente.nombre }}<br>
        {{ remitente.direccion }}<br>
        {{ remitente.codigo_postal }}<br>
        {{ remitente.ciudad }}<br><br>
        {{ remitente.codigo_postal }} {{ remitente.ciudad }}<br>
        {{ remitente.pais }}
      </td>
    </tr>
  </table>

  <!-- Destinatario -->
  <table class="section-table-dhl border-bottom-dhl">
    <tr>
      <td class="padding-dhl small-dhl">
        <span class="bold-dhl">To:</span><br>
        {{ destinatario.nombre }}<br>
        {{ destinatario.nombre }}<br>
        {{ destinatario.direccion }}<br><br>
        <span class="bold-dhl medium-dhl">{{ destinatario.codigo_postal }} {{ destinatario.ciudad }}</span><br>
        {{ destinatario.pais }}
      </td>
    </tr>
  </table>

  <!-- Código país y contacto -->
  <table class="section-table-dhl border-bottom-dhl">
    <tr>
      <td class="padding-dhl" style="width: 70%;">
        <span class="bold-dhl medium-dhl">B</span><br>
        <span class="large-dhl">{{ destino }}</span>
      </td>
      <td class="padding-dhl small-dhl" style="vertical-align: top;">
        <span class="bold-dhl">Contact:</span><br>
        {{ destinatario.nombre }}
      </td>
    </tr>
  </table>

  <!-- Caja negra -->
  <table class="section-table-dhl border-top-dhl border-bottom-dhl">
    <tr>
      <td class="black-box-dhl">
        {{ zona }} C-RES-SIR
      </td>
      <td class="right-dhl padding-dhl small-dhl">
        Day ________ Time ________
      </td>
    </tr>
  </table>

  <!-- Referencia -->
  <table class="section-table-dhl">
    <tr>
      <td class="padding-dhl small-dhl"><span class="bold-dhl">Ref:</span></td>
    </tr>
  </table>

  <!-- Peso y pieza -->
  <table class="section-table-dhl">
    <tr>
      <td class="padding-dhl small-dhl">
        <span class="bold-dhl">Pce/Shpt Weight</span><br>
        <span class="medium-dhl">{{ peso_fisico }}</span>
      </td>
      <td class="padding-dhl small-dhl">
        <span class="bold-dhl">Piece</span><br>
        <span class="medium-dhl">{{ pieza }} / {{ total_piezas }}</span>
      </td>
    </tr>
  </table>

  <!-- Contenido -->
  <table class="section-table-dhl">
    <tr>
      <td class="padding-dhl small-dhl">
        <span class="bold-dhl">Contents:</span> {{ descripcion_contenido }}
      </td>
    </tr>
  </table>

  <!-- Código de barras -->
  <table class="section-table-dhl">
    <tr>
      <td class="center-dhl padding-dhl">
        <div class="barcode-dhl">
          {{ barcode_svg | safe }}
        </div>
        <div class="bold-dhl medium-dhl">WAYBILL {{ no_guide }}</div>
      </td>
    </tr>
  </table>

</div>
"""
