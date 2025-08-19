_HTML_TEMPLATE_DEPRISA = """
<style>
  * {
    box-sizing: border-box;
  }

  body {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
  }

  .container {
    width: {{ width }}px;
    height: {{ height }}px;
    padding: 8px;
    border: 1px solid #000;
    overflow: hidden;
  }

  table {
    width: 100%;
    border-collapse: collapse;
  }

  td, th {
    border: 1px solid black;
    padding: 3px;
    font-size: 10px;
  }

  .no-border {
    border: none !important;
  }

  .center {
    text-align: center;
  }

  .right {
    text-align: right;
  }

  .bold {
    font-weight: bold;
  }

  .large {
    font-size: 24px;
    font-weight: bold;
  }

  .barcode {
    text-align: center;
    margin-top: 5px;
  }

  .barcode img {
    height: 70px;
  }

  .vertical {
    width: 0;
    padding: 0;
    text-align: center;
    vertical-align: middle;
  }

  .vertical div {
    transform: rotate(270deg);    
    white-space: nowrap;
    font-size: 8px;
    font-weight: bold;
    display: inline-block;
  }


  .logo {
    text-align: right;
    padding: 4px;
  }

  .logo img {
    width: 90px;
    
  }

  .small-text {
    font-size: 9px;
  }

  .medium-text {
    font-size: 11px;
  }

  .piezas {
    font-size: 13px;
    font-weight: bold;
  }

  .etiqueta-num {
    font-size: 20px;
    font-weight: bold;
    text-align: center;
  }

  .poblacion {
    font-weight: bold;
    font-size: 12px;
    text-align: center;
  }
</style>
<div class="container">
  <!-- DESTINO, PIEZ/PESO, PRODUCTO -->
  <table>
    <tr>
      <td class="vertical"><div>DESTINO</div></td>
      <td class="center large">{{ destino }}</td>
      <td class="center small-text">
        <div class="bold">PIEZ</div>
        <div class="piezas">{{ pieza }} / {{ total_piezas }}</div>
        <div class="bold">PESO</div>
        <div class="piezas">{{ peso_fisico }}</div>
      </td>
      <td class="vertical"><div>PRODUCTO</div></td>
      <td class="center large">{{ tipo_servicio }}</td>
    </tr>
  </table>

  <!-- Guía y fecha -->
  <table>
    <tr>
      <td colspan="4" class="bold">GUÍA: {{ no_guide }}</td>
      <td class="right">{{ fecha_recepcion }}</td>
    </tr>
  </table>

  <!-- Origen -->
  <table>
    <tr>
      <td colspan="2" class="small-text">DE: {{ remitente.ciudad }}</td>
      <td colspan="3" class="small-text">{{ remitente.nombre }}</td>
    </tr>
  </table>

  <!-- Código de barras -->
  <div class="barcode">
    {{ barcode_svg | safe }}
    <div class="small-text">{{ no_guide }}</div>
  </div>

  <!-- Datos de destinatario -->
  <table>
    <tr>
      <td style="width: 80px; text-align: center;">
        <div class="small-text">CÓDIGO POSTAL</div>
        <div class="bold" style="font-size: 16px;">{{ destinatario.codigo_postal }}</div>
      </td>
      <td rowspan="2" class="vertical"><div>PARA:</div></td>
      <td rowspan="2">
        <div class="bold medium-text">{{ destinatario.nombre }}</div>
        <div class="medium-text">{{ destinatario.direccion }}</div>
        <div class="small-text">CONTACTO: {{ destinatario.nombre }}</div>
        <div class="small-text">TELÉFONO: {{ destinatario.telefono }}</div>
      </td>
      <td rowspan="2" class="center small-text bold" style="width: 100px;">TOTAL A PAGAR</td>
    </tr>
    <tr>
      <td class="center small-text">ZONA DE REPARTO</td>
    </tr>
  </table>

  <!-- Observaciones y logo -->
  <table>
    <tr>
      <td class="etiqueta-num" rowspan="2" style="width: 80px;">{{ zona }}</td>
      <td colspan="2" class="small-text">OBS.: <strong>{{ observaciones }}</strong></td>
    </tr>
    <tr>
      <td style="padding: 4px;">
        <div class="small-text">ETIQUETA: {{ no_guide }}</div>
        <div class="small-text" style="margin-top: 4px;">
          POBLACIÓN:<br>
          <span class="poblacion">{{ destinatario.ciudad }}</span>
        </div>
      </td>
      <td class="logo">
        <img src="https://enviotodo.com.co/wp-content/uploads/2017/11/deprisa.png" alt="Deprisa Logo">
      </td>
    </tr>
  </table>
</div>
"""
