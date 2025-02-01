import os
import pydicom
import uuid
import zipfile
from flask import Flask, request, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# List of tags to anonymize based on user-provided file
ANONYMIZED_TAGS = [
    (0x0008, 0x0012), (0x0008, 0x0013), (0x0008, 0x0014), (0x0008, 0x0015), (0x0008, 0x0017),
    (0x0008, 0x0018), (0x0008, 0x0019), (0x0008, 0x0020), (0x0008, 0x0021), (0x0008, 0x0022),
    (0x0008, 0x0023), (0x0008, 0x0024), (0x0008, 0x0025), (0x0008, 0x002A), (0x0008, 0x0030),
    (0x0008, 0x0031), (0x0008, 0x0032), (0x0008, 0x0033), (0x0008, 0x0034), (0x0008, 0x0035),
    (0x0008, 0x0050), (0x0008, 0x0080), (0x0008, 0x0090), (0x0010, 0x0010), (0x0010, 0x0020),
    (0x0010, 0x0030), (0x0010, 0x0040), (0x0020, 0x000D), (0x0020, 0x000E), (0x0020, 0x0010)
]

# Generate a consistent anonymized identity for a batch
def generate_anonymized_identity():
    return {
        "PatientName": "Anonymized",
        "PatientID": str(uuid.uuid4()),
        "StudyInstanceUID": pydicom.uid.generate_uid(),
        "SeriesInstanceUID": pydicom.uid.generate_uid(),
    }

def anonymize_dicom(input_path, output_path, identity):
    """Anonymizes specific fields in a DICOM file while keeping batch consistency."""
    try:
        dicom_data = pydicom.dcmread(input_path)
        
        for tag in ANONYMIZED_TAGS:
            if tag in dicom_data:
                if "UID" in dicom_data[tag].name:
                    dicom_data[tag].value = identity["StudyInstanceUID"] if tag == (0x0020, 0x000D) else identity["SeriesInstanceUID"]
                else:
                    dicom_data[tag].value = identity["PatientName"] if tag == (0x0010, 0x0010) else identity["PatientID"]
        
        dicom_data.save_as(output_path)
        return True, output_path
    except Exception as e:
        return False, str(e)

@app.route("/", methods=["GET", "POST"])
def upload_files():
    if request.method == "POST":
        if "files" not in request.files:
            return "No file part"
        
        files = request.files.getlist("files")
        if not files or files[0].filename == "":
            return "No selected files"
        
        zip_filename = "anonymized_dicoms.zip"
        zip_filepath = os.path.join(OUTPUT_FOLDER, zip_filename)
        
        # Generate a single anonymized identity for the entire batch
        identity = generate_anonymized_identity()
        
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for file in files:
                filename = secure_filename(file.filename)
                input_path = os.path.join(UPLOAD_FOLDER, filename)
                output_path = os.path.join(OUTPUT_FOLDER, filename)
                file.save(input_path)
                
                success, result = anonymize_dicom(input_path, output_path, identity)
                if success:
                    zipf.write(output_path, filename)
                else:
                    return f"Error processing {filename}: {result}"
        
        return send_file(zip_filepath, as_attachment=True)
    
    return """
    <!doctype html>
    <title>Upload DICOM Files</title>
    <h1>Upload Multiple DICOM Files for Anonymization</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=files multiple>
      <input type=submit value=Upload>
    </form>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
