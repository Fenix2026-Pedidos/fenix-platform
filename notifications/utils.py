import io
import logging
from django.template.loader import get_template
from xhtml2pdf import pisa

logger = logging.getLogger(__name__)

def generate_order_pdf(context):
    """
    Convierte la plantilla HTML de pedido en un archivo PDF.
    Retorna el archivo como un objeto BytesIO o None si falla.
    """
    try:
        template = get_template('notifications/order_pdf.html')
        html = template.render(context)
        
        result = io.BytesIO()
        pisa_status = pisa.CreatePDF(io.BytesIO(html.encode("UTF-8")), dest=result)
        
        if pisa_status.err:
            logger.error("Error al generar PDF: %s", pisa_status.err)
            return None
            
        result.seek(0)
        return result
    except Exception as e:
        logger.exception("Excepción durante la generación del PDF: %s", str(e))
        return None
