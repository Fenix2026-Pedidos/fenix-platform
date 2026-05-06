/**
 * FENIX CRM SYNC (v1.0)
 * Este script debe desplegarse como Web App en Google Apps Script
 * con acceso "Anyone" (Cualquiera).
 */

function doPost(e) {
  try {
    var sheet = SpreadsheetApp.getActiveSpreadsheet().getActiveSheet();
    var data = JSON.parse(e.postData.contents);
    
    // Mapeo unificado de columnas para Fenix
    sheet.appendRow([
      new Date(),          // Columna A: Fecha
      data.source || "Fenix Web", // Columna B: Origen
      data.name,           // Columna C: Nombre
      data.email,          // Columna D: Email
      data.phone_prefix,   // Columna E: Prefijo
      data.phone_number,   // Columna F: Teléfono
      data.company || "-", // Columna G: Empresa
      data.message || "-"  // Columna H: Mensaje / Consulta
    ]);
    
    return ContentService.createTextOutput(JSON.stringify({
      success: true,
      message: "Lead sincronizado correctamente en Fenix CRM"
    })).setMimeType(ContentService.MimeType.JSON);
    
  } catch (error) {
    return ContentService.createTextOutput(JSON.stringify({
      success: false,
      message: error.toString()
    })).setMimeType(ContentService.MimeType.JSON);
  }
}
