from flask import render_template, url_for, redirect, flash, current_app
from flask_login import current_user
from .. import db, videos, outlines
from ..models import Category, Permission, Course, Chapter, User, Comment
from ..decorators import admin_required, permission_required
from flask_login import login_required
from . import admin
from .forms import CategoryAddForm, CategoryModerateForm, CategoryDeleteForm, \
    CourseAddForm, CourseModerateForm, \
    ChapterAddForm, ChapterModerateForm, ChapterUploadForm
import os


@admin.route('/category-add', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def category_add():
    form = CategoryAddForm()
    if form.validate_on_submit():
        new_category = Category(name=form.new_category.data)
        db.session.add(new_category)
        db.session.commit()
        current_app.logger.info('管理员*{}*\n添加了新课程类别*{}*'.format(current_user._get_current_object().email, new_category.name))
        flash('新类别已经添加。')
        return redirect(url_for('main.index'))
    return render_template('admin/category-add.html', form=form)


@admin.route('/category-moderate/<int:id>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def category_moderate(id):
    category = Category.query.get_or_404(id)
    form = CategoryModerateForm()
    if form.validate_on_submit():
        category.name = form.name.data
        db.session.add(category)
        current_app.logger.info('管理员*{}*\n修改了类别信息*{}*'.format(current_user._get_current_object().email,
                                                          category.name))
        flash('类别信息已被修改。')
        return redirect(url_for('main.index'))
    form.name.data = category.name
    return render_template('admin/category-moderate.html', form=form)


@admin.route('/category-delete', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def category_delete():
    form = CategoryDeleteForm()
    if form.validate_on_submit():
        category = Category.query.get(form.name.data)
        current_app.logger.warning('管理员*{}*\n删除了课程类别*{}*的所有内容'.format(current_user._get_current_object().email,
                                                            category.name))
        db.session.delete(category)
        flash('该类别的所有课程已经删除。')
        return redirect(url_for('main.index'))
    return render_template('admin/category-delete.html', form=form)


@admin.route('/course-add', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def course_add():
    form = CourseAddForm()
    if form.validate_on_submit():
        course = Course(name=form.name.data,
                        category_id=form.category.data,
                        teacher_name=form.teacher_name.data,
                        about_course=form.about_course.data)
        db.session.add(course)
        chapter = Chapter(name='初始章节',
                          index=1,
                          prev_index=0,
                          next_index=2,
                          course=course,
                          about_chapter='默认内容')
        db.session.add(chapter)
        current_app.logger.info('管理员*{}*\n添加了*{}*类别的新课程*{}*'.format(current_user._get_current_object().email,
                                                                               Category.query.get(course.category_id).name,
                                                                     course.name))
        flash('新课程已经添加。')
        return redirect(url_for('main.index'))
    return render_template('admin/course-add.html', form=form)


@admin.route('/course-moderate/<int:course_id>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def course_moderate(course_id):
    course = Course.query.get_or_404(course_id)
    form = CourseModerateForm()
    if form.validate_on_submit():
        course.name = form.name.data
        course.category = Category.query.get(form.category.data)
        course.teacher_name = form.teacher_name.data
        course.about_course = form.about_course.data
        db.session.add(course)
        current_app.logger.info('管理员*{}*\n修改了*{}*类别的*{}*课程的信息'.format(current_user._get_current_object().email,
                                                                      Category.query.get(course.category_id).name,
                                                                      course.name))
        flash('课程信息已被修改。')
        return redirect(url_for('main.show_course', course_id=course.id, chapter_index=1))
    form.name.data = course.name
    form.category.data = course.category_id
    form.teacher_name.data = course.teacher_name
    form.about_course.data = course.about_course
    return render_template('admin/course-moderate.html', form=form)


@admin.route('/course-delete/<int:course_id>')
@permission_required(Permission.MODERATE_COURSES)
def course_delete(course_id):
    course = Course.query.get_or_404(course_id)
    category = course.category
    current_app.logger.warning('管理员*{}*\n删除了*{}*类别的*{}*课程的所有内容'.format(current_user._get_current_object().email,
                                                                    category,
                                                                    course.name))
    db.session.delete(course)
    flash('该课程已经完全删除。')
    return render_template('category-courses.html', category=category)


@admin.route('/chapter-add/<int:course_id>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def chapter_add(course_id):
    course = Course.query.get_or_404(course_id)
    form = ChapterAddForm(course=course)
    if form.validate_on_submit():
        index = form.prev_index.data + 1
        count = course.chapters.count()
        chapters = course.chapters
        for i in range(index, count + 1):
            chapter = chapters.filter_by(index=i).first()
            chapter.prev_index += 1
            chapter.index += 1
            chapter.next_index += 1
            db.session.add(chapter)
        db.session.commit()

        chapter = Chapter(prev_index=index - 1,
                          index=index,
                          next_index=index + 1,
                          name=form.name.data,
                          course=Course.query.get(course_id),
                          about_chapter=form.about_chapter.data)
        db.session.add(chapter)
        current_app.logger.info('管理员*{}*\n添加了新的章节*{}*至课程*{}*'.format(current_user._get_current_object().email,
                                                                     '第{}章 '.format(chapter.index) + chapter.name,
                                                                       course.name))
        flash('已经添加一个新的章节至本课程。')
        return redirect(url_for('main.show_course', course_id=course_id, chapter_index=1))
    return render_template('admin/chapter-add.html', form=form)


@admin.route('/chapter-moderate/<int:course_id>/<int:chapter_index>', methods=['GET', 'POST'])
@permission_required(Permission.MODERATE_COURSES)
def chapter_moderate(course_id, chapter_index):
    course = Course.query.get_or_404(course_id)
    chapter = course.chapters.filter_by(index=chapter_index).first()
    form = ChapterModerateForm()
    form2 = ChapterUploadForm()
    if form.validate_on_submit():
        chapter.name = form.name.data
        chapter.about_chapter = form.about_chapter.data
        db.session.add(chapter)
        current_app.logger.info('管理员*{}*\n修改了课程*{}*的*{}*的章节信息'.format(current_user._get_current_object().email,
                                                                       Course.query.get(chapter.course_id).name,
                                                                        '第{}章 '.format(chapter.index) + chapter.name))
        flash('章节信息已被修改。')
        return redirect(url_for('main.show_course', course_id=course_id, chapter_index=chapter_index))
    if form2.validate_on_submit():
        video_path = os.path.join(videos.path(chapter.video_filename), chapter.video_filename)
        outline_path = os.path.join(outlines.path(chapter.outline_filename), chapter.outline_filename)
        if os.path.exists(video_path):
            os.remove(video_path)
        if os.path.exists(outline_path):
            os.remove(outline_path)
        chapter.video_filename = videos.save(form2.video.data,
                                             name='{}-chapter{}-{}.'.format(course.name, chapter.index, chapter.name))
        chapter.outline_filename = outlines.save(form2.outline.data,
                                                 name='{}-chapter{}-{}.'.format(course.name, chapter.index,
                                                                                chapter.name))
        db.session.add(chapter)
        current_app.logger.info('管理员*{}*\n修改了课程*{}*的*{}*的相关文件'.format(current_user._get_current_object().email,
                                                                      Course.query.get(chapter.course_id).name,
                                                                      '第{}章 '.format(chapter.index) + chapter.name))
        flash('章节相关文件已被修改。')
        return redirect(url_for('main.show_course', course_id=course_id, chapter_index=chapter_index))
    form.name.data = chapter.name
    form.about_chapter.data = chapter.about_chapter
    return render_template('admin/chapter-moderate.html', form=form, form2=form2)


@admin.route('/chapter-delete/<int:chapter_id>')
@permission_required(Permission.MODERATE_COURSES)
def chapter_delete(chapter_id):
    chapter = Chapter.query.get_or_404(chapter_id)
    index = chapter.index + 1
    course = chapter.course
    if course.chapters.count() == 1:
        flash('第一章内容默认不能删除，请直接修改第一章节内容或完全删除该课程。')
        return redirect(url_for('main.show_course', course_id=course.id, chapter_index=1))

    current_app.logger.warning('管理员*{}*\n删除了课程*{}*的*{}*的所有内容'.format(current_user._get_current_object().email,
                                                                    Course.query.get(chapter.course_id).name,
                                                                    '第{}章 '.format(chapter.index) + chapter.name))

    db.session.delete(chapter)
    db.session.commit()
    chapters = course.chapters
    for i in range(index, chapters.count() + 2):
        chapter = chapters.filter_by(index=i).first()
        chapter.prev_index -= 1
        chapter.index -= 1
        chapter.next_index -= 1
        db.session.add(chapter)
    db.session.commit()
    flash('该章节已经删除。')
    return redirect(url_for('main.show_course', course_id=course.id, chapter_index=1))


@admin.route('/freeze/<int:user_id>')
@admin_required
def freeze(user_id):
    user = User.query.get_or_404(user_id)
    user.role.permissions -= Permission.COMMENT
    flash('用户已被冻结。')
    return redirect(url_for('main.user', username=user.username))


@admin.route('/unfreeze/<int:user_id>')
@admin_required
def unfreeze(user_id):
    user = User.query.get_or_404(user_id)
    user.role.permissions += Permission.COMMENT
    flash('用户已解除冻结。')
    return redirect(url_for('main.user', username=user.username))


@admin.route('/check-freeze')
@admin_required
def check_freeze():
    frozen_users = []
    for user in User.query.all():
        if not user.can(Permission.COMMENT):
            frozen_users.append(user)
    return render_template('show-frozen-users.html', frozen_users=frozen_users)


@admin.route('/enable-comment/<int:comment_id>')
@permission_required(Permission.MODERATE_COMMENTS)
def enable_comment(comment_id):
    comment = Comment.query.get(comment_id)
    comment.enabled = True
    db.session.add(comment)
    flash('评论审核通过。')
    chapter = Chapter.query.get(comment.chapter_id)
    return redirect(url_for('main.show_chapter', course_id=chapter.course_id, chapter_index=chapter.index))


@admin.route('/check-comments')
@permission_required(Permission.MODERATE_COMMENTS)
def check_comments():
    comments = Comment.query.filter_by(enabled=False).all()
    return render_template('show-disabled-comments.html', comments=comments)


@admin.route('/enable-comment/shortcut/<int:comment_id>')
@permission_required(Permission.MODERATE_COMMENTS)
def enable_comment_shortcut(comment_id):
    comment = Comment.query.get(comment_id)
    comment.enabled = True
    db.session.add(comment)
    flash('评论审核通过。')
    return redirect(url_for('admin.check_comments'))
