# Implementación de debi en Python


En este ejemplo mostramos cómo agregar pagos y suscripciones a través del checkout de debi.
Más información en nuestra documentación:
https://debi.pro/docs

Hará falta sacar un token de acceso en https://debi-test.pro/dashboard/developers y ponerlo como variable de entorno `DEBI_API_KEY`
Para activar las notificaciones por webhook, en la misma url agregar una dirección webhook y la variable de entorno `DEBI_API_WEBHOOK_SECRET`

```bash
export debi_api_KEY=........
export debi_api_WEBHOOK_SECRET=....
```


Tarjeta para hacer pruebas en sandbox:
- mastercard
- 5447651834106668

Rutas
- /debi/payment
- /debi/subscription
- /debi/callback
- /debi/webhooks (POST)


## Requerimientos
- Python 3
- Flask

## Instalación
`pip install -r requirements.txt`