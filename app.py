from flask import Flask, render_template, request, send_file
from img2table.document import Image
from img2table.ocr import PaddleOCR
import cv2
import numpy as np
import io
import pandas as pd  # Importing pandas for Excel manipulation

# Initialize the Flask application
app = Flask(__name__)
paddle_ocr = PaddleOCR(lang="en", kw={"use_dilation": True})

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/process_image', methods=['POST'])
def process_image():
    cropped_image = request.files['cropped_image']
    # Convert the cropped image data to bytes
    image_bytes = cropped_image.read()
    
    # Convert to grayscale
    img_array = np.frombuffer(image_bytes, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Convert back to bytes
    _, img_encoded = cv2.imencode('.jpg', gray_img)
    gray_image_bytes = img_encoded.tobytes()
    
    # Process the grayscale image and generate the Excel file
    image = Image(src=io.BytesIO(gray_image_bytes))
    image.to_xlsx(dest="table.xlsx",
                   ocr=paddle_ocr,
                   implicit_rows=False,
                   borderless_tables=True,
                   min_confidence=50)
    
    # Load the generated Excel file into pandas for manipulation
    df = pd.read_excel("table.xlsx")
    
    # Clean up column names by stripping whitespace and normalizing
    print("Columns in DataFrame:", df.columns.tolist())
    df.columns = [col.strip().replace('\n', ' ') for col in df.columns]

    # Assign correct names to the columns if necessary
    expected_columns = ['Name', 'Enrollment Number'] + [f'Attendance {i}' for i in range(len(df.columns) - 2)]
    df.columns = expected_columns
    
    # Check for missing columns
    if not all(col in df.columns for col in ['Name', 'Enrollment Number']):
        raise ValueError("One or more expected columns are missing from the DataFrame.")
    
    # Assume first column is 'Name', second is 'Enrollment Number', and others are attendance columns
    attendance_columns = df.columns[2:]  # All columns after the first two are attendance columns
    
    # Count 'P's in each row for total attendance
    df['Total Attendance'] = df[attendance_columns].apply(lambda row: (row == 'P').sum(), axis=1)
    
    # Keep only 'Name', 'Enrollment Number', and 'Total Attendance'
    df = df[['Name', 'Enrollment Number', 'Total Attendance']]
    
    # Save the modified DataFrame back to an Excel file
    output_file = "modified_table.xlsx"
    df.to_excel(output_file, index=False)
    
    # Send back the modified Excel file
    return send_file(output_file, as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
