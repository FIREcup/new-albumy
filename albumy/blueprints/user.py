from flask import render_template, Blueprint, request, current_app, flash, redirect, url_for
from flask_login import login_required, logout_user
from ..decorators import permission_required, confirm_required
from flask_login import current_user, fresh_login_required, login_required
from ..extensions import db, avatars
from ..utils import redirect_back
from ..notifications import push_follow_notification

from ..models import User, Photo, Collect, Follow
from ..forms.user import UploadAvatarForm, CropAvatarForm, EditProfileForm, ChangeEmailForm, ChangePasswordForm
from ..forms.user import NotificationSettingForm, PrivacySettingForm, DeleteAccountForm
from ..emails import send_confirm_email
from ..utils import generate_token, flash_errors


user_bp = Blueprint('user', __name__)


@user_bp.route('/<username>')
def index(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user == user and user.locked:
        flash('Your account is locked.', 'danger')

    if user == current_user and not user.active:
        logout_user()

    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Photo.query.with_parent(user).order_by(Photo.timestamp.desc()).paginate(page, per_page)
    photos = pagination.items
    return render_template('user/index.html', user=user, photos=photos, pagination=pagination)


@user_bp.route('/<username>/collections')
def show_collections(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_PHOTO_PER_PAGE']
    pagination = Collect.query.with_parent(user).order_by(Collect.timestamp.asc()).paginate(page, per_page)
    collects = pagination.items
    return render_template('user/collections.html', user=user, pagination=pagination, collects=collects)


@user_bp.route('/follow/<username>', methods=['POST'])
@login_required
@permission_required('FOLLOW')
def follow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if current_user.is_following(user):
        flash('Already followed.', 'info')
        return redirect(url_for('.index', username=username))
    current_user.follow(user)
    push_follow_notification(follower=current_user, receiver=user)
    flash('Followed successfully.', 'success')
    return redirect_back()


@user_bp.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    user = User.query.filter_by(username=username).first_or_404()
    if not current_user.is_following(user):
        flash('Not following.', 'info')
        return redirect_back(url_for('.index', username=username))

    current_user.unfollow(user)
    flash('unfollow successfully', 'success')
    return redirect_back()


@user_bp.route('/<username>followers')
@login_required
def show_followers(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.followers.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/followers.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/<username>/following')
@login_required
def show_following(username):
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ALBUMY_USER_PER_PAGE']
    pagination = user.following.paginate(page, per_page)
    follows = pagination.items
    return render_template('user/following.html', user=user, pagination=pagination, follows=follows)


@user_bp.route('/settings/avatar')
@login_required
@confirm_required
def change_avatar():
    upload_form = UploadAvatarForm()
    crop_form = CropAvatarForm()
    return render_template('user/settings/change_avatar.html', upload_form=upload_form, crop_form=crop_form)


@user_bp.route('/settings/avatar/upload', methods=['POST'])
@login_required
@confirm_required
def upload_avatar():
    form = UploadAvatarForm()
    if form.validate_on_submit():
        image = form.image.data
        filename = avatars.save_avatar(image)
        current_user.avatar_raw = filename
        db.session.commit()
        flash('Image uploaded, please crop.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/avatar/crop', methods=['POST'])
@login_required
@confirm_required
def crop_avatar():
    form = CropAvatarForm()
    if form.validate_on_submit():
        x = form.x.data
        y = form.y.data
        w = form.w.data
        h = form.h.data
        filenames = avatars.crop_avatar(current_user.avatar_raw, x, y, w, h)
        current_user.avatar_s = filenames[0]
        current_user.avatar_m = filenames[1]
        current_user.avatar_l = filenames[2]
        db.session.commit()
        flash('Avatar updated.', 'success')
    flash_errors(form)
    return redirect(url_for('.change_avatar'))


@user_bp.route('/settings/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.name = form.name.data
        current_user.username = form.username.data
        current_user.bio = form.bio.data
        current_user.website = form.website.data
        current_user.location = form.location.data
        db.session.commit()
        flash('Profile updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.name.data = current_user.name
    form.username.data = current_user.username
    form.bio.data = current_user.bio
    form.website.data = current_user.website
    form.location.data = current_user.location
    return render_template('user/settings/edit_profile.html', form=form)


@user_bp.route('/settings/change-password', methods=['POST', 'GET'])
@fresh_login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit() and current_user.validate_password(form.old_password.data):
        current_user.set_password(form.password.data)
        db.session.commit()
        flash('Password updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_password.html', form=form)


@user_bp.route('/settings/change-email', methods=['GET', 'POST'])
@fresh_login_required
def change_email_request():
    form = ChangeEmailForm()
    if form.validate_on_submit():
        token = generate_token(user=current_user, operation=Operation.CHANGE_EMAIL, new_email=form.email.data.lower())
        send_confirm_email(to=form.email.data, user=current_user, token=token)
        flash('Confirm email sent, check your inbox', 'info')
        return redirect(url_for('.index', username=current_user.username))
    return render_template('user/settings/change_email.html', form=form)


@user_bp.route('/settings/notification', methods=['GET', 'POST'])
@login_required
def notification_setting():
    form = NotificationSettingForm()
    if form.validate_on_submit():
        current_user.receive_collect_notification = form.receive_collect_notification.data
        current_user.receive_comment_notification = form.receive_comment_notification.data
        current_user.receive_follow_notification = form.receive_follow_notification.data
        db.session.commit()
        flash('Notification settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.receive_collect_notification = current_user.receive_collect_notification
    form.receive_comment_notification = current_user.receive_comment_notification
    form.receive_follow_notification = current_user.receive_follow_notification
    return render_template('user/settings/edit_notification.html', form=form)


@user_bp.route('/settings/privacy', methods=['GET', 'POST'])
@login_required
def privacy_setting():
    form = PrivacySettingForm()
    if form.validate_on_submit():
        current_user.public_collections = form.public_collections.data
        db.session.commit()
        flash('Privacy settings updated.', 'success')
        return redirect(url_for('.index', username=current_user.username))
    form.public_collections.data = current_user.public_collections
    return render_template('user/settings/edit_privacy.html', form=form)


@user_bp.route('/settings/delete/account', methods=['GET', 'POST'])
@fresh_login_required
def delete_account():
    form = DeleteAccountForm()
    if form.validate_on_submit():
        db.session.delete(current_user._get_current_object())
        db.session.commit()
        flash('You are free, goodbye!', 'success')
        return redirect(url_for('main.index'))
    return render_template('user/settings/delete_account.html', form=form)
