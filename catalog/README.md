# Catalog App

Gestión del catálogo de productos y categorías de la plataforma.

## Modelos Principales
- **Product**: Información del producto (nombres y descripciones en ES/ZH).
- **Category**: Organización jerárquica de productos.

## Características
- **Multi-idioma**: Soporte para campos localizados.
- **Traducción Automática**: Integración con `deep-translator` para agilizar la carga de productos.
- **Gestión de Stock**: Los managers pueden gestionar el inventario desde el admin.

## Vistas Clave
- `ProductListView`: Catálogo principal para clientes.
- `ProductDetailView`: Ficha técnica del producto.
