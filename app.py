import uuid

from flask import Flask, request, jsonify
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError

app = Flask(__name__)

# 连接到 MySQL 数据库
mysql_user = 'root'
mysql_password = 'hc19941015'
mysql_host = '8.138.1.127'
mysql_db = 'hiddify_data'

connection_string = f"mysql+mysqlconnector://{mysql_user}:{mysql_password}@{mysql_host}/{mysql_db}"
engine = create_engine(connection_string, echo=True)


@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    package_type = data.get('package_type', 'free')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    user_id = str(uuid.uuid4())

    try:
        with engine.connect() as connection:
            from sqlalchemy import text
            stmt = text(
                "INSERT INTO users (user_id, username, password, package_type) VALUES (:user_id, :username, :password, :package_type)")
            connection.execute(stmt, {
                "user_id": user_id,
                "username": username,
                "password": password,
                "package_type": package_type
            })
            connection.commit()
        return jsonify({"message": "User registered successfully"}), 200
    except SQLAlchemyError as e:
        return jsonify({"error": "Database error occurred"}), 500


@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    try:
        with engine.connect() as connection:
            stmt = text("SELECT user_id, password FROM users WHERE username = :username")
            result = connection.execute(stmt, {"username": username})
            user = result.fetchone()

        if user and user.password == password:
            # 这里可以添加生成和返回 JWT token 的逻辑
            return jsonify({
                "message": "Login successful",
                "user_id": user.user_id
            })
        else:
            return jsonify({"error": "Invalid username or password"}), 401

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500


@app.route('/change_password', methods=['POST'])
def change_password():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    new_password = data.get('new_password')

    if not username or not password or not new_password:
        return jsonify({"error": "Username, current password, and new password are required"}), 400

    try:
        with engine.connect() as connection:
            # 获取用户信息
            select_stmt = text("SELECT user_id, password FROM users WHERE username = :username")
            result = connection.execute(select_stmt, {"username": username})
            user = result.fetchone()

            if not user or user.password != password:
                return jsonify({"error": "Invalid username or password"}), 401

            # 更新密码
            update_stmt = text("UPDATE users SET password = :new_password WHERE user_id = :user_id")
            connection.execute(update_stmt, {"new_password": new_password, "user_id": user.user_id})
            connection.commit()

            return jsonify({"message": "Password changed successfully"}), 200

    except SQLAlchemyError as e:
        return jsonify({"error": f"Database error occurred: {str(e)}"}), 500


# 获取所有订阅套餐
@app.route('/user_orders', methods=['POST'])
def get_subscriptions():
    data = request.get_json()
    username = data.get('username')
    try:
        with engine.connect() as connection:
            stmt = text("SELECT order_list FROM users where username = :username")
            result = connection.execute(stmt, {"username": username}).fetchone()
            if result:
                order_list = result[0].split(',')
                response_data = {
                    "username": username,
                    "orders": order_list
                }
                return jsonify(response_data), 200
            else:
                return jsonify({"error": "User not found"}), 404

    except Exception as e:
        return jsonify({"error": "An error occurred while fetching subscriptions"}), 500


# 创建新订阅套餐
@app.route('/create_order', methods=['POST'])
def create_order():
    data = request.get_json()
    username = data.get('username')
    package_type = data.get('package_type')

    if not username or not package_type:
        return jsonify({"error": "Username and package type are required"}), 400

    try:
        with engine.connect() as connection:
            # 查询现有的 order_list 值
            stmt_select = text("SELECT order_list FROM users WHERE username = :username")
            result = connection.execute(stmt_select, {"username": username}).fetchone()

            if not result:
                return jsonify({"error": "User not found. Please register first."}), 404

            existing_order_list = result[0] if result else ""

            # 更新 order_list 字段，将新的 package_type 值追加到现有值后面
            updated_order_list = f"{existing_order_list}, {package_type}" if existing_order_list else package_type
            stmt_update = text("UPDATE users SET order_list = :updated_order_list WHERE username = :username")
            connection.execute(stmt_update, {"updated_order_list": updated_order_list, "username": username})
            connection.commit()

        return jsonify({"message": "Order created successfully"}), 201
    except Exception as e:
        return jsonify({"error": "An error occurred while creating order"}), 500

@app.route('/pay', methods=['POST'])
def pay():
    data = request.get_json()
    username = data.get('username')
    # 在这里可以根据订单号查询订单信息，生成支付页面
    response_data = {
        "username": username,
    }
    return jsonify(response_data), 200


if __name__ == '__main__':
    app.run(host='localhost', port=8081)
