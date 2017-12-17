from . import db, login_manager
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from flask import current_app, request
from datetime import datetime
import hashlib
from markdown import markdown
import bleach


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Permission:
    CHECK_DOWNLOAD = 0x01
    COMMENT = 0x02
    MODERATE_COURSES = 0x04
    MODERATE_COMMENTS = 0x08
    FREEZE = 0x10
    QUERY_STATISTICS = 0x20
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    def __repr__(self):
        return '<Role %r>' % self.name

    @staticmethod
    def insert_roles():
        roles = {
            '普通用户': (Permission.CHECK_DOWNLOAD |
                     Permission.COMMENT, True),
            '课程信息管理员': (Permission.CHECK_DOWNLOAD |
                          Permission.COMMENT |
                          Permission.MODERATE_COMMENTS |
                          Permission.MODERATE_COURSES, False),
            '校领导': (Permission.CHECK_DOWNLOAD |
                       Permission.COMMENT |
                       Permission.QUERY_STATISTICS, False),
            '系统管理员': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    temp_email = db.Column(db.String(64))
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))

    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    can_comment = db.Column(db.Boolean, default=True)

    name = db.Column(db.String(64))
    location = db.Column(db.String(64))
    about_me = db.Column(db.Text())
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)

    avatar_hash = db.Column(db.String(32))

    comments = db.relationship('Comment', backref='author', lazy='dynamic')

    def __repr__(self):
        return '<User %r>' % self.username

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        if self.role is None:
            if self.email == current_app.config['EFC_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()

        if self.email is not None and self.avatar_hash is None:
            self.avatar_hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self, expiration=3600):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        return s.dumps({'confirm': self.id})

    def confirm(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get('confirm') != self.id:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and \
               (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=100, default='identicon', rating='g'):
        if request.is_secure:
            url = 'https://secure.gravatar.com/avatar'
        else:
            url = 'http://www.gravatar.com/avatar'
        hash = self.avatar_hash or hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=url, hash=hash, size=size, default=default, rating=rating)

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     location=forgery_py.address.city(),
                     about_me=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

login_manager.anonymous_user = AnonymousUser


class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    courses = db.relationship('Course', backref='category', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Category {}>'.format(self.name)

    @staticmethod
    def insert_categories():
        category_names = ['编程开发', '音乐', '手工']
        for name in category_names:
            category = Category.query.filter_by(name=name).first()
            if category is None:
                category = Category(name=name)
            db.session.add(category)
        db.session.commit()


class Course(db.Model):
    __tablename__ = 'courses'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'))
    teacher_name = db.Column(db.String(64))
    about_course = db.Column(db.Text())
    chapters = db.relationship('Chapter', backref='course', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        return '<Course {}>'.format(self.name)


class Chapter(db.Model):
    __tablename__ = 'chapters'
    id = db.Column(db.Integer, primary_key=True)
    index = db.Column(db.Integer, index=True)
    name = db.Column(db.String(64))
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id'))
    about_chapter = db.Column(db.Text())
    video_filename = db.Column(db.Text(), default='null')
    outline_filename = db.Column(db.Text(), default='null')
    access_sum = db.Column(db.Integer, default=0)

    prev_index = db.Column(db.Integer)
    next_index = db.Column(db.Integer)

    comments = db.relationship('Comment', backref='chapter', lazy='dynamic', cascade='all, delete-orphan')

    # def __init__(self):
    #     self.prev_index = self.index - 1
    #     self.next_index = self.index + 1

    def __repr__(self):
        return '<Chapter {0} {1}>'.format(self.index, self.name)


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    timestamp = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.id'))
    enabled = db.Column(db.Boolean, default=False)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        chapter_count = Chapter.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            chapter = Chapter.query.offset(randint(0, chapter_count - 1)).first()
            c = Comment(body=forgery_py.lorem_ipsum.sentences(randint(1, 3)),
                        timestamp=forgery_py.date.date(True), author=u, chapter=chapter)
            db.session.add(c)
            db.session.commit()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        allowed_tags = ['a', 'abbr', 'acronym', 'b', 'blockquote', 'code',
                        'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
                        'h1', 'h2', 'h3', 'p']
        target.body_html = bleach.linkify(bleach.clean(
            markdown(value, output_format='html'),
            tags=allowed_tags, strip=True
        ))

db.event.listen(Comment.body, 'set', Comment.on_changed_body)
