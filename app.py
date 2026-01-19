from flask import Flask, jsonify, request, redirect
import debi as debi_module
from os import getenv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
client = debi_module.debi(getenv('DEBI_API_KEY'))
intro = """

En este ejemplo mostramos cómo agregar pagos y suscripciones a través del checkout de debi.
Más información en nuestra documentación:
https://debi.pro/docs

Hará falta sacar un token de acceso en https://debi-test.pro/dashboard/developers y ponerlo como variable de entorno en archivo .env:

Tarjeta para hacer pruebas en sandbox:
4000056655665556

Rutas para sesión tipo pago o suscripción:
/debi/payment
/debi/subscription

Donde se redirigen los checkouts exitosos
/debi/callback

Webhooks para recibir notificaciones
/debi/webhooks (POST)

"""

def _require_api_key():
	if not client.token:
		return jsonify({
			"error": "Missing DEBI_API_KEY environment variable.",
			"hint": "export DEBI_API_KEY=...."
		}), 400
	return None


@app.route('/')
def hello():
	return "<pre>%s</pre>" % intro


@app.route('/debi/payment')
def payment():
	missing_key = _require_api_key()
	if missing_key:
		return missing_key




	# Pago directo (API /v1/sessions)
	try:
		response = client.post('/v1/sessions', {
			
        	'description' : "Pago único",
        	'success_url' : "http://127.0.0.1:5000/debi/callback", # esta uri no será visible hasta que se complete el flujo del checkout y el cliente no la verá nunca.
			'kind': 'payment',
			'description': 'Pago único',
			'amount': 12000,
        	'customer_name': "Juan Ramonda",
        	'customer_email': "juanchoramonda@gmail.pro",
			'metadata' : { # se pueden agregar acá cualquier tipo de metadatos. La suscripción o pagos que genere el checkout también tendrán la misma metadata
				'course_id': 5,
			},
		})
	except debi_module.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400

	uri = response.get('data', {}).get('public_uri')
	return redirect(uri)


@app.route('/debi/subscription')
@app.route('/debi/sessions')
def subscription():
	missing_key = _require_api_key()
	if missing_key:
		return missing_key



	# Suscripción directa (API /v1/sessions)
	try:
		response = client.post('/v1/sessions', {
			'description' : "Suscripción",
			'success_url' : "http://127.0.0.1:5000/debi/callback", # esta uri no será visible hasta que se complete el flujo del checkout y el cliente no la verá nunca.
			'kind': 'subscription',
			'description': 'Suscripción',
			'amount': 12000,
			'customer_name': "Juan Ramonda",
			'customer_email': "juanchoramonda@gmail.pro",
			'interval_unit': "monthly",
			'metadata' : { # se pueden agregar acá cualquier tipo de metadatos. La suscripción o pagos que genere el checkout también tendrán la misma metadata
				'course_id': 5,
			},
		})
	except debi_module.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400

	uri = response.get('data', {}).get('public_uri')
	return redirect(uri)


@app.route('/debi/callback')
def callback():
	missing_key = _require_api_key()
	if missing_key:
		return missing_key
	course_id  = request.args.get('course_id')
	session_id = request.args.get('session_id')

	# Created resource
	try:
		session = client.get('/v1/sessions/%s' % session_id)
	except debi_module.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400
	createdResource = session.get('data', {}).get('resource')

	return jsonify(createdResource)


if __name__ == "__main__":
	app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
