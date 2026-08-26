# TopicosProject

Marketplace desarrollado con Django. El flujo crítico de creación de órdenes usa
Service Layer, Builder, Factory e inyección de dependencias.

## Flujo de órdenes

El endpoint `POST /api/ordenes/` recibe un JSON con `items` (`variante` y
`cantidad`) y un `cupon_codigo` opcional. También conserva compatibilidad con
el formato form-data anterior.

La API incluye consulta de órdenes, detalle, pago y cancelación, con respuestas
`201`, `400`, `404` y `409` según el caso.

La explicación arquitectónica, los diagramas y la evidencia de pruebas están
publicados en la Wiki de GitHub del repositorio.

## Notificaciones

- `NOTIFICADOR_TYPE=MOCK`: salida por consola, valor predeterminado.
- `NOTIFICADOR_TYPE=REAL`: utiliza el backend de correo de Django.

## Pruebas

```shell
python manage.py test
```
