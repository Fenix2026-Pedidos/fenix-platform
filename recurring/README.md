# Recurring App

Este módulo gestiona la creación y programación de pedidos recurrentes (suscripciones de productos).

## Modelos Principales
- **RecurringOrder**: Define la frecuencia (semanal, quincenal, mensual) y los productos que se generarán automáticamente.
- **RecurringOrderLog**: Historial de generaciones automáticas.

## Funcionamiento
El sistema procesa periódicamente las suscripciones activas y crea pedidos estándar en la aplicación `orders` basados en la configuración de recurrencia.
