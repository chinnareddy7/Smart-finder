
from datetime import datetime, timezone
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


def utc_now():
    """Returns naive UTC datetime object."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(25), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationships
    lost_items = db.relationship(
        'LostItem', back_populates='reporter',
        cascade='all, delete-orphan', lazy='dynamic'
    )
    found_items = db.relationship(
        'FoundItem', back_populates='reporter',
        cascade='all, delete-orphan', lazy='dynamic'
    )
    sent_requests = db.relationship(
        'ContactRequest', foreign_keys='ContactRequest.sender_id',
        back_populates='sender', cascade='all, delete-orphan',
        lazy='dynamic'
    )
    received_requests = db.relationship(
        'ContactRequest', foreign_keys='ContactRequest.receiver_id',
        back_populates='receiver', cascade='all, delete-orphan',
        lazy='dynamic'
    )
    notifications = db.relationship(
        'Notification', back_populates='user',
        cascade='all, delete-orphan',
        order_by='Notification.created_at.desc()', lazy='dynamic'
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def unread_notifications_count(self):
        return self.notifications.filter_by(is_read=False).count()

    def __repr__(self):
        return f'<User {self.student_id} - {self.name}>'


class LostItem(db.Model):
    __tablename__ = 'lost_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False, index=True)
    lost_date = db.Column(db.Date, nullable=False)
    additional_details = db.Column(db.Text, nullable=True)

    # Public Contact Details
    contact_name = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(25), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_public = db.Column(db.Boolean, default=False, nullable=False)

    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(20), default='Lost', nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    reporter = db.relationship('User', back_populates='lost_items')
    matches = db.relationship(
        'Match', back_populates='lost_item',
        cascade='all, delete-orphan', lazy='dynamic',
        order_by='Match.similarity_score.desc()'
    )
    contact_requests = db.relationship(
        'ContactRequest', back_populates='lost_item',
        cascade='all, delete-orphan', lazy='dynamic'
    )

    def __repr__(self):
        return f'<LostItem {self.id}: {self.item_name}>'


class FoundItem(db.Model):
    __tablename__ = 'found_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    item_name = db.Column(db.String(120), nullable=False)
    category = db.Column(db.String(60), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150), nullable=False, index=True)
    found_date = db.Column(db.Date, nullable=False)
    storage_location = db.Column(
        db.String(150), nullable=True
    )
    additional_details = db.Column(db.Text, nullable=True)

    # Public Contact Details
    contact_name = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(25), nullable=True)
    contact_email = db.Column(db.String(120), nullable=True)
    contact_public = db.Column(db.Boolean, default=False, nullable=False)

    image_filename = db.Column(db.String(255), nullable=True)
    status = db.Column(
        db.String(20), default='Found', nullable=False, index=True
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    reporter = db.relationship('User', back_populates='found_items')
    matches = db.relationship(
        'Match', back_populates='found_item',
        cascade='all, delete-orphan', lazy='dynamic',
        order_by='Match.similarity_score.desc()'
    )
    contact_requests = db.relationship(
        'ContactRequest', back_populates='found_item',
        cascade='all, delete-orphan', lazy='dynamic'
    )

    def __repr__(self):
        return f'<FoundItem {self.id}: {self.item_name}>'


class Match(db.Model):
    __tablename__ = 'matches'
    __table_args__ = (
        db.UniqueConstraint(
            'lost_item_id', 'found_item_id',
            name='uq_lost_found_match'
        ),
    )

    id = db.Column(db.Integer, primary_key=True)
    lost_item_id = db.Column(
        db.Integer, db.ForeignKey('lost_items.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    found_item_id = db.Column(
        db.Integer, db.ForeignKey('found_items.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    similarity_score = db.Column(db.Float, nullable=False)
    text_score = db.Column(db.Float, default=0.0)
    category_score = db.Column(db.Float, default=0.0)
    location_score = db.Column(db.Float, default=0.0)
    category_match = db.Column(db.Boolean, default=False)
    location_match = db.Column(db.Boolean, default=False)
    explanation = db.Column(db.Text, nullable=True)
    status = db.Column(
        db.String(20), default='Suggested', nullable=False
    )
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    lost_item = db.relationship('LostItem', back_populates='matches')
    found_item = db.relationship('FoundItem', back_populates='matches')

    def __repr__(self):
        return (
            f'<Match L{self.lost_item_id}-F{self.found_item_id} '
            f'({self.similarity_score:.1f}%)>'
        )


class ContactRequest(db.Model):
    __tablename__ = 'contact_requests'

    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    receiver_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    item_type = db.Column(db.String(10), nullable=False)
    lost_item_id = db.Column(
        db.Integer, db.ForeignKey('lost_items.id', ondelete='SET NULL'),
        nullable=True
    )
    found_item_id = db.Column(
        db.Integer, db.ForeignKey('found_items.id', ondelete='SET NULL'),
        nullable=True
    )
    message = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(20), default='Pending', nullable=False)
    response_note = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=utc_now)
    updated_at = db.Column(db.DateTime, default=utc_now, onupdate=utc_now)

    # Relationships
    sender = db.relationship(
        'User', foreign_keys=[sender_id], back_populates='sent_requests'
    )
    receiver = db.relationship(
        'User', foreign_keys=[receiver_id], back_populates='received_requests'
    )
    lost_item = db.relationship('LostItem', back_populates='contact_requests')
    found_item = db.relationship('FoundItem', back_populates='contact_requests')

    def __repr__(self):
        return (
            f'<ContactRequest {self.id}: '
            f'{self.sender_id}->{self.receiver_id} [{self.status}]>'
        )


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False, index=True
    )
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=False)
    link = db.Column(db.String(255), nullable=True)
    is_read = db.Column(db.Boolean, default=False, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=utc_now)

    # Relationship
    user = db.relationship('User', back_populates='notifications')

    def __repr__(self):
        return f'<Notification {self.id} for User {self.user_id}>'
