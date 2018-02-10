from flask import render_template, redirect, url_for, abort, flash, request, current_app, make_response
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, PostForm, CommentForm
from .. import db
from ..models import User, Role, Post, Permission, Comment
from ..decorators import admin_required, permissions_required


@main.route('/', methods=['GET', 'POST'])
def index():
    """View of the main page"""
    form = PostForm()
    # Check user permissions and validate the form
    if current_user.can(Permission.WRITE_ARTICLES) and form.validate_on_submit():
        # Create a new instance of post from form data and save it into the database
        post = Post(body=form.body.data, author=current_user._get_current_object())
        db.session.add(post)
        db.session.commit()
        return redirect(url_for('main.index'))

    page = request.args.get('page', 1, type=int)
    show_followed = False

    # Show only followed posts if current user is authenticated
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))

    if show_followed:
        query = current_user.followed_posts
    else:
        query = Post.query

    # Setup posts pagination
    pagination = query.order_by(Post.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['YURAIST_POSTS_PER_PAGE'],
        error_out=False)
    posts = pagination.items

    return render_template('index.html',
                           form=form,
                           posts=posts,
                           pagination=pagination,
                           show_followed=show_followed)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '', max_age=30*24*60*60)
    return resp


@main.route('/show_followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('.index')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp


@main.route('/post/<int:id>', methods=['GET', 'POST'])
def post(id):
    """View of the post page"""
    # Finding for a post
    post = Post.query.get_or_404(id)
    form = CommentForm()

    # Validate the comment form and save a new comment into the database
    if form.validate_on_submit():
        comment = Comment(body=form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published.')
        return redirect(url_for('.post', id=post.id, page=-1))

    page = request.args.get('page', 1, type=int)

    # Set the value of the last page to the page variable if passed argument is equal to -1
    if page == -1:
        page = (post.comments.count() - 1) / current_app.config['YURAIST_POSTS_PER_PAGE'] + 1

    # Setup comment pagination
    pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
        page,
        per_page=current_app.config['YURAIST_POSTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items

    return render_template('post.html',
                           posts=[post],
                           form=form,
                           comments=comments,
                           pagination=pagination)


@main.route('/moderate')
@login_required
@permissions_required(Permission.MODERATE_COMMENTS)
def moderate():
    """View of the page with list of all of the comments for moderators"""
    page = request.args.get('page', 1, type=int)
    pagination = Comment.query.order_by(Comment.timestamp.desc()).paginate(
        page,
        per_page=current_app.config['YURAIST_POSTS_PER_PAGE'],
        error_out=False)
    comments = pagination.items

    return render_template('moderate.html',
                           comments=comments,
                           pagination=pagination,
                           page=page)


@main.route('/moderate/enable/<int:id>')
@login_required
@permissions_required(Permission.MODERATE_COMMENTS)
def moderate_enable(id):
    """View for making comments enabled"""
    comment = Comment.query.get_or_404(id)
    comment.disabled = False
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/moderate/disable/<int:id>')
@login_required
@permissions_required(Permission.MODERATE_COMMENTS)
def moderate_disable(id):
    """View for making comments disabled"""
    comment = Comment.query.get_or_404(id)
    comment.disabled = True
    db.session.add(comment)
    db.session.commit()
    return redirect(url_for('.moderate', page=request.args.get('page', 1, type=int)))


@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_post(id):
    """View of the post editing page"""
    # Finding for needed post
    post = Post.query.get_or_404(id)

    # Return error 403 if the user does not have permissions for editing
    if current_user != post.author and not current_user.can(Permission.ADMINISTER):
        abort(403)

    form = PostForm()

    # Validate the form and update data in the database
    if form.validate_on_submit():
        post.body = form.body.data
        db.session.add(post)
        db.session.commit()
        flash('The post has been updated.')
        return redirect(url_for('.post', id=post.id))

    # Update form data
    form.body.data = post.body
    return render_template('edit_post.html', post=post, form=form)


@main.route('/user/<username>')
def user(username):
    """View of the user page"""
    # Get needed user by id
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)

    # Get posts of the user
    posts = user.posts.order_by(Post.timestamp.desc()).all()
    return render_template('user.html', user=user, posts=posts)


@main.route('/follow/<username>')
@login_required
@permissions_required(Permission.FOLLOW)
def follow(username):
    """View for following"""

    # Finding for a user
    user = User.query.filter_by(username=username).first()

    # Check the user is valid
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))

    # Check the user is not already followed
    if current_user.is_following(user):
        flash('You are already following the user')
        return redirect(url_for('.user', username=username))

    # Follow the user
    current_user.follow(user)
    flash('You are now following %s.' % username)
    return redirect(url_for('.user', username=username))


@main.route('/unfollow/<username>')
@login_required
@permissions_required(Permission.FOLLOW)
def unfollow(username):
    """View for unfollowing"""

    # Finding for needed user by username
    user = User.query.filter_by(username=username).first()

    # Check the user exists
    if user is None:
        flash('Invalid user')
        return redirect(url_for('.index'))

    # Check the user is followed
    if not current_user.is_following(user):
        flash('You are already not following this user.')
        return redirect(url_for('.user', username=username))

    # Unfollow the user
    current_user.unfollow(user)
    return redirect(url_for('.user', username=username))


@main.route('/followers/<username>')
def followers(username):
    """View of the list of followers"""

    # Get the followed user
    user = User.query.filter_by(username=username).first()

    # Check user validness
    if user is None:
        flash('Invalid user')

    # Setup pagination of follower list
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page,
        per_page=current_app.config['YURAIST_POSTS_PER_PAGE'],
        error_out=False)

    # List of followers
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html',
                           user=user,
                           title='Follower of',
                           endpoint='.followers',
                           pagination=pagination,
                           follows=follows)


@main.route('/followed-by/<username>')
def followed_by(username):
    """View of the list of users followed by the specific user"""

    # Get the specific user
    user = User.query.filter_by(username=username).first()

    # Check user validnes
    if user is None:
        flash('Invalid user.')
        return redirect(url_for('.index'))

    # Setup pagination of the followed user list
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page,
        per_page=current_app.config['YURAIST_POSTS_PER_PAGE'],
        error_out=False)

    # List of followed users
    follows = [{'user': item.followed, 'timestamp': item.timestamp} for item in pagination.items]
    return render_template('followers.html',
                           user=user,
                           title="Followed by",
                           endpoint='.followed_by',
                           pagination=pagination,
                           follows=follows)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    """View for user profile editing"""
    form = EditProfileForm()

    # Validate the form data
    if form.validate_on_submit():
        # Update user data
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data

        # Update data in the database
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))

    # Update the form data
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit_profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    """View for profile editing for administrators"""

    # Get needed user
    user = User.query.get_or_404(id)

    # Setup the form with user data
    form = EditProfileAdminForm(user=user)

    # Validate the form data
    if form.validate_on_submit():
        # Update user data
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data

        # Update data in the database
        db.session.add(user)
        db.session.commit()
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))

    # Update the form data
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me

    return render_template('edit_profile.html', form=form, user=user)
