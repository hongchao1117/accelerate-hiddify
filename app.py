import uuid
from functools import wraps

from flask import Flask, request, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)
app.config['SECRET_KEY'] = 'a3f4b6d1e58f9a8e5e9a5b7c1a9d8e2f5b6e9a4c7f8b1c2e3d5a7b9c4e6f1a0e'  # 请更改为一个强密钥

# 数据库连接设置
mysql_user = 'root'
mysql_password = 'hc19941015'
mysql_host = '8.138.1.127'
mysql_db = 'hiddify_data'

connection_string = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
engine = create_engine(connection_string, echo=True)

# Flask-Login 设置
login_manager = LoginManager()
login_manager.init_app(app)


class User(UserMixin):
    def __init__(self, user_id, username):
        self.id = user_id
        self.username = username


@login_manager.user_loader
def load_user(user_id):
    with engine.connect() as connection:
        stmt = text("SELECT user_id, username FROM users WHERE user_id = :user_id")
        result = connection.execute(stmt, {"user_id": user_id}).fetchone()
        if result:
            return User(result.user_id, result.username)
    return None


def handle_error(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except SQLAlchemyError as e:
            app.logger.error(f"Database error in {func.__name__}: {str(e)}")
            return jsonify({"error": "A database error occurred"}), 500
        except Exception as e:
            app.logger.error(f"Unexpected error in {func.__name__}: {str(e)}")
            return jsonify({"error": "An unexpected error occurred"}), 500

    return wrapper


@app.route('/get_node_list', methods=['GET', 'POST'])
def get_node_list():
    node_list = [
        {
            "title": "US",
            "config": {
                "server": "198.2.240.89",
                "port": 49303,
                "password": "Bj6N25kZQS1sei",
                "method": "ssh"
            }
        },
        {
            "title": "Japan",
            "config": {
                "server": "104.219.209.105",
                "port": 41903,
                "password": "3q1g8vKssMpg",
                "method": "ssh"
            }
        }
    ]

    return jsonify({"nodeList": node_list})


@app.route('/get_user_info', methods=['POST', 'GET'])
def get_user_info():
    data = request.get_json()
    user_id = data.get('userId')
    if not user_id:
        return jsonify({"error": "userId  is required"}), 400

    with engine.connect() as connection:
        # 检查用户名是否已存在
        check_stmt = text("SELECT username,package_type FROM users WHERE user_id = :user_id")
        existing_user = connection.execute(check_stmt, {"user_id": user_id}).fetchone()
        if not existing_user:
            return jsonify({"error": "Username isn't exists"}), 409
        username = existing_user.username
        packageType = existing_user.package_type

    return jsonify({
        "username": username,
        "email": "",
        "phone": "",
        "remainTryTime": "0",
        "packageType": packageType,
        "packageExpiresTime": "",
        "deviceCount": 1
    })


@app.route('/get_package_list', methods=['POST', 'GET'])
def get_package_list():
    package_list = [{
        "type": "month",
        "title": "1 Month",
        "fakePrice": "$9.99",
        "price": "$7.99",
        "priceTip": "Save $2.00"
    },
        {
            "type": "quarter",
            "title": "1 Quarter",
            "fakePrice": "$29.99",
            "price": "$23.99",
            "priceTip": "Save $6.00"
        },
        {
            "type": "year",
            "title": "1 Year",
            "fakePrice": "$119.96",
            "price": "$89.96",
            "priceTip": "Save $30.00"
        }
    ]

    return jsonify({
        "typeInit": "month",
        "list": package_list
    })


@app.route('/register', methods=['POST', 'GET'])
@handle_error
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    package_type = data.get('package_type', 'free')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with engine.connect() as connection:
        # 检查用户名是否已存在
        check_stmt = text("SELECT user_id FROM users WHERE username = :username")
        existing_user = connection.execute(check_stmt, {"username": username}).fetchone()
        if existing_user:
            return jsonify({"error": "Username already exists"}), 409

        user_id = str(uuid.uuid4())
        hashed_password = password

        stmt = text(
            "INSERT INTO users (user_id, username, password, package_type) VALUES (:user_id, :username, :password, :package_type)")
        connection.execute(stmt, {
            "user_id": user_id,
            "username": username,
            "password": hashed_password,
            "package_type": package_type
        })
        connection.commit()

    return jsonify({"message": "User registered successfully", "user_id": user_id}), 201


@app.route('/login', methods=['POST', 'GET'])
@handle_error
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    with engine.connect() as connection:
        stmt = text("SELECT user_id, password FROM users WHERE username = :username")
        result = connection.execute(stmt, {"username": username}).fetchone()

    if result and (result.password, password):
        user = User(result.user_id, username)
        login_user(user)
        return jsonify({"message": "Login successful", "user_id": result.user_id}), 200
    else:
        return jsonify({"error": "Invalid username or password"}), 401


@app.route('/logout', methods=['POST', 'GET'])
@login_required
@handle_error
def logout():
    # 检查请求中是否包含用户ID
    user_id = request.json.get('user_id')
    if user_id and user_id == str(current_user.id):  # 确保用户ID匹配
        logout_user()
        response_data = {
            "message": "Logged out successfully",
            "user_id": user_id
        }
        return jsonify(response_data), 200
    else:
        return jsonify({"message": "Unauthorized to log out this user."}), 403


@app.route('/change_password', methods=['POST', 'GET'])
@login_required
@handle_error
def change_password():
    data = request.get_json()
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({"error": "Current password and new password are required"}), 400

    with engine.connect() as connection:
        stmt = text("SELECT password FROM users WHERE user_id = :user_id")
        result = connection.execute(stmt, {"user_id": current_user.id}).fetchone()

        if not result or not (result.password, current_password):
            return jsonify({"error": "Current password is incorrect"}), 401

        hashed_new_password = (new_password)
        update_stmt = text("UPDATE users SET password = :new_password WHERE user_id = :user_id")
        connection.execute(update_stmt, {"new_password": hashed_new_password, "user_id": current_user.id})
        connection.commit()

    return jsonify({"message": "Password changed successfully"}), 200


@app.route('/user_orders', methods=['POST', 'GET'])
@login_required
@handle_error
def get_subscriptions():
    with engine.connect() as connection:
        stmt = text("SELECT order_list FROM users WHERE user_id = :user_id")
        result = connection.execute(stmt, {"user_id": current_user.id}).fetchone()

    if result:
        order_list = result.order_list.split(',') if result.order_list else []
        response_data = {
            "username": current_user.username,
            "orders": order_list
        }
        return jsonify(response_data), 200
    else:
        return jsonify({"error": "User not found"}), 404


@app.route('/create_order', methods=['POST', 'GET'])
@login_required
@handle_error
def create_order():
    data = request.get_json()
    package_type = data.get('package_type')

    if not package_type:
        return jsonify({"error": "Package type is required"}), 400

    with engine.connect() as connection:
        stmt_select = text("SELECT order_list FROM users WHERE user_id = :user_id")
        result = connection.execute(stmt_select, {"user_id": current_user.id}).fetchone()

        existing_order_list = result.order_list if result and result.order_list else ""
        updated_order_list = f"{existing_order_list},{package_type}" if existing_order_list else package_type

        stmt_update = text("UPDATE users SET order_list = :updated_order_list WHERE user_id = :user_id")
        connection.execute(stmt_update, {"updated_order_list": updated_order_list, "user_id": current_user.id})
        connection.commit()

    return jsonify({"message": "Order created successfully"}), 200


@app.route('/pay', methods=['POST', 'GET'])
@login_required
@handle_error
def pay():
    # 这里应该实现实际的支付逻辑
    return jsonify({"message": "Payment process initiated", "username": current_user.username}), 200


if __name__ == '__main__':
    app.run(host='localhost', port=8081)
