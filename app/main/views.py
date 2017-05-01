# coding=utf-8
import base64
import os

from flask import current_app, jsonify
from flask import redirect, flash
from flask import render_template
from flask import request
from flask import url_for
from flask_login import login_required, current_user

from app import db
from app.main.forms import EditProfileForm
from app.models.models import User, Follow, TopicCategory
from . import main
from app.helpers import constant


@main.route("/")
@login_required
def index():
    return render_template("zheye.html", user=current_user, base64=base64)


@main.route('/people/<username>')
def people(username):
    """个人资料界面"""
    user = User.query.filter_by(username=username).first_or_404()
    return render_template('user.html', user=user, base64=base64)


@main.route('/edit-profile', methods=['POST', 'GET'])
@login_required
def edit_profile():
    """编辑个人资料"""
    form = EditProfileForm()
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.location = form.location.data
        current_user.sex = form.sex.data
        current_user.short_intr = form.short_intr.data
        current_user.school = form.school.data
        current_user.industry = form.industry.data
        current_user.discipline = form.discipline.data
        current_user.introduction = form.introduction.data
        db.session.add(current_user)
        db.session.commit()

        flash(constant.PROFILE_UPDATE)
        return redirect(url_for('main.people', username=current_user.username))

    form.username.data = current_user.username
    form.sex.data = current_user.sex or "man"
    form.short_intr.data = current_user.short_intr
    form.industry.data = current_user.industry
    form.school.data = current_user.school
    form.discipline.data = current_user.discipline
    form.introduction.data = current_user.introduction
    form.location.data = current_user.location

    return render_template('edit_profile.html', form=form, user=current_user, base64=base64)


@main.route('/follow/<username>')
@login_required
def follow(username):
    """关注某人"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(constant.INVALID_USER)
        return redirect(url_for('main.index'))

    if user == current_user:
        flash(constant.CANNOT_CON_MYSELF)
        return redirect(url_for('main.index'))
    if current_user.is_following(user):
        return redirect(url_for('main.people', username=username))
    current_user.follow(user)
    return redirect(url_for('main.people', username=username))


@main.route('/unfollow/<username>')
@login_required
def unfollow(username):
    """取消关注"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(constant.INVALID_USER)
        return redirect(url_for('main.index'))
    if not current_user.is_following(user):
        return redirect(url_for('main.people', username=username))
    current_user.unfollow(user)
    return redirect(url_for('main.people', username=username))


@main.route('/people/<username>/followers')
def followers(username):
    """显示username的关注者"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(constant.INVALID_USER)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followers.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.follower}
               for item in pagination.items]
    return render_template('user_followers.html', user=user,
                           endpoint='.followers', pagination=pagination,
                           follows=follows,base64=base64)


@main.route('/people/<username>/following')
def following(username):
    """分页显示username关注了谁"""
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(constant.INVALID_USER)
        return redirect(url_for('.index'))
    page = request.args.get('page', 1, type=int)
    pagination = user.followed.paginate(
        page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE'],
        error_out=False)
    follows = [{'user': item.followed}
               for item in pagination.items]
    return render_template('user_followers.html', user=user,
                           endpoint='.following', pagination=pagination,
                           follows=follows, base64=base64)


@main.route('/people/images', methods=['POST'])
@login_required
def images():
    try:
        # 读取图片内容
        file = request.files['file'].read()
        if current_user.change_avatar(file):
            return redirect(url_for("main.people", username=current_user.username))
    except:
        pass
    # 头像修改失败，提示
    flash(constant.AVATAR_MODI_FAIL)
    return redirect(url_for("main.index"))


@main.route('/topics')
def topics():
    """话题广场"""
    topic_cate = TopicCategory.query.all()
    return render_template("topics.html", base64=base64, user=current_user,
                           topic_cate=topic_cate, topics=topic_cate[0].topics)


@main.route('/topics_search', methods=['POST'])
def topics_search():
    """查询选中话题类型下的所有话题"""
    cate = request.form.get("topic_cate", None)
    topic_cate = TopicCategory.query.filter_by(
        category_name=cate).first()
    if topic_cate:
        return jsonify(topics=[[topic.topic_name, topic.topic_desc if topic.topic_desc else ""]
                               for topic in topic_cate.topics])

    return "error"
