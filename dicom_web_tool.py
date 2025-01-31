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

# Generate shared anonymized patient information
def generate_anonymized_patient_info():
    return {
        "PatientName": "Anonymized",
        "PatientID": str(uuid.uuid4()),
        "PatientBirthDate": "00000000",
        "PatientSex": "O",
        "StudyInstanceUID": pydicom.uid.generate_uid(),
        "SeriesInstanceUID": pydicom.uid.generate_uid(),
        "FrameOfReferenceUID": pydicom.uid.generate_uid(),
    }

def anonymize_dicom(input_path, output_path, patient_info):
    """Anonymizes a DICOM file and ensures all files in a batch stay together."""
    try:
        dicom_data = pydicom.dcmread(input_path)

        # Apply shared patient info
        dicom_data.PatientName = patient_info["PatientName"]
        dicom_data.PatientID = patient_info["PatientID"]
        dicom_data.PatientBirthDate = patient_info["PatientBirthDate"]
        dicom_data.PatientSex = patient_info["PatientSex"]
        dicom_data.StudyInstanceUID = patient_info["StudyInstanceUID"]
        dicom_data.SeriesInstanceUID = patient_info["SeriesInstanceUID"]
        dicom_data.FrameOfReferenceUID = patient_info["FrameOfReferenceUID"]

        # Generate a new SOPInstanceUID for each file
        dicom_data.SOPInstanceUID = pydicom.uid.generate_uid()

        # Remove identifying metadata
        dicom_data.remove_private_tags()
        dicom_data.InstitutionName = "Anonymized"
        dicom_data.ReferringPhysicianName = "Anonymized"
        dicom_data.OperatorsName = "Anonymized"
        dicom_data.Manufacturer = "Anonymized"

        # Remove burned-in annotations
        if "BurnedInAnnotation" in dicom_data:
            dicom_data.BurnedInAnnotation = "NO"

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

        # Generate a shared set of anonymized patient details
        patient_info = generate_anonymized_patient_info()
        
        with zipfile.ZipFile(zip_filepath, 'w') as zipf:
            for file in files:
                filename = secure_filename(file.filename)
                input_path = os.path.join(UPLOAD_FOLDER, filename)
                output_path = os.path.join(OUTPUT_FOLDER, filename)
                file.save(input_path)

                success, result = anonymize_dicom(input_path, output_path, patient_info)
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
