from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import json

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/dbname'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# 数据模型
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    register_time = db.Column(db.DateTime, default=datetime.utcnow)
    package_type = db.Column(db.String(50), default='free')
    package_expires = db.Column(db.DateTime)
    devices = db.relationship('Device', backref='user', lazy=True)

#
class Device(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    device_id = db.Column(db.String(100), unique=True, nullable=False)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)


class Node(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    config = db.Column(db.JSON, nullable=False)


class Package(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    fake_price = db.Column(db.Float, nullable=False)
    price = db.Column(db.Float, nullable=False)
    price_tip = db.Column(db.String(100))


# API 路由
@app.route('/get_node_list', methods=['GET'])
def get_node_list():
    nodes = Node.query.all()
    node_list = [{"title": node.title, "config": node.config} for node in nodes]
    return jsonify({"nodeList": node_list})


@app.route('/get_user_info', methods=['POST'])
def get_user_info():
    data = request.get_json()
    user_id = data.get('userId')
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    device_count = Device.query.filter_by(user_id=user_id).count()
    remain_try_time = max(0, (user.register_time + timedelta(days=7) - datetime.utcnow()).total_seconds() / 60)

    return jsonify({
        "username": user.username,
        "email": user.email or "",
        "phone": user.phone or "",
        "remainTryTime": str(int(remain_try_time)),
        "packageType": user.package_type,
        "packageExpiresTime": user.package_expires.timestamp() if user.package_expires else "",
        "deviceCount": device_count
    })


@app.route('/get_package_list', methods=['GET'])
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


# 初始化数据库
def init_db():
    db.create_all()

    # 添加示例节点
    if Node.query.count() == 0:
        nodes = [
            Node(title="US", config=json.dumps({
                "server": "198.2.240.89",
                "port": 49303,
                "password": "Bj6N25kZQS1sei",
                "method": "ssh"
            })),
            Node(title="Japan", config=json.dumps({
                "server": "104.219.209.105",
                "port": 41903,
                "password": "3q1g8vKssMpg",
                "method": "ssh"
            }))
        ]
        db.session.add_all(nodes)

    # 添加示例套餐
    if Package.query.count() == 0:
        packages = [
            Package(type="month", title="1个月", fake_price=9.99, price=7.99, price_tip="立省$2.00"),
            Package(type="quarter", title="3个月", fake_price=24.99, price=19.99, price_tip="立省$5.00"),
            Package(type="year", title="12个月", fake_price=89.99, price=69.99, price_tip="立省$20.00")
        ]
        db.session.add_all(packages)

    db.session.commit()


if __name__ == '__main__':
    init_db()
    app.run(debug=True)