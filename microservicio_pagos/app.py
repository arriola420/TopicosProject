from uuid import uuid4

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException


app = Flask(__name__)
METODOS_PERMITIDOS = {'TARJETA', 'PSE', 'NEQUI', 'EFECTIVO'}


@app.post('/api/v2/pagos/procesar')
def procesar_pago():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        return jsonify({'error': 'El cuerpo debe ser un objeto JSON.'}), 400

    orden_id = datos.get('orden_id')
    monto = datos.get('monto')
    metodo = str(datos.get('metodo', '')).upper()

    errores = {}
    if not isinstance(orden_id, int) or isinstance(orden_id, bool) or orden_id < 1:
        errores['orden_id'] = 'Debe ser un entero mayor que cero.'
    if not isinstance(monto, (int, float)) or isinstance(monto, bool) or monto <= 0:
        errores['monto'] = 'Debe ser un número mayor que cero.'
    if metodo not in METODOS_PERMITIDOS:
        errores['metodo'] = 'Debe ser TARJETA, PSE, NEQUI o EFECTIVO.'
    if errores:
        return jsonify({'error': 'Datos de pago inválidos.', 'campos': errores}), 400

    return jsonify({
        'servicio': 'Microservicio Flask de Pagos (v2)',
        'orden_id': orden_id,
        'monto': round(float(monto), 2),
        'metodo': metodo,
        'estado': 'PROCESADO',
        'referencia': f'PAY-{uuid4().hex[:12].upper()}',
    }), 200


@app.errorhandler(Exception)
def manejar_error(error):
    if isinstance(error, HTTPException):
        return jsonify({'error': error.description}), error.code
    app.logger.exception('Error no controlado al procesar el pago')
    return jsonify({'error': 'Error interno del servicio de pagos.'}), 500
