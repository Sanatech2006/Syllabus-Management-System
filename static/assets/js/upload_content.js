document.addEventListener('DOMContentLoaded', function() {
    const actionBtns = document.querySelectorAll('.action-btn');
    
    actionBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const courseCode = this.getAttribute('data-course-code');
            openUploadDialog(courseCode);
        });
    });
    
    function openUploadDialog(courseCode) {
        const input = document.createElement('input');
        input.type = 'file';
        input.accept = '.txt,.pdf,.doc,.docx';
        input.onchange = function(e) {
            const file = e.target.files[0];
            if (file) {
                readFile(file, courseCode);
            }
        };
        input.click();
    }
    
    function readFile(file, courseCode) {
        const reader = new FileReader();
        reader.onload = function(e) {
            uploadContent(courseCode, e.target.result);
        };
        reader.readAsText(file);
    }
    
    function uploadContent(courseCode, content) {
        fetch('/upload-content/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            },
            body: JSON.stringify({
                course_code: courseCode,
                file_content: content
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`✅ Content uploaded for ${data.course_code}`);
            } else {
                alert(`❌ Error: ${data.error}`);
            }
        })
        .catch(error => {
            alert('❌ Upload failed');
            console.error('Error:', error);
        });
    }
    
    function getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }
});
