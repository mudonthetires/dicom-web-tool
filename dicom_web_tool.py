import os
import pydicom
import uuid
from flask import Flask, request, render_template, send_file
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "output"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def generate_new_uid():
    return pydicom.uid.generate_uid()

def anonymize_dicom(input_path, output_path):
    """Anonymizes a DICOM file and saves it to output_path."""
    try:
        dicom_data = pydicom.dcmread(input_path)

        # Remove patient-specific information
        dicom_data.PatientName = "Anonymized"
        dicom_data.PatientID = "Anonymized"
        dicom_data.PatientBirthDate = "00000000"
        dicom_data.PatientSex = "O"

        # Generate new UIDs to prevent linking to the original patient
        dicom_data.StudyInstanceUID = generate_new_uid()
        dicom_data.SeriesInstanceUID = generate_new_uid()
        dicom_data.SOPInstanceUID = generate_new_uid()
        dicom_data.FrameOfReferenceUID = generate_new_uid()

        # Remove modifying equipment and institution info
        dicom_data.InstitutionName = "Anonymized"
        dicom_data.InstitutionAddress = "Anonymized"
        dicom_data.ReferringPhysicianName = "Anonymized"
        dicom_data.StationName = "Anonymized"
        dicom_data.OperatorsName = "Anonymized"
        dicom_data.Manufacturer = "Anonymized"

        dicom_data.save_as(output_path)
        return True, output_path
    except Exception as e:
        return False, str(e)

@app.route("/", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        if "file" not in request.files:
            return "No file part"

        file = request.files["file"]
        if file.filename == "":
            return "No selected file"

        filename = secure_filename(file.filename)
        input_path = os.path.join(UPLOAD_FOLDER, filename)
        output_path = os.path.join(OUTPUT_FOLDER, filename)
        file.save(input_path)

        success, result = anonymize_dicom(input_path, output_path)
        if success:
            return send_file(output_path, as_attachment=True)
        else:
            return f"Error: {result}"

    return """
    <!doctype html>
    <title>Upload DICOM File</title>
    <h1>Upload a DICOM File for Anonymization</h1>
    <form method=post enctype=multipart/form-data>
      <input type=file name=file>
      <input type=submit value=Upload>
    </form>
    """

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
