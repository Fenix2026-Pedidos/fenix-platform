import os
import django
import traceback

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fenix.settings')
django.setup()

from django.template.loader import get_template
from django.template import TemplateSyntaxError

try:
    get_template('catalog/product_list.html')
    print('SUCCESS COMPILING catalog/product_list.html')
except TemplateSyntaxError as e:
    print('Failed parsing template catalog/product_list.html')
    print('Origin name:', getattr(getattr(e, 'template', None), 'origin', getattr(e, 'template', None)))
    print('Traceback:')
    traceback.print_exc()
