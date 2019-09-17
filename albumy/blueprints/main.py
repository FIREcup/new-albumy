import os
from flask import render_template, Blueprint, request, current_app
from flask_login import current_user, login_required
from flask_dropzone import random_filename

from ..decorators import permission_required, confirm_required
from ..extensions import db
from ..models import Photo


main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    return render_template('main/index.html')


@main_bp.route('/explore')
def explore():
    return render_template('main/explore.html')


@main_bp.route('/upload', methods=['GET', 'POST'])
@login_required
@confirm_required
@permission_required('UPLOAD')
def upload():
    print("current_user's role: {}".format(current_user.role))
    if request.method == 'POST' and 'file' in request.files:
        f = request.files.get('file')
        filename = random_filename(f.filename)
        f.save(os.path.join(current_app.config['ALBUMY_UPLOAD_PATH'], filename))

        photo = Photo(
            filename=filename,
            author=current_user._get_current_object()
        )

        db.session.add(photo)
        db.session.commit()
    return render_template('main/upload.html')