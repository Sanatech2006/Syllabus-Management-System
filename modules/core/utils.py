import os
import json
import time
from django.conf import settings

def clean_old_progress_files():
    try:
        progress_dir = os.path.join(settings.MEDIA_ROOT, 'upload_progress')
        if not os.path.exists(progress_dir):
            return
        now = time.time()
        for filename in os.listdir(progress_dir):
            filepath = os.path.join(progress_dir, filename)
            if os.path.isfile(filepath):
                # Delete files older than 30 minutes (1800 seconds)
                if os.path.getmtime(filepath) < now - 1800:
                    try:
                        os.remove(filepath)
                    except OSError:
                        pass
    except Exception:
        pass

def get_progress_dir():
    progress_dir = os.path.join(settings.MEDIA_ROOT, 'upload_progress')
    os.makedirs(progress_dir, exist_ok=True)
    return progress_dir

def get_progress_file_path(upload_id):
    safe_id = "".join([c for c in str(upload_id) if c.isalnum() or c in ('-', '_')])
    return os.path.join(get_progress_dir(), f"{safe_id}.json")

def set_upload_progress(upload_id, current, total, status="processing"):
    if not upload_id:
        return
    clean_old_progress_files()
    path = get_progress_file_path(upload_id)
    data = {
        'current': current,
        'total': total,
        'status': status
    }
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

def get_upload_progress(upload_id):
    if not upload_id:
        return None
    path = get_progress_file_path(upload_id)
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'status': 'processing', 'current': 0, 'total': 0, 'error': 'locked'}

def delete_upload_progress(upload_id):
    if not upload_id:
        return
    path = get_progress_file_path(upload_id)
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass