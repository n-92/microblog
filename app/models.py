"""
Optional:
	The id field is usually in all models, and is used as the primary key. 
	Each user in the database will be assigned 
	a unique id value, stored in this field. 
	Luckily this is done automatically for us, we just need to provide the id field.


	Once a link between a user and a post is established there are two types 
	of queries that we may need to use. The most trivial one is when you have 
	a blog post and need to know what user wrote it. A more complex query is 
	the reverse of this one. If you have a user, you may want to know all the 
	posts that the user wrote. Flask-SQLAlchemy will help us with both types of queries.

	We have added the Post class, which will represent blog posts written by users. 
	The user_id field in the Post class was initialized as a foreign key, so that 
	Flask-SQLAlchemy knows that this field will link to a user.

	Note that we have also added a new field to the User class called posts, 
	that is constructed as a db.relationship field. This is not an actual database 
	field, so it isn't in our database diagram. For a one-to-many relationship a 
	db.relationship field is normally defined on the "one" side (one user has many posts).
	With this relationship we get a user.posts member that gets us the list of posts from the user. 
	The first argument to db.relationship indicates the "many" class of this relationship. 
	The backref argument defines a field that will be added to the objects of the "many" 
	class that points back at the "one" object. In our case this means that we can use post.author 
	to get the User instance that created a post.
"""


from hashlib import md5
from app import db
from app import app
import sys
if sys.version_info >= (3, 0):
    enable_search = False
else:
    enable_search = True
    import flask_whooshalchemy

followers = db.Table(
    'followers',
    db.Column('follower_id', db.Integer, db.ForeignKey('user.id')),
    db.Column('followed_id', db.Integer, db.ForeignKey('user.id'))
)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nickname = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    posts = db.relationship('Post', backref='author', lazy='dynamic')
    about_me = db.Column(db.String(140))
    last_seen = db.Column(db.DateTime)
    followed = db.relationship('User',
                               secondary=followers,
                               primaryjoin=(followers.c.follower_id == id),
                               secondaryjoin=(followers.c.followed_id == id),
                               backref=db.backref('followers', lazy='dynamic'),
                               lazy='dynamic')

    @staticmethod
    def make_unique_nickname(nickname):
        if User.query.filter_by(nickname=nickname).first() is None:
            return nickname
        version = 2
        while True:
            new_nickname = nickname + str(version)
            if User.query.filter_by(nickname=new_nickname).first() is None:
                break
            version += 1
        return new_nickname

    @property
    def is_authenticated(self):
        return True

    @property
    def is_active(self):
        return True

    @property
    def is_anonymous(self):
        return False

    def get_id(self):
        try:
            return unicode(self.id)  # python 2
        except NameError:
            return str(self.id)  # python 3

    def avatar(self, size):
        return 'http://www.gravatar.com/avatar/%s?d=mm&s=%d' % \
            (md5(self.email.encode('utf-8')).hexdigest(), size)

    def follow(self, user):
        if not self.is_following(user):
            self.followed.append(user)
            return self

    def unfollow(self, user):
        if self.is_following(user):
            self.followed.remove(user)
            return self

    def is_following(self, user):
        return self.followed.filter(
            followers.c.followed_id == user.id).count() > 0

    def followed_posts(self):
        return Post.query.join(
            followers, (followers.c.followed_id == Post.user_id)).filter(
                followers.c.follower_id == self.id).order_by(
                    Post.timestamp.desc())

    def __repr__(self):
        return '<User %r>' % (self.nickname)


class Post(db.Model):
    __searchable__ = ['body']

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.String(140))
    timestamp = db.Column(db.DateTime)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __repr__(self):
        return '<Post %r>' % (self.body)

if enable_search:
    flask_whooshalchemy.whoosh_index(app, Post)