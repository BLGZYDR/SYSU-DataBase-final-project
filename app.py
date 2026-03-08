import enum

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime

app = Flask(__name__)
HOSTNAME = "127.0.0.1"
PORT = 3306
USERNAME = "root"
PASSWORD = "2015Xz0202"
DATABASE = "hotel_management"
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{USERNAME}:{PASSWORD}@{HOSTNAME}:{PORT}/{DATABASE}?charset=utf8mb4"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# 枚举定义
class RoleEnum(enum.Enum):
    FRONT_DESK = "前台"
    ADMIN = "管理员"

class RoomStatusEnum(enum.Enum):
    AVAILABLE = "空闲"
    RESERVED = "预留"
    OCCUPIED = "已入住"

class OrderStatusEnum(enum.Enum):
    BOOKED = "已预订"
    CANCELLED = "已取消"
    CHECKED_IN = "已入住"
    COMPLETED = "已完成"

class RoomTypeEnum(enum.Enum):
    STANDARD = "标准房"
    KING_BED = "大床房"
    TWIN_BED = "双床房"
    FAMILY_SUITE = "家庭套房"

class Guest(db.Model):
    __tablename__ = 'guest'
    guest_id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(100), nullable=False, unique=True)
    id_card = db.Column(db.String(100), nullable=False, unique=True)

    # 关系
    orders_as_primary = db.relationship('Order', foreign_keys='Order.guest_id', backref='primary_guest', lazy=True)
    order_guests = db.relationship('OrderGuest', backref='guest', lazy=True, cascade='all, delete-orphan')


class Operator(db.Model):
    __tablename__ = 'operator'
    operator_id = db.Column(db.Integer, primary_key=True)
    account_name = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role_name = db.Column(db.Enum(RoleEnum), nullable=False, default=RoleEnum.FRONT_DESK)
    # 关系
    total_revenue_reports = db.relationship('TotalRevenueReport', backref='operator', lazy=True)
    room_type_reports = db.relationship('RoomTypeReport', backref='operator', lazy=True)
    day_revenue_reports = db.relationship('DayRevenueReport', backref='operator', lazy=True)
    price_change_logs = db.relationship('RoomTypePriceChangeLog', backref='operator', lazy=True)
    room_add_delete_logs = db.relationship('RoomAddDeleteLog', backref='operator', lazy=True)
    room_type_change_logs = db.relationship('RoomTypeChangeLog', backref='operator', lazy=True)


class Room(db.Model):
    __tablename__ = 'room'
    room_id = db.Column(db.Integer, primary_key=True)
    type_name = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    base_price = db.Column(db.Numeric(10, 2), nullable=False)  # 改为 Decimal
    room_number = db.Column(db.String(50), nullable=False)
    status = db.Column(db.Enum(RoomStatusEnum), nullable=False, default=RoomStatusEnum.AVAILABLE)
    is_deleted = db.Column(db.Boolean, nullable=False, default=False)

    # 关系
    order_rooms = db.relationship('OrderRoom', backref='room', lazy=True, cascade='all, delete-orphan')
    # 新增关系
    add_delete_logs = db.relationship('RoomAddDeleteLog', backref='room', lazy=True)
    type_change_logs = db.relationship('RoomTypeChangeLog', backref='room', lazy=True)


class Order(db.Model):
    __tablename__ = 'order'
    order_id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.guest_id'), nullable=False)
    order_status = db.Column(db.Enum(OrderStatusEnum), nullable=False, default=OrderStatusEnum.BOOKED)
    total_people = db.Column(db.Integer, nullable=False)
    total_rooms = db.Column(db.Integer, nullable=False)
    expect_check_in_time = db.Column(db.Date, nullable=False)
    expect_check_out_time = db.Column(db.Date, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)  # 改为 Decimal
    order_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # 关系
    order_guests = db.relationship('OrderGuest', backref='order', lazy=True, cascade='all, delete-orphan')
    order_rooms = db.relationship('OrderRoom', backref='order', lazy=True, cascade='all, delete-orphan')


class OrderGuest(db.Model):
    __tablename__ = 'order_guest'
    relation_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.guest_id'), nullable=False)


class OrderRoom(db.Model):
    __tablename__ = 'order_room'
    relation_id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('order.order_id'), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=False)
    type_name = db.Column(db.Enum(RoomTypeEnum), nullable=False)  # 改为枚举
    price = db.Column(db.Numeric(10, 2), nullable=False)  # 改为 Decimal


class TotalRevenueReport(db.Model):
    __tablename__ = 'total_revenue_report'
    template_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    orders_count = db.Column(db.Integer, nullable=False)
    total_guest = db.Column(db.Integer, nullable=False)
    total_revenue = db.Column(db.Numeric(10, 2), nullable=False)


class RoomTypeReport(db.Model):
    __tablename__ = 'room_type_report'
    template_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    room_type = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    total_revenue = db.Column(db.Numeric(10, 2), nullable=False)


class DayRevenueReport(db.Model):
    __tablename__ = 'day_revenue_report'
    template_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    date = db.Column(db.Date, nullable=False)
    total_guest = db.Column(db.Integer, nullable=False)
    total_revenue = db.Column(db.Numeric(10, 2), nullable=False)


class RoomTypePriceChangeLog(db.Model):
    __tablename__ = 'room_type_price_change_log'
    log_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    room_type = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    old_price = db.Column(db.Numeric(10, 2), nullable=False)
    new_price = db.Column(db.Numeric(10, 2), nullable=False)
    change_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class RoomAddDeleteLog(db.Model):
    __tablename__ = 'room_add_delete_log'
    log_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    # 新增外键关联room表
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    type_name = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    operation_type = db.Column(db.String(10), nullable=False)
    operation_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class RoomTypeChangeLog(db.Model):
    __tablename__ = 'room_type_change_log'
    log_id = db.Column(db.Integer, primary_key=True)
    operator_id = db.Column(db.Integer, db.ForeignKey('operator.operator_id'), nullable=False)
    # 新增外键关联room表
    room_id = db.Column(db.Integer, db.ForeignKey('room.room_id'), nullable=False)
    room_number = db.Column(db.String(50), nullable=False)
    old_type = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    new_type = db.Column(db.Enum(RoomTypeEnum), nullable=False)
    change_time = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)