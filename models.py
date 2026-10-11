from datetime import datetime

from flask_login import UserMixin
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class NGO(db.Model):
    __tablename__ = "ngos"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), nullable=False)
    location = db.Column(db.String(200), nullable=False, default="")
    description = db.Column(db.Text, default="")
    status = db.Column(db.String(20), nullable=False, default="pending")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.Text,nullable=True)

    users = db.relationship("User", back_populates="ngo")
    campaigns = db.relationship("Campaign", back_populates="ngo")


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(256), nullable=False)

    # Allowed roles: donor, ngo_staff, admin
    role = db.Column(db.String(20), nullable=False, default="donor")

    ngo_id = db.Column(db.Integer, db.ForeignKey("ngos.id"), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ngo = db.relationship("NGO", back_populates="users")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Campaign(db.Model):
    __tablename__ = "campaigns"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    emergency_type = db.Column(db.String(60), nullable=False)
    location = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_items = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), nullable=False, default="pending")
    last_verified_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    ngo_id = db.Column(db.Integer, db.ForeignKey("ngos.id"), nullable=False)
    ngo = db.relationship("NGO", back_populates="campaigns")


class Donation(db.Model):
    __tablename__ = "donations"

    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.String(30), unique=True, nullable=False, index=True)

    donor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    created_by_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ngo_id = db.Column(db.Integer, db.ForeignKey("ngos.id"), nullable=False)
    campaign_id = db.Column(
        db.Integer, db.ForeignKey("campaigns.id"), nullable=True
    )

    # online or offline
    source = db.Column(db.String(20), nullable=False, default="online")

    # offered, awaiting_confirmation, accepted, cancelled,
    # rejected, received, verified
    status = db.Column(
        db.String(30), nullable=False, default="offered"
    )

    delivery_method = db.Column(
        db.String(30), nullable=False, default="drop_off"
    )

    notes = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    received_at = db.Column(db.DateTime, nullable=True)

    donor = db.relationship("User", foreign_keys=[donor_id])
    created_by = db.relationship("User", foreign_keys=[created_by_id])
    ngo = db.relationship("NGO")
    campaign = db.relationship("Campaign")

    items = db.relationship(
        "DonationItem",
        back_populates="donation",
        cascade="all, delete-orphan"
    )

    events = db.relationship(
        "DonationEvent",
        back_populates="donation",
        cascade="all, delete-orphan",
        order_by="DonationEvent.created_at"
    )


class DonationItem(db.Model):
    __tablename__ = "donation_items"

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(
        db.Integer,
        db.ForeignKey("donations.id"),
        nullable=False
    )

    item_name = db.Column(db.String(120), nullable=False)
    declared_qty = db.Column(db.Integer, nullable=False, default=0)
    received_qty = db.Column(db.Integer, nullable=True)
    accepted_qty = db.Column(db.Integer, nullable=True)

    condition = db.Column(db.String(60), nullable=False, default="good")
    rejection_reason = db.Column(db.String(250), default="")

    donation = db.relationship("Donation", back_populates="items")


class DonationEvent(db.Model):
    __tablename__ = "donation_events"

    id = db.Column(db.Integer, primary_key=True)
    donation_id = db.Column(
        db.Integer,
        db.ForeignKey("donations.id"),
        nullable=False
    )

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)
    event_type = db.Column(db.String(80), nullable=False)
    note = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    donation = db.relationship("Donation", back_populates="events")
    user = db.relationship("User")