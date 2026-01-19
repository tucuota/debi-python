from flask import Flask, jsonify, request, redirect
import debi
from os import getenv
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
debi = debi.debi(getenv('DEBI_API_KEY'))
if os.getenv("WERKZEUG_RUN_MAIN") != "true":
	# Avoid duplicate prompt with the reloader process.
	try:
		DEFAULT_CUSTOMER_ID = input("DEBI_CUSTOMER_ID (customer_id para pruebas): ").strip()
	except EOFError:
		DEFAULT_CUSTOMER_ID = ""
else:
	DEFAULT_CUSTOMER_ID = ""
intro = """

En este ejemplo mostramos cómo agregar pagos y suscripciones a través del checkout de debi.
Más información en nuestra documentación:
https://debi.pro/docs

Hará falta sacar un token de acceso en https://debi-test.pro/dashboard/developers y ponerlo como variable de entorno:
export DEBI_API_KEY=........

Para activar las notificaciones por webhook, en la misma url agregar una dirección webhook y la variable de entorno del código secreto
export DEBI_API_WEBHOOK_SECRET=....

Tarjeta para hacer pruebas en sandbox:
mastercard
5447651834106668

Rutas
/debi/payment
/debi/subscription

Donde se redirigen los checkouts exitosos
/debi/callback

Webhooks para recibir notificaciones
/debi/webhooks (POST)
"""

def _require_api_key():
	if not debi.token:
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
	debi.sandbox = True


	customer_id = request.args.get("customer_id") or DEFAULT_CUSTOMER_ID
	if not customer_id:
		return jsonify({"error": "customer_id requerido. Reinicia la app y cargalo por consola o pásalo por query."}), 400
	description = request.args.get("description") or "test123"
	amount = request.args.get("amount") or "123"
	try:
		amount = int(amount)
	except ValueError:
		return jsonify({"error": "amount must be an integer"}), 400

	# Pago directo (API /v1/payments)
	try:
		response = debi.post('/v1/payments', {
			'customer_id': customer_id,
			'amount': amount, # Monto del pago
			'description': description,
		})
	except debi.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400

	return jsonify(response)


@app.route('/debi/subscription')
def subscription():
	missing_key = _require_api_key()
	if missing_key:
		return missing_key
	debi.sandbox = True

	customer_id = request.args.get("customer_id") or DEFAULT_CUSTOMER_ID
	if not customer_id:
		return jsonify({"error": "customer_id requerido. Reinicia la app y cargalo por consola o pásalo por query."}), 400
	description = request.args.get("description") or "Curso"
	amount = request.args.get("amount") or "125"
	count = request.args.get("count") or "12"
	interval_unit = request.args.get("interval_unit") or "monthly"
	day_of_month = request.args.get("day_of_month") or "1"
	try:
		amount = int(amount)
		count = int(count)
		day_of_month = int(day_of_month)
	except ValueError:
		return jsonify({"error": "amount, count y day_of_month deben ser enteros"}), 400

	# Suscripción directa (API /v1/subscriptions)
	try:
		response = debi.post('/v1/subscriptions', {
			'customer_id': customer_id,
			'amount': amount, # Monto del pago
			'count': count, # cantidad de repeticiones
			'interval_unit': interval_unit,
			'description': description,
			'day_of_month': day_of_month,
		})
	except debi.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400

	return jsonify(response)


@app.route('/debi/callback')
def callback():
	missing_key = _require_api_key()
	if missing_key:
		return missing_key
	course_id  = request.args.get('course_id')
	session_id = request.args.get('session_id')

	# Created resource
	try:
		session = debi.get('/v1/sessions/%s' % session_id)
	except debi.debiRequestFailed as exc:
		return jsonify({"error": str(exc)}), 400
	createdResource = session.get('data', {}).get('resource')

	return jsonify(createdResource)


@app.route("/debi/webhooks", methods=["POST"])
def webhooks():

	payload = request.data.decode("utf-8")
	timestamp = request.headers.get("debi-Timestamp", None)
	received_sig = request.headers.get("debi-Signature", None)
	secret = getenv('DEBI_API_WEBHOOK_SECRET')
	if not secret:
		return jsonify({
			"error": "Missing DEBI_API_WEBHOOK_SECRET environment variable.",
			"hint": "export DEBI_API_WEBHOOK_SECRET=...."
		}), 400

	try:
		event = debi.Webhook.construct_event(
			payload, timestamp, received_sig, secret
		)
	except ValueError:
		print("Error while decoding event!")
		return "Bad payload", 400
	except debi.debiSignatureVerificationError:
		print("Invalid signature!")
		return "Bad signature", 400

	print(event)

	return "", 200


if __name__ == "__main__":
	app.run(host="127.0.0.1", port=5000, debug=True, use_reloader=False)
