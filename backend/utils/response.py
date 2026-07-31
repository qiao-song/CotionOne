from flask import jsonify


def success(data=None, msg='ok'):
    return jsonify({'code': 0, 'data': data, 'msg': msg})


def fail(msg='error', code=1, data=None):
    return jsonify({'code': code, 'data': data, 'msg': msg}), 400 if code <= 1 else code
