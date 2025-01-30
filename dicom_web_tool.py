import os
import zipfile
from flask import Flask, request, send_file
import pydicom
from werkzeug.utils import secure_filename

# Create temporary folders for uploads and modified files
upload_folder = "uploads"
modified_folder = "modified_files"
os.makedirs(upload_folder, exist_ok=True)
os.makedirs(modified_folder, exist_ok=True)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_files():
    if request.method == 'POST':
        if 'files' not in request.files:
            return "No files uploaded"
        files = request.files.getlist('files')
        if not files:
            return "No selected files"
        
        modified_file_paths = []
        for file in files:
            filename = secure_filename(file.filename)
            filepath = os.path.join(upload_folder, filename)
            file.save(filepath)
            
            modified_filepath = modify_dicom_tag(filepath)
            modified_file_paths.append(modified_filepath)
        
        # Create a ZIP file with modified files
        zip_filename = "modified_dicoms.zip"
        zip_filepath = os.path.join(modified_folder, zip_filename)
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for file_path in modified_file_paths:
                zipf.write(file_path, os.path.basename(file_path))
        
        return send_file(zip_filepath, as_attachment=True)
    
    return '''
    <!doctype html>
    <title>Upload DICOM Files</title>
    <h1>Upload a Folder of DICOM Files to Modify</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=files multiple>
      <input type=submit value=Upload>
    </form>
    '''

def modify_dicom_tag(filepath):
    """Modify MLCparam_ELMconfig to OVL_V18_DLG in a DICOM file."""
    dicom_data = pydicom.dcmread(filepath)
    
    if hasattr(dicom_data, "MLCparam_ELMconfig"):
        dicom_data.MLCparam_ELMconfig = "OVL_V18_DLG"
        modified_path = os.path.join(modified_folder, os.path.basename(filepath))
        dicom_data.save_as(modified_path)
        return modified_path
    else:
        return filepath  # Return original if tag not found

if __name__ == '__main__':
    app.run(debug=True)
