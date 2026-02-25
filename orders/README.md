# Orders App

Gestión del ciclo de vida de los pedidos, desde el carrito hasta la entrega.

## Modelos Principales
- **Order**: Encabezado del pedido con estados y datos de facturación.
- **OrderItem**: Líneas de detalle del pedido.
- **OrderDocument**: Documentos asociados (facturas, albaranes).

## Ciclo de Vida del Pedido
1. **Nuevo**: Creado por el cliente.
2. **Confirmado**: Validado por un manager.
3. **Preparando**: Se reserva el stock.
4. **En reparto**: Enviado al cliente.
5. **Entregado**: Recepción confirmada.

## Vistas Clave
- `cart_detail`: Gestión del carrito de compras.
- `order_create`: Proceso de checkout (requiere perfil operativo completo).
- `order_list`: Historial de pedidos para el cliente y panel de gestión para admins.
