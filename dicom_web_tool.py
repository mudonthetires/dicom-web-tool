import os
import pydicom
import uuid
from tkinter import Tk, filedialog

def generate_new_uid():
    return pydicom.uid.generate_uid()

def anonymize_dicom(file_path, output_folder):
    try:
        dicom_data = pydicom.dcmread(file_path)
        
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
        
        # Save anonymized file
        output_path = os.path.join(output_folder, os.path.basename(file_path))
        dicom_data.save_as(output_path)
        print(f"Anonymized: {file_path} -> {output_path}")
    except Exception as e:
        print(f"Error processing {file_path}: {e}")

def batch_anonymize_dicom():
    Tk().withdraw()  # Hide GUI window
    input_folder = filedialog.askdirectory(title="Select Folder Containing DICOM Files")
    output_folder = filedialog.askdirectory(title="Select Output Folder for Anonymized Files")
    
    if not input_folder or not output_folder:
        print("Operation cancelled.")
        return
    
    for filename in os.listdir(input_folder):
        if filename.lower().endswith(".dcm"):
            file_path = os.path.join(input_folder, filename)
            anonymize_dicom(file_path, output_folder)
    
    print("Batch anonymization complete!")

if __name__ == "__main__":
    batch_anonymize_dicom()
