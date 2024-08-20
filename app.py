from flask import Flask, render_template, request, url_for
import os
from werkzeug.utils import secure_filename
from PIL import Image
import torchvision.transforms.functional as TF
import torch
import numpy as np
import pandas as pd
import CNN  # Ensure this is the correct import for your model script

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Utility function to check file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Load data and model
disease_info = pd.read_csv('disease_info.csv', encoding='cp1252')
supplement_info = pd.read_csv('supplement_info.csv', encoding='cp1252')

model = CNN.CNN(39)    
model.load_state_dict(torch.load("plant_disease_model_1_latest.pt"))
model.eval()

def prediction(image_path):
    image = Image.open(image_path)
    image = image.resize((224, 224))
    input_data = TF.to_tensor(image)
    input_data = input_data.view((-1, 3, 224, 224))
    output = model(input_data)
    output = output.detach().numpy()
    index = np.argmax(output)
    return index

# Define routes for the website
@app.route('/')
def home():
    return render_template('Home.html')

@app.route('/detection', methods=['GET', 'POST'])
def detection():
    if request.method == 'POST':
        if 'plant_image' not in request.files:
            return render_template('Detection.html', message='No file part')
        
        file = request.files['plant_image']
        if file.filename == '':
            return render_template('Detection.html', message='No selected file')
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            # Run the image through your model to get the disease prediction
            pred = prediction(file_path)
            
            # Ensure that the index is within bounds
            if pred >= len(disease_info) or pred >= len(supplement_info):
                return render_template('Detection.html', message='Prediction index out of bounds')
            
            title = disease_info['disease_name'][pred]
            description = disease_info['description'][pred]
            prevent = disease_info['Possible Steps'][pred]
            image_url = disease_info['image_url'][pred]

            # Use the correct path for supplement images
            supplement_name = supplement_info['supplement name'][pred]
            supplement_image_filename = supplement_info['supplement image'][pred]
            supplement_image_url = url_for('static', filename='supplement_images/' + supplement_image_filename)
            supplement_buy_link = supplement_info['buy link'][pred]

            result = {
                'title': title,
                'description': description,
                'prevention': prevent,
                'image_url': url_for('static', filename='uploads/' + filename),
                'supplement_image_url': supplement_image_url,
                'supplement_name': supplement_name,
                'supplement_buy_link': supplement_buy_link
            }

            return render_template('Detection.html', result=result)
        
        return render_template('Detection.html', message='File type not allowed')
    
    return render_template('Detection.html')

@app.route('/Features.html')
def features():
    return render_template('Features.html')

@app.route('/About.html')
def about():
    return render_template('About.html')

@app.route('/Contact.html')
def contact():
    return render_template('Contact.html')

# Run the app
if __name__ == '__main__':
    app.run(debug=True)
