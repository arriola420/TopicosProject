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
    D -->|ServicioAliadoAdapter| A[Servicio aliado de envíos\nOtra EC2 - repo aliado-envios]
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
| GET | `/api/v1/integracion/aliado/?ciudad=` | Consumo del servicio aliado (Adapter) |
| GET | `http://<IP_ALIADO>/api/v2/envios/tarifas?ciudad=` | Servicio aliado (repo y EC2 independientes) |
| GET | `/api/v1/integracion/recomendaciones/` | API externa mediante Adapter |
| POST | `/api/v1/ordenes/` | Creación de orden Django |
| POST | `/api/v2/pagos/procesar` | Microservicio Flask |

La URL del aliado se configura en `ALLY_SERVICE_URL` con la IP elástica de la EC2 del aliado; no hay nada del aliado dentro de este repositorio.
