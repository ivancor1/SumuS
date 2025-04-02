document.addEventListener('DOMContentLoaded', function() {
    const createPostForm = document.querySelector('.create-post form');
    const imageInput = document.getElementById('post-image');
    const imagePreview = document.querySelector('.image-preview');
    const previewImg = imagePreview.querySelector('img');
    const feedContainer = document.querySelector('.feed');
    
    // Handle image selection
    imageInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                imagePreview.style.display = 'block';
            }
            reader.readAsDataURL(file);
        }
    });
    
    // Handle image removal
    document.querySelector('.remove-image').addEventListener('click', function() {
        imageInput.value = '';
        imagePreview.style.display = 'none';
        previewImg.src = '';
    });
    
    // Handle post submission with image
    createPostForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const textarea = createPostForm.querySelector('textarea');
        const content = textarea.value.trim();
        const imageFile = imageInput.files[0];
        
        if (!content && !imageFile) return;
        
        try {
            const formData = new FormData();
            formData.append('content', content);
            if (imageFile) {
                formData.append('image', imageFile);
            }
            
            const response = await fetch('/posts', {
                method: 'POST',
                body: formData
            });
            
            if (!response.ok) throw new Error('Failed to create post');
            
            const post = await response.json();
            const feed = document.querySelector('.feed');
            
            // Get current user info
            const currentUser = {
                fullname: document.querySelector('.user-name').textContent,
                profile_picture: document.querySelector('.user-menu img')?.src.split('/uploads/')[1] || 'default.jpg'
            };
            
            // Insert the new post at the top of the feed
            feed.insertBefore(createPostElement(post, currentUser), feed.firstChild);
            
            // Clear the form
            textarea.value = '';
            imageInput.value = '';
            imagePreview.style.display = 'none';
            previewImg.src = '';
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to create post. Please try again.');
        }
    });
    
    function formatDate(isoString) {
        const date = new Date(isoString);
        const now = new Date();
        const diffInMinutes = Math.floor((now - date) / 60000);
        
        if (diffInMinutes < 1) return 'Just now';
        if (diffInMinutes < 60) return `${diffInMinutes}m ago`;
        if (diffInMinutes < 1440) return `${Math.floor(diffInMinutes/60)}h ago`;
        return date.toLocaleDateString();
    }
    
    function createPostElement(post, currentUser) {
        const postElement = document.createElement('div');
        postElement.className = 'post';
        postElement.dataset.postId = post.id;
        
        let imageHtml = '';
        if (post.image) {
            imageHtml = `
                <div class="post-image">
                    <img src="/static/uploads/${post.image}" alt="Post image">
                </div>
            `;
        }
        
        postElement.innerHTML = `
            <div class="post-header">
                <img src="/static/uploads/${currentUser.profile_picture}" 
                     alt="User" 
                     class="user-avatar"
                     onerror="this.src='/static/uploads/default.jpg'">
                <div class="post-info">
                    <h4>${currentUser.fullname}</h4>
                    <span>${formatDate(post.timestamp)}</span>
                </div>
            </div>
            <div class="post-content">
                <p>${post.content}</p>
                ${imageHtml}
            </div>
            <div class="post-actions">
                <button class="like-btn" data-likes="${post.likes}">
                    <i class="fas fa-thumbs-up"></i> Like <span class="like-count">${post.likes}</span>
                </button>
                <button class="comment-btn">
                    <i class="fas fa-comment"></i> Comment
                    ${post.comments && post.comments.length > 0 ? `<span class="comment-count">(${post.comments.length})</span>` : ''}
                </button>
                <button><i class="fas fa-share"></i> Share</button>
            </div>
            <div class="comments-section" style="display: none;">
                <form class="comment-form">
                    <input type="text" placeholder="Write a comment..." required>
                    <button type="submit"><i class="fas fa-paper-plane"></i></button>
                </form>
                <div class="comments-container"></div>
            </div>
        `;
        
        return postElement;
    }

    // Handle comment button clicks
    document.addEventListener('click', function(e) {
        if (e.target.closest('.comment-btn')) {
            const post = e.target.closest('.post');
            const commentsSection = post.querySelector('.comments-section');
            commentsSection.style.display = commentsSection.style.display === 'none' ? 'block' : 'none';
        }
    });

    // Handle comment submissions
    document.addEventListener('submit', async function(e) {
        if (!e.target.matches('.comment-form')) return;
        e.preventDefault();
        
        const form = e.target;
        const post = form.closest('.post');
        const postId = post.dataset.postId;
        const input = form.querySelector('input');
        const content = input.value.trim();
        
        if (!content) return;
        
        try {
            const response = await fetch(`/posts/${postId}/comments`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                },
                body: `content=${encodeURIComponent(content)}`
            });

            const data = await response.json();
            
            if (!response.ok) {
                throw new Error(data.error || 'Failed to add comment');
            }
            
            const commentsContainer = post.querySelector('.comments-container');
            
            // Create and add the new comment
            const commentElement = document.createElement('div');
            commentElement.className = 'comment';
            commentElement.innerHTML = `
                <div class="comment-header">
                    <img src="${window.location.origin}/static/uploads/${data.author.profile_picture}" 
                         alt="User" 
                         class="user-avatar"
                         onerror="this.src='${window.location.origin}/static/uploads/default.jpg'">
                    <div class="comment-info">
                        <h5>${data.author.name}</h5>
                        <span>Just now</span>
                    </div>
                </div>
                <div class="comment-content">
                    <p>${data.content}</p>
                </div>
            `;
            
            // Add the comment to the beginning of the comments container
            if (commentsContainer.firstChild) {
                commentsContainer.insertBefore(commentElement, commentsContainer.firstChild);
            } else {
                commentsContainer.appendChild(commentElement);
            }

            // Clear the input
            input.value = '';
            
            // Make sure the comments section is visible
            const commentsSection = post.querySelector('.comments-section');
            commentsSection.style.display = 'block';
            
        } catch (error) {
            console.error('Error details:', error);
            console.error('Error stack:', error.stack);
            alert('Failed to add comment. Please try again.');
        }
    });

    // Add this to your existing JavaScript
    document.addEventListener('click', async function(e) {
        if (!e.target.closest('.like-btn')) return;
        
        const likeBtn = e.target.closest('.like-btn');
        const post = likeBtn.closest('.post');
        const postId = post.dataset.postId;
        
        try {
            const response = await fetch(`/posts/${postId}/like`, {
                method: 'POST'
            });
            
            if (!response.ok) throw new Error('Failed to like post');
            
            const data = await response.json();
            
            // Update like count and button state
            const likeCount = likeBtn.querySelector('.like-count');
            likeCount.textContent = data.likes;
            
            if (data.liked) {
                likeBtn.classList.add('liked');
            } else {
                likeBtn.classList.remove('liked');
            }
            
        } catch (error) {
            console.error('Error:', error);
            alert('Failed to like post. Please try again.');
        }
    });
}); 