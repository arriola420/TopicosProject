# Arquitectura - Entregable 2

## Vista de contenedores y despliegue

```mermaid
flowchart LR
    U[Usuario web / equipo aliado] -->|HTTP :80| EC2
    subgraph AWS Academy - EC2
        N[Nginx API Gateway]
        D[Django + Gunicorn\nMonolito / API v1 / UI]
        F[Flask + Gunicorn\nPagos v2]
        W[Celery Worker]
        R[(Redis Broker)]
        DB[(PostgreSQL)]
        N -->|/ y /api/v1/*| D
        N -->|/api/v2/pagos/*| F
        D --> DB
        D -->|publica tareas| R
        R --> W
        W --> DB
    end
    D -->|Adapter HTTP| A[API equipo aliado]
    D -->|CatalogoExternoAdapter| T[API de terceros]
```

## Decisiones

- Nginx es el único puerto público y conserva URLs estables.
- Django mantiene la UI, autenticación, catálogo y órdenes.
- Flask aísla el procesamiento v2 de pagos mediante Strangler Pattern.
- Redis desacopla la petición HTTP de las notificaciones ejecutadas por Celery.
- Las integraciones dependen de adaptadores propios y de variables de entorno.
- gettext y `LocaleMiddleware` permiten alternar español e inglés.

## Contratos principales

| Método | Ruta | Responsable |
|---|---|---|
| GET | `/api/v1/integracion/catalogo/` | Servicio JSON provisto por Django |
| GET | `/api/v1/integracion/aliado/` | Consumo del equipo aliado |
| GET | `/api/v1/integracion/recomendaciones/` | API externa mediante Adapter |
| POST | `/api/v1/ordenes/` | Creación de orden Django |
| POST | `/api/v2/pagos/procesar` | Microservicio Flask |

La URL real del aliado se configura en `ALLY_SERVICE_URL`; no queda quemada en el código.
