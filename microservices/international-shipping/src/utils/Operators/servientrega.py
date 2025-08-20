_HTML_TEMPLATE_SERVIENTREGA = """
  <style>
    :root {
      --font-base-servientrega: {{ font }}px;
    }

    .label-servientrega {
      width: {{ width }}px;
      border: 1px solid black;
      padding: 5px;
      box-sizing: border-box;
      position: relative;
      font-family: Arial, sans-serif;
      font-size: var(--font-base-servientrega);
      margin: 0;
    }

    .header-servientrega {
      display: flex;
      justify-content: space-between;
      align-items: flex-start;
    }

    .header-left-servientrega {
      width: 70%;
    }

    .barcode-img-servientrega {
      width: 200px;
      height: auto;
    }

    .title-servientrega {
      font-size: calc(var(--font-base-servientrega) * 1.4);
      font-weight: bold;
    }

    .bold-servientrega {
      font-weight: bold;
    }

    .section-servientrega {
      margin: 4px 0;
      padding: 4px;
    }

    .data-table-servientrega {
      width: 100%;
    }

    .data-table-border-servientrega {
      width: 100%;
      border-collapse: collapse;
    }

    .data-table-servientrega td {
      padding: 0px 0px;
      vertical-align: top;
      border: none;
      font-size: var(--font-base-servientrega);
    }

    .data-table-border-servientrega td {
      padding: 0px 0px;
      vertical-align: top;
      border: 1px solid black;
      font-size: var(--font-base-servientrega);
    }

    .info-box-servientrega {
      display: flex;
      border: 1px solid black;
      margin-top: 5px;
      font-size: var(--font-base-servientrega);
    }

    .info-box-servientrega .label-servientrega {
      width: 25px;
      height: auto;
      display: flex;
      align-items: center;
      justify-content: center;
      transform: rotate(270deg);
      white-space: nowrap;
      font-weight: bold;
      border: 0px solid rgb(255, 255, 255);
      padding: 3px 5px;
      margin-right: 5px;
      font-size: var(--font-base-servientrega);
    }

    .info-box-servientrega .label-container-servientrega {
      width: 25px;
      display: flex;
      justify-content: center;
      align-items: center;
      border-right: 1px solid black;
    }

    .info-box-servientrega .content-servientrega {
      padding: 4px;
      flex: 1;
    }

    .footer-servientrega {
      font-size: calc(var(--font-base-servientrega) * 0.6);
      text-align: center;
      margin-top: 4px;
      font-family: Arial, sans-serif;
    }

    .text-center-servientrega {
      text-align: center;
    }

    .hr-servientrega {
      border: none;
      margin: 5px 0;
    }
    </style>

<div class="label-servientrega">
  <!-- HEADER -->
  <div class="header-servientrega">
    <div class="header-left-servientrega">
      <div class="title-servientrega">Piezas: {{ pieza }}/{{ total_piezas }}</div>
      Fecha: {{ fecha_recepcion }}<br>
      Hora: {{ hora_recepcion }}<br>
      Fecha impresión: {{ fecha_recepcion }}
      <div class="bold-servientrega">{{ tipo_servicio }}</div>
      <div class="bold-servientrega">GUÍA No. <span style="font-size: calc(var(--font-base-servientrega) * 1.5);">{{ no_guide }}</span></div>
    </div>
    <div class="header-right-servientrega">
      {{ barcode_svg | safe }}
    </div>
  </div>

  <!-- PDC Info -->
  <div class="section-servientrega">
    <table class="data-table-border-servientrega">
      <tr>
        <td><strong>PDC</strong><br>{{ remitente.pdc or '269' }}</td>
        <td><strong>CIUDAD:</strong><br>{{ destino }}</td>
        <td><strong>DEPTO.:</strong><br>{{ remitente.departamento }}</td>
        <td><strong>{{ zona }}</strong></td>
        <td><strong>F.P.:</strong><br>{{ tipo_pago }}</td>
        <td><strong>SERVICIO:</strong><br>{{ tipo_servicio }}</td>
        <td><strong>M.T.:</strong><br>TERRESTRE</td>
      </tr>
    </table>
  </div>

  <!-- DESTINATARIO -->
  <div class="info-box-servientrega">
    <div class="label-container-servientrega"><div class="label-servientrega">DESTINATARIO</div></div>
    <div class="content-servientrega">
      <strong>{{ destinatario.nombre }}</strong><br>
      {{ destinatario.direccion }}<br>
      Tel: {{ destinatario.telefono }}<br>
      D/UNIT: {{ destinatario.dunit }}<br>
      Cod. Postal: {{ destinatario.codigo_postal }}<br>
      País: {{ destinatario.pais or 'COLOMBIA' }}<br>
      E-mail: {{ destinatario.email or 'Dato no suministrado por el cliente' }}
    </div>
  </div>

  <!-- DATOS ENVIO -->
  <div class="info-box-servientrega">
    <div class="label-container-servientrega"><div class="label-servientrega">DATOS ENVÍO</div></div>
    <div class="content-servientrega">
      Dice Contener: {{ descripcion_contenido }}<br><br>
      <table class="data-table-servientrega">
        <tr>
          <td><strong>V. Declarado:</strong><br>${{ '{:,.0f}'.format(destinatario.valor_declarado | default(50000)) }}</td>
          <td><strong>Vol:</strong><br>{{ destinatario.volumen or '26 / 23 / 19' }}</td>
          <td><strong>Peso (Vol):</strong><br>{{ peso_volumetrico }}</td>
          <td><strong>Peso (Kg):</strong><br>{{ peso_fisico }}</td>
        </tr>
        <tr>
          <td><strong>Vlr. Flete:</strong><br>${{ '{:,.2f}'.format(destinatario.flete | default(14600.00)) }}</td>
          <td>No Facturar</td>
          <td><strong>Vlr. Sobreporte:</strong><br>${{ '{:,.2f}'.format(destinatario.sobreporte | default(550.00)) }}</td>
          <td>No Sobreporte</td>
        </tr>
        <tr>
          <td colspan="4"><strong>V. Total:</strong> ${{ '{:,.2f}'.format(destinatario.total | default(15150.00)) }}</td>
        </tr>
      </table>
      <br>
      Ref1: {{ observaciones }}
    </div>
  </div>

  <!-- REMITENTE -->
  <div class="info-box-servientrega">
    <div class="label-container-servientrega"><div class="label-servientrega">REMITENTE</div></div>
    <div class="content-servientrega">
      <strong>NOMBRE:</strong> {{ remitente.empresa }}<br>
      Dirección: {{ remitente.direccion }}<br>
      Tel: {{ remitente.telefono }}<br>
      D/UNIT: {{ remitente.dunit }}<br>
      Cod. Postal: {{ remitente.codigo_postal }}<br>
      Ciudad: {{ remitente.ciudad }}<br>
      Departamento: {{ remitente.departamento }}<br>
      País: {{ remitente.pais or 'COLOMBIA' }}<br>
      E-mail: {{ remitente.email }}
    </div>
  </div>

  <hr class="servientrega">
  <div class="footer-servientrega">
    Servientrega S.A. NIT 860.512.330-3 Principal: Bogotá D.C., Colombia Av Calle 6 No. 34A - 11<br>
    Atención al usuario: www.servientrega.com. T: 770 0200 FAX: 770 0830 ext 110054.
  </div>
</div>
"""
