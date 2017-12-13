from datetime import datetime
from flask import render_template, session, redirect, url_for, current_app, abort, flash, request, send_from_directory
from flask_login import login_required, current_user
from . import main
from .forms import EditProfileForm, EditProfileAdminForm, CommentForm
from .. import db, videos, outlines
from ..models import User, Role, Permission, Category, Course, Chapter, Comment
from ..decorators import admin_required, permission_required
from os import remove
from os.path import exists


@main.route('/')
def index():
    categories = Category.query.order_by(Category.id).all()
    return render_template('index.html', categories=categories)


@main.route('/info')
def info():
    return render_template('info.html')


@main.route('/user/<username>')
def user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        abort(404)
    comments = user.comments.order_by(Comment.timestamp.desc()).all()
    return render_template('user.html', user=user, comments=comments)


@main.route('/edit-profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.add(current_user)
        flash('Your profile has been updated.')
        return redirect(url_for('.user', username=current_user.username))
    form.name.data = current_user.name
    form.location.data = current_user.location
    form.about_me.data = current_user.about_me
    return render_template('edit-profile.html', form=form)


@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
    user = User.query.get_or_404(id)
    form = EditProfileAdminForm(user=user)
    if form.validate_on_submit():
        user.email = form.email.data
        user.username = form.username.data
        user.confirmed = form.confirmed.data
        user.role = Role.query.get(form.role.data)
        user.name = form.name.data
        user.location = form.location.data
        user.about_me = form.about_me.data
        db.session.add(user)
        flash('The profile has been updated.')
        return redirect(url_for('.user', username=user.username))
    form.email.data = user.email
    form.username.data = user.username
    form.confirmed.data = user.confirmed
    form.role.data = user.role_id
    form.name.data = user.name
    form.location.data = user.location
    form.about_me.data = user.about_me
    return render_template('edit-profile.html', form=form, user=user)


@main.route('/edit/<int:comment_id>', methods=['GET', 'POST'])
@login_required
def edit(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if current_user != comment.author and not current_user.can(Permission.MODERATE_COMMENTS):
        abort(403)
    form = CommentForm()
    if form.validate_on_submit():
        comment.body = form.body.data
        db.session.add(comment)
        db.session.commit()
        flash('评论已被修改。')
        return render_template('edit-comment.html', form=form)
    form.body.data = comment.body
    return render_template('edit-comment.html', form=form)


@main.route('/category-courses/<int:id>')
@login_required
@permission_required(Permission.CHECK_DOWNLOAD)
def category_courses(id):
    category = Category.query.get(id)
    return render_template('category-courses.html', category=category)


@main.route('/courses/<int:course_id>/<int:chapter_index>')
@login_required
@permission_required(Permission.CHECK_DOWNLOAD)
def show_course(course_id, chapter_index):
    course = Course.query.get(course_id)
    display_chapter = course.chapters.filter_by(index=chapter_index).first()
    chapters = course.chapters.order_by(Chapter.index).all()
    return render_template('show-course.html', course=course, display_chapter=display_chapter, chapters=chapters)


@main.route('/show-chapter/<int:course_id>/<int:chapter_index>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.CHECK_DOWNLOAD)
def show_chapter(course_id, chapter_index):
    course = Course.query.get_or_404(course_id)
    display_chapter = course.chapters.filter_by(index=chapter_index).first()
    if not display_chapter:
        if chapter_index == 0:
            display_chapter = course.chapters.first()
            flash('已经是第一章。')
        else:
            display_chapter = course.chapters.filter_by(index=chapter_index - 1).first()
            flash('已经是最后一章。')

    form = CommentForm()
    if current_user.can(Permission.COMMENT) and form.validate_on_submit():
        comment = Comment(body=form.body.data,
                          author=current_user._get_current_object(),
                          chapter=display_chapter)
        db.session.add(comment)

    page = request.args.get('page', 1, type=int)
    pagination = display_chapter.comments.order_by(Comment.timestamp.desc()).paginate(
        page, per_page=current_app.config['EFC_COMMENTS_PER_PAGE'], error_out=False
    )
    comments = pagination.items

    video_url = '#'
    outline_url = '#'
    if exists(videos.path(display_chapter.video_filename)):
        video_url = videos.url(display_chapter.video_filename)
    if exists(outlines.path(display_chapter.outline_filename)):
        outline_url = outlines.url(display_chapter.outline_filename)
    return render_template('show-chapter.html',
                           form=form,
                           display_chapter=display_chapter,
                           video_url=video_url,
                           outline_url=outline_url,
                           comments=comments,
                           pagination=pagination)


@main.route('/videos/<video_filename>')
@login_required
@permission_required(Permission.CHECK_DOWNLOAD)
def download_video(video_filename):
    return send_from_directory(current_app.config['UPLOADED_VIDEOS_DEST'], video_filename)
