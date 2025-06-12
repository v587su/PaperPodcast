from flask import request, jsonify
import functools

def jwt_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # 预留JWT校验逻辑
        auth_header = request.headers.get('Authorization', None)
        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header.split(' ')[1]
        # TODO: 在此处添加JWT解码与校验逻辑
        # if not valid_token(token):
        #     return jsonify({"error": "Invalid token"}), 401
        return func(*args, **kwargs)
    return wrapper