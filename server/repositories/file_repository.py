import os
import hashlib
import datetime

class FileRepository:
    @staticmethod
    def file_hash(fobj):
        hash_obj = hashlib.sha256()
        fobj.seek(0)
        while True:
            chunk = fobj.read(8192)
            if not chunk:
                break
            hash_obj.update(chunk)
        fobj.seek(0)
        return hash_obj.hexdigest()

    @staticmethod
    def find_mp3_for_pdf(pdf_filename, app_ctx):
        mp3_folder = os.path.join(app_ctx.config['UPLOAD_FOLDER'], 'mp3')
        os.makedirs(mp3_folder, exist_ok=True)
        base_name = os.path.splitext(pdf_filename)[0]
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        mp3_candidates = [
            os.path.join(mp3_folder, f"{today}-{base_name}.mp3"),
            os.path.join(mp3_folder, f"{base_name}.mp3")
        ]
        for candidate in mp3_candidates:
            if os.path.exists(candidate):
                return candidate
        return None