import os
from flask import Flask, request, send_file
import pydicom
from werkzeug.utils import secure_filename

# Create a temporary folder to store uploaded and modified files
temp_folder = "uploads"
os.makedirs(temp_folder, exist_ok=True)

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        if 'file' not in request.files:
            return "No file uploaded"
        file = request.files['file']
        if file.filename == '':
            return "No selected file"
        
        filename = secure_filename(file.filename)
        filepath = os.path.join(temp_folder, filename)
        file.save(filepath)
        
        modified_filepath = modify_dicom_tag(filepath)
        return send_file(modified_filepath, as_attachment=True)
    
    return '''
    <!doctype html>
    <title>Upload DICOM File</title>
    <h1>Upload a DICOM file to modify</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    '''

def modify_dicom_tag(filepath):
    """Modify MLCparam_ELMconfig to OVL_V18_DLG in a DICOM file."""
    dicom_data = pydicom.dcmread(filepath)
    
    if hasattr(dicom_data, "MLCparam_ELMconfig"):
        dicom_data.MLCparam_ELMconfig = "OVL_V18_DLG"
        modified_path = os.path.join(temp_folder, "modified_" + os.path.basename(filepath))
        dicom_data.save_as(modified_path)
        return modified_path
    else:
        return filepath  # Return original if tag not found

if __name__ == '__main__':
    app.run(debug=True)
