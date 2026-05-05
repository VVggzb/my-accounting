from flask import jsonify

def success_response(data=None, message='success', code=200):
    """成功响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data or {}
    }), code

def error_response(message='error', code=400, data=None):
    """错误响应"""
    return jsonify({
        'code': code,
        'message': message,
        'data': data or {}
    }), code