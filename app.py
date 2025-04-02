from flask import Flask, request, render_template, jsonify, session, redirect, url_for, send_from_directory
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import shutil
from PIL import Image, ImageDraw
import io

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # Required for sessions

# Path to our local storage file
USERS_FILE = 'users.json'
POSTS_FILE = 'posts.json'

# Create necessary directories
if not os.path.exists('static'):
    os.makedirs('static', mode=0o755)
if not os.path.exists('static/uploads'):
    os.makedirs('static/uploads', mode=0o755)

# Create a simple default profile picture if it doesn't exist
default_pic_path = 'static/uploads/default.jpg'
if not os.path.exists(default_pic_path):
    img = Image.new('RGB', (100, 100), color='#4A90E2')
    d = ImageDraw.Draw(img)
    
    d.ellipse([25, 25, 75, 75], fill='white')
    d.ellipse([45, 35, 55, 45], fill='#4A90E2')
    d.arc([35, 45, 65, 65], 0, 180, fill='#4A90E2', width=2)
    
    img.save(default_pic_path, 'JPEG')
    # Set file permissions
    os.chmod(default_pic_path, 0o644)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=4)

def load_posts():
    if os.path.exists(POSTS_FILE):
        with open(POSTS_FILE, 'r') as f:
            return json.load(f)
    return []

def save_posts(posts):
    with open(POSTS_FILE, 'w') as f:
        json.dump(posts, f, indent=4)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    
    data = request.form
    users = load_users()
    
    if any(user['email'] == data['email'] for user in users):
        return jsonify({'error': 'Email already registered'}), 400
    
    new_user = {
        'id': str(len(users) + 1),
        'fullname': data['fullname'],
        'email': data['email'],
        'password': generate_password_hash(data['password']),
        'college': data['college'],
        'age': None,
        'bio': '',
        'profile_picture': 'default.jpg'  # Ensure this is set
    }
    
    users.append(new_user)
    save_users(users)
    
    return jsonify({'message': 'Account created successfully'}), 200

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    
    data = request.form
    users = load_users()
    
    user = next((user for user in users if user['email'] == data['email']), None)
    
    if not user or not check_password_hash(user['password'], data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    # Ensure user has profile_picture
    if 'profile_picture' not in user:
        user['profile_picture'] = 'default.jpg'
        save_users(users)
    
    session['user'] = {
        'id': user['id'],
        'fullname': user['fullname'],
        'email': user['email'],
        'college': user['college'],
        'profile_picture': user['profile_picture']
    }
    
    return jsonify({'message': 'Logged in successfully'}), 200

@app.route('/posts', methods=['GET', 'POST'])
def posts():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    if request.method == 'GET':
        posts = load_posts()
        users = load_users()
        
        # Update each post with current user info
        for post in posts:
            user = next((u for u in users if u['email'] == post['author']['email']), None)
            if user:
                post['author'].update({
                    'name': user['fullname'],
                    'profile_picture': user['profile_picture']
                })
            
            # Update comments with current user info
            for comment in post.get('comments', []):
                comment_user = next((u for u in users if u['email'] == comment['author']['email']), None)
                if comment_user:
                    comment['author'].update({
                        'name': comment_user['fullname'],
                        'profile_picture': comment_user['profile_picture']
                    })
        
        # Sort posts by timestamp, newest first
        posts.sort(key=lambda x: x['timestamp'], reverse=True)
        return jsonify(posts)
    
    if request.method == 'POST':
        data = request.form
        image_file = request.files.get('image')
        image_filename = None
        
        if image_file and allowed_file(image_file.filename):
            try:
                # Generate filename with timestamp
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"post_{session['user']['email'].split('@')[0]}_{timestamp}.jpg"  # Always save as jpg
                filepath = os.path.join('static', 'uploads', filename)
                
                # Resize image
                resized_image = resize_image(image_file)
                
                # Save the resized image
                with open(filepath, 'wb') as f:
                    f.write(resized_image.getvalue())
                
                os.chmod(filepath, 0o644)
                image_filename = filename
                
            except Exception as e:
                print(f"Error processing image: {str(e)}")
                return jsonify({'error': 'Failed to process image'}), 500
        
        new_post = {
            'id': str(len(load_posts()) + 1),
            'content': data['content'],
            'author': {
                'email': session['user']['email']
            },
            'timestamp': datetime.now().isoformat(),
            'likes': 0,
            'liked_by': [],
            'comments': []
        }
        
        if image_filename:
            new_post['image'] = image_filename
        
        posts = load_posts()
        posts.append(new_post)
        save_posts(posts)
        
        # Add current user info for the response
        new_post['author'].update({
            'name': session['user']['fullname'],
            'profile_picture': session['user']['profile_picture']
        })
        
        return jsonify(new_post), 201

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    posts = load_posts()
    users = load_users()
    
    posts.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template('dashboard.html', user=session['user'], posts=posts, users=users)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('home'))

@app.route('/posts/<post_id>/comments', methods=['POST'])
def add_comment(post_id):
    print(f"\nReceived comment request for post {post_id}")
    print("Headers:", dict(request.headers))
    print("Form data:", dict(request.form))
    
    if 'user' not in session:
        print("User not logged in")
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.form
        content = data.get('content')
        print(f"Content received: {content}")
        
        if not content:
            print("No content provided")
            return jsonify({'error': 'Comment content is required'}), 400
        
        posts = load_posts()
        post = next((p for p in posts if p['id'] == post_id), None)
        
        if not post:
            print(f"Post {post_id} not found")
            return jsonify({'error': 'Post not found'}), 404
        
        new_comment = {
            'id': str(len(load_posts()) + 1),
            'content': content,
            'author': {
                'email': session['user']['email']
            },
            'timestamp': datetime.now().isoformat()
        }
        
        print(f"Created new comment: {new_comment}")
        
        if 'comments' not in post:
            post['comments'] = []
        
        post['comments'].append(new_comment)
        save_posts(posts)
        
        # Get current user info for the response
        users = load_users()
        current_user = next((u for u in users if u['email'] == session['user']['email']), None)
        
        # Add user info to the response
        new_comment['author'].update({
            'name': current_user['fullname'],
            'profile_picture': current_user['profile_picture']
        })
        
        print(f"Sending response: {new_comment}")
        return jsonify(new_comment), 201
        
    except Exception as e:
        print(f"Error processing comment: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/posts/<post_id>/like', methods=['POST'])
def toggle_like(post_id):
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    posts = load_posts()
    post = next((p for p in posts if p['id'] == post_id), None)
    
    if not post:
        return jsonify({'error': 'Post not found'}), 404
    
    # Initialize likes and liked_by if they don't exist
    if 'likes' not in post:
        post['likes'] = 0
    if 'liked_by' not in post:
        post['liked_by'] = []
    
    user_email = session['user']['email']
    
    # Toggle like
    if user_email in post['liked_by']:
        post['liked_by'].remove(user_email)
        post['likes'] -= 1
    else:
        post['liked_by'].append(user_email)
        post['likes'] += 1
    
    save_posts(posts)
    
    return jsonify({
        'likes': post['likes'],
        'liked': user_email in post['liked_by']
    }), 200

@app.route('/profile')
def profile():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    users = load_users()
    user = next((u for u in users if u['email'] == session['user']['email']), None)
    
    if not user:
        return redirect(url_for('logout'))
    
    # Ensure user has profile_picture attribute
    if 'profile_picture' not in user:
        user['profile_picture'] = 'default.jpg'
        save_users(users)
    
    return render_template('profile.html', user=user)

@app.route('/profile/update', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return jsonify({'error': 'Not logged in'}), 401
    
    try:
        data = request.form
        print("Received form data:", dict(data))
        print("Received files:", request.files)
        
        users = load_users()
        user = next((u for u in users if u['email'] == session['user']['email']), None)
        
        if not user:
            return jsonify({'error': 'User not found'}), 404
        
        print("Current user:", user)
        
        # Validate age
        try:
            age = int(data['age'])
            if age < 18:
                return jsonify({'error': 'Must be 18 or older'}), 400
        except ValueError:
            return jsonify({'error': 'Invalid age'}), 400
        
        # Update user info
        user['age'] = age
        user['bio'] = data['bio']
        
        # Handle profile picture upload
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            print("Received file:", file)
            print("File name:", file.filename if file else None)
            print("File content type:", file.content_type if file else None)
            
            if file and file.filename:
                if allowed_file(file.filename):
                    try:
                        # Ensure the uploads directory exists
                        upload_dir = os.path.join('static', 'uploads')
                        os.makedirs(upload_dir, mode=0o755, exist_ok=True)
                        
                        # Generate filename with timestamp instead of ID
                        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                        filename = f"profile_{user['email'].split('@')[0]}_{timestamp}{os.path.splitext(file.filename)[1].lower()}"
                        filepath = os.path.join(upload_dir, filename)
                        
                        print(f"Attempting to save file to: {filepath}")
                        print(f"Directory exists: {os.path.exists(upload_dir)}")
                        print(f"Directory writable: {os.access(upload_dir, os.W_OK)}")
                        
                        # Save the file
                        file.save(filepath)
                        print(f"File saved successfully to {filepath}")
                        
                        # Set file permissions
                        os.chmod(filepath, 0o644)
                        print("File permissions set")
                        
                        # Update user profile picture
                        user['profile_picture'] = filename
                        print(f"User profile picture updated to: {filename}")
                    except Exception as e:
                        print(f"Error saving file: {str(e)}")
                        print(f"Error type: {type(e)}")
                        import traceback
                        print("Full traceback:")
                        traceback.print_exc()
                        raise
                else:
                    return jsonify({'error': 'Invalid file type. Please use jpg, jpeg, png, or gif'}), 400
        
        # After successfully updating the profile picture, update all posts and comments
        if 'profile_picture' in request.files and file and file.filename:
            posts = load_posts()
            user_email = user['email']
            
            # Update profile picture in all posts by this user
            for post in posts:
                if post['author']['email'] == user_email:
                    post['author']['profile_picture'] = user['profile_picture']
                
                # Update profile picture in all comments by this user
                if 'comments' in post:
                    for comment in post['comments']:
                        if comment['author']['email'] == user_email:
                            comment['author']['profile_picture'] = user['profile_picture']
            
            # Save updated posts
            save_posts(posts)
            print("Updated profile picture in all posts and comments")
        
        # Save user changes
        try:
            save_users(users)
            print("Users saved successfully")
        except Exception as e:
            print(f"Error saving users: {str(e)}")
            raise
        
        # Update session with new profile picture
        session['user'] = {
            'id': user['id'],
            'fullname': user['fullname'],
            'email': user['email'],
            'college': user['college'],
            'profile_picture': user['profile_picture']  # Make sure this is updated
        }
        
        return jsonify({
            'message': 'Profile updated successfully',
            'redirect': url_for('dashboard'),
            'profile_picture': user['profile_picture']  # Send back the new profile picture
        }), 200
        
    except Exception as e:
        print(f"Error updating profile: {str(e)}")
        print(f"Error type: {type(e)}")
        import traceback
        print("Full traceback:")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# Add helper function for file upload
def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/static/uploads/<path:filename>')
def serve_upload(filename):
    return send_from_directory('static/uploads', filename)

def clear_users():
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)  # Write an empty list to the file

def clear_all_data():
    # Clear users
    with open(USERS_FILE, 'w') as f:
        json.dump([], f)
    
    # Clear posts
    with open(POSTS_FILE, 'w') as f:
        json.dump([], f)
    
    # Clear uploads directory except default.jpg
    uploads_dir = 'static/uploads'
    for filename in os.listdir(uploads_dir):
        if filename != 'default.jpg':
            file_path = os.path.join(uploads_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f'Error deleting {file_path}: {e}')

def resize_image(image_file, max_size=(600, 600)):
    # Read the image file
    img = Image.open(image_file)
    
    # Convert RGBA to RGB if necessary
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    
    # Calculate new dimensions while maintaining aspect ratio
    ratio = min(max_size[0]/img.width, max_size[1]/img.height)
    new_size = tuple([int(x*ratio) for x in img.size])
    
    # Only resize if the image is larger than max_size
    if img.width > max_size[0] or img.height > max_size[1]:
        img = img.resize(new_size, Image.Resampling.LANCZOS)
    
    # Save to bytes buffer
    buffer = io.BytesIO()
    img.save(buffer, format='JPEG', quality=85)
    buffer.seek(0)
    
    return buffer

if __name__ == '__main__':
    app.run(debug=True) 