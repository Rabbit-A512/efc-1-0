from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, SelectField, TextAreaField, IntegerField
from wtforms.validators import DataRequired, Length, Regexp, ValidationError
from ..models import Category, Chapter


class CategoryAddForm(FlaskForm):
    new_category = StringField('新的类别', validators=[Length(1, 64)])
    submit = SubmitField('添加')

    def validate_new_category(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError('类别已经存在。')


class CategoryModerateForm(FlaskForm):
    name = StringField('类别名称', validators=[Length(1, 64)])
    submit = SubmitField('修改')

    def validate_name(self, field):
        if Category.query.filter_by(name=field.data).first():
            raise ValidationError("类别已经存在。")


class CategoryDeleteForm(FlaskForm):
    name = SelectField('课程类别', coerce=int)
    submit = SubmitField('删除')

    def __init__(self, *args, **kwargs):
        super(CategoryDeleteForm, self).__init__(*args, **kwargs)
        self.name.choices = [(category.id, category.name) for category in Category.query.order_by(Category.id).all()]


class CourseAddForm(FlaskForm):
    name = StringField('课程名称', validators=[Length(1, 64)])
    category = SelectField('课程类别', coerce=int)
    teacher_name = StringField('教师姓名', validators=[Length(0, 64)])
    about_course = TextAreaField('关于课程')
    submit = SubmitField('添加')

    def __init__(self, *args, **kwargs):
        super(CourseAddForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.id).all()]


class CourseModerateForm(FlaskForm):
    name = StringField('课程名称', validators=[Length(1, 64)])
    category = SelectField('课程类别', coerce=int)
    teacher_name = StringField('教师姓名', validators=[Length(0, 64)])
    about_course = TextAreaField('关于课程')
    submit = SubmitField('修改')

    def __init__(self, *args, **kwargs):
        super(CourseModerateForm, self).__init__(*args, **kwargs)
        self.category.choices = [(category.id, category.name)
                                 for category in Category.query.order_by(Category.id).all()]


class ChapterAddForm(FlaskForm):
    prev_index = SelectField('选择添加在哪一个章节之后', coerce=int)
    name = StringField('章节名称', validators=[Length(1, 64)])
    about_chapter = TextAreaField('关于本章')
    submit = SubmitField('添加')

    def __init__(self, *args, **kwargs):
        super(ChapterAddForm, self).__init__(*args, **kwargs)
        course = kwargs['course']
        self.prev_index.choices = [(chapter.index, '第{0}章 {1}'.format(chapter.index, chapter.name))
                                 for chapter in course.chapters.order_by(Chapter.index).all()]


class ChapterModerateForm(FlaskForm):
    name = StringField('章节名称', validators=[Length(1, 64)])
    about_chapter = TextAreaField('关于本章')
    submit = SubmitField('修改')
