from flask import render_template, redirect, request, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
from . import auth
from ..models import User
from .forms import LoginForm, RegistrationForm, EmailConfirmationForm, FindPasswordForm, ChangePasswordForm
from .. import db
from ..email import send_email
import hashlib


@auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, form.remember_me.data)
            return redirect(request.args.get('next') or url_for('main.index'))
        flash('Invalid username or password.')
    return render_template('auth/login.html', form=form)


@auth.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.')
    return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(email=form.email.data,
                    username=form.username.data,
                    password=form.password.data)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_email(user.email, 'Confirm Your Account',
                   'auth/email/confirm', user=user, token=token)
        flash('A confirmation email has been sent to you by email.')
        return redirect(url_for('main.index'))
    return render_template('auth/register.html', form=form)


@auth.route('/confirm/<token>')
@login_required
def confirm(token):
    if current_user.confirmed:
        return redirect(url_for('main.index'))
    if current_user.confirm(token):
        flash('You have confirmed your account. Thanks!')
    else:
        flash('The confirmation link is invalid or has expired.')
    return redirect(url_for('main.index'))


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed \
                and request.endpoint \
                and request.endpoint[:5] != 'auth.' \
                and request.endpoint != 'static':
            return redirect(url_for('auth.unconfirmed'))


@auth.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.index'))
    return render_template('auth/unconfirmed.html', user=current_user)


@auth.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_email(current_user.email, 'Confirm Your Account',
               'auth/email/confirm', user=current_user, token=token)
    flash('A new confirmation email has been sent to you by email.')
    return redirect(url_for('main.index'))


@auth.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        user = current_user
        if user.verify_password(form.old_password.data):
            user.password = form.new_password.data
            flash('You have changed your password.')
            return redirect(url_for('main.index'))
        flash('Wrong old password.')
    return render_template('auth/change_password.html', form=form)


@auth.route('/wait_for_confirmation', methods=['GET', 'POST'])
def wait_for_confirmation():
    form = EmailConfirmationForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None:
            token = user.generate_confirmation_token()
            send_email(user.email, 'Confirm Your Account', 'auth/email/find_password', user=user, token=token)
            flash('A confirmation email has been sent to your email address. Check it out!')
        else:
            flash('Invalid email. Maybe you have not registered yet.')
    return render_template('auth/wait_for_confirmation.html', form=form)


@auth.route('/find_password_confirm/<email>/<token>', methods=['GET', 'POST'])
def find_password_confirm(email, token):
    user = User.query.filter_by(email=email).first()
    if user.confirm(token):
        flash('You have confirmed your account. Now you can set a new password.')
        return redirect(url_for('auth.find_password', email=user.email))
    else:
        flash('The confirmation link is invalid or has expired.')
        return redirect(url_for('auth.login'))


@auth.route('/find_password/<email>', methods=['GET', 'POST'])
def find_password(email):
    form = FindPasswordForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()
        user.password = form.new_password.data
        flash('You have set a new password. Better not forget again!')
        return redirect(url_for('main.index'))
    return render_template('auth/find_password.html', form=form)


@auth.route('/change_email', methods=['GET', 'POST'])
@login_required
def change_email():
    form = EmailConfirmationForm()
    if form.validate_on_submit():
        user = current_user
        token = user.generate_confirmation_token()
        user.temp_email = form.email.data
        send_email(form.email.data, 'Confirmation', 'auth/email/change_email', user=user, token=token)
        flash('A confirmation email has been sent to your new email address. Check it out!')
        return redirect(url_for('main.index'))
    return render_template('auth/wait_for_confirmation.html', form=form)


@auth.route('/change_email_confirm/<username>/<token>')
def change_email_confirm(username, token):
    user = User.query.filter_by(username=username).first()
    if user.confirm(token):
        flash('You have confirmed your account. Now you can use the new email address.')
        user.email = user.temp_email
        user.temp_email = ''
        user.avatar_hash = hashlib.md5(user.email.encode('utf-8')).hexdigest()
        return redirect('main.index')
    else:
        flash('Confirmation failed.')
        return redirect('main.index')
