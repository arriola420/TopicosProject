# TopicosProject

Marketplace desarrollado con Django. El flujo crítico de creación de órdenes usa
Service Layer, Builder, Factory e inyección de dependencias.

## Flujo de órdenes

El endpoint `POST /api/ordenes/` recibe listas `variante_id` y `cantidad`, además
de un `cupon_codigo` opcional.

La explicación arquitectónica y el diagrama están en
[`wiki/Implementacion-del-Patron-Creacional.md`](wiki/Implementacion-del-Patron-Creacional.md).

## Notificaciones

- `NOTIFICADOR_TYPE=MOCK`: salida por consola, valor predeterminado.
- `NOTIFICADOR_TYPE=REAL`: utiliza el backend de correo de Django.

## Pruebas

```shell
python manage.py test
```
