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

## Strangler Pattern

El procesamiento de pagos dispone de dos versiones coexistentes:

- Django v1: `POST /api/v1/ordenes/<id>/pagar/`.
- Flask v2: `POST /api/v2/pagos/procesar`.

Nginx actúa como punto único de entrada y selecciona el backend según la URL.
El borrador listo para publicar en la Wiki se encuentra en
`docs/wiki/Migracion-a-Microservicios-Strangler-Pattern.md`.

## Notificaciones

- `NOTIFICADOR_TYPE=MOCK`: salida por consola, valor predeterminado.
- `NOTIFICADOR_TYPE=REAL`: utiliza el backend de correo de Django.

## Pruebas

```shell
python manage.py test
```

La arquitectura completa se inicia con:

```shell
docker compose up -d --build
```
