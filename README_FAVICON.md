# Favicon for Fenix

favicon.png generado a partir del logo. Para usarlo como favicon en Django, sigue estos pasos:

1. Mueve favicon.png a la carpeta static/ de tu proyecto (por ejemplo: static/favicon.png).
2. En tu template base (por ejemplo, base.html), dentro del <head>, agrega:

<link rel="icon" type="image/png" href="{% static 'favicon.png' %}">

3. Asegúrate de tener configurado correctamente STATIC_URL y de haber ejecutado collectstatic si usas producción.

¡Listo! El favicon aparecerá en los navegadores.
