from flask import Blueprint, render_template, flash, request, redirect, url_for, jsonify
from flask_login import login_required, current_user
from .models import Post, User, Comment, Like
from . import db
from sqlalchemy import desc
from werkzeug.utils import secure_filename
import os



views = Blueprint("views", __name__)

@views.route("/")
@views.route("/home")
@login_required
def home():
    posts = Post.query.order_by(desc(Post.date_created)).all()
    return render_template("home.html", user=current_user, posts=posts)

@views.route("/create-post", methods=['GET', 'POST'])
@login_required
def create_post():
    title = request.form.get('title')
    text = request.form.get('text')
    photo = request.files.get('photo')

    if not title or not text:
        flash('Title and text are required', category='error')
    elif not photo or not photo.filename:
        flash('Image is required', category='error')
    else:
        filename = secure_filename(photo.filename)
        photo_path = os.path.join("website/static/uploads/photos", filename)
        
        post = Post(title=title, text=text, author=current_user.id, image=filename)
        db.session.add(post)
        db.session.commit()

        photo.save(photo_path)

        flash('Post created!', category='success')
        return redirect(url_for('views.home'))

    return render_template('create_post.html', user=current_user)

@views.route("/delete-post/<id>")
@login_required
def delete_post(id):
    post = Post.query.filter_by(id=id).first()

    if not post:
        flash("Post does not exist.", category='error')
    elif current_user.id != post.id:
        flash('You do not have permission to delete this post.', category='error')
    else:
        db.session.delete(post)
        db.session.commit()
        flash('Post deleted.', category='success')
    
    return redirect(url_for('views.home'))

@views.route("/posts/<username>")
@login_required
def posts(username):
    user = User.query.filter_by(username=username).first()

    if not user:
        flash('No user with that username exists.', category='error')
        return redirect(url_for('views.home'))

    posts = user.posts
    return render_template("posts.html", user=current_user, posts=posts, username=username)

@views.route("/create-comment/<post_id>", methods=['POST'])
@login_required
def create_comment(post_id):
    text = request.form.get('text')

    if not text:
        flash('Comment cannot be empty', category='error')
    else:
        post = Post.query.filter_by(id = post_id)
        if post:
            comment = Comment(text=text, author=current_user.id, post_id=post_id)
            db.session.add(comment)
            db.session.commit()
        else:
            flash('Post does not exist.', category='error')

    return redirect(url_for('views.home'))

@views.route("/delete-comment/<comment_id>")
@login_required
def delete_comment(comment_id):
    comment = Comment.query.filter_by(id=comment_id).first()

    if not comment:
        flash('Comment does not exist', category='error')
    elif current_user.id != comment.author and current_user.id != comment.post.author:
        flash('Unauthorized delete permission', category='error')
    else:
        db.session.delete(comment)
        db.session.commit()

    return redirect(url_for('views.home'))

@views.route("/like-post/<post_id>", methods=['GET'])
@login_required
def like(post_id):
    post = Post.query.filter_by(id=post_id)
    like = Like.query.filter_by(author=current_user.id, post_id=post_id).first()

    if not post:
        flash('Post does not exist.', category='error')
    elif like:
        db.session.delete(like)
        db.session.commit()
    else:
        like = Like(author=current_user.id, post_id=post_id)
        db.session.add(like)
        db.session.commit()

    return redirect(url_for('views.home'))

@views.route("/search", methods=['GET'])
@login_required
def search():
    query = request.args.get('query')

    if not query:
        flash('Please enter a search query.', category='error')
        return redirect(url_for('views.home'))

    
    search_results = Post.query.filter((Post.title.like(f"%{query}%"))).all()

    return render_template('search.html', user=current_user, query=query, search_results=search_results)

@views.route("/single_post/<post_id>")
@login_required
def single_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        flash('Post not found.', category='error')
        return redirect(url_for('views.home'))

    return render_template('single_post.html', user=current_user, post=post)

@views.route("/edit-post/<post_id>", methods=['GET', 'POST'])
@login_required
def edit_post(post_id):
    post = Post.query.get(post_id)

    if not post:
        flash("Post not found.", category='error')
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        title = request.form.get('title')
        text = request.form.get('text')
        photo = request.files.get('photo')

        if not title or not text:
            flash('Title and text are required', category='error')
        else:
            if photo:
                filename = secure_filename(photo.filename)
                photo_path = os.path.join("website/static/uploads/photos", filename)
                photo.save(photo_path)
                post.image = filename

            post.title = title
            post.text = text
            db.session.commit()

            flash('Post updated!', category='success')
            return redirect(url_for('views.home'))

    return render_template('edit_post.html', user=current_user, post=post)