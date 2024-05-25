import os
import numpy as np
import matplotlib.pyplot as plt
from PIL import Image
import requests
from flask import Flask, request, redirect, url_for, render_template

app = Flask(__name__, static_folder='static')

UPLOAD_FOLDER = 'static/'  # Path to the upload folder inside static
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Replace with your Google reCAPTCHA keys
SECRET_KEY = "6LfEhdgpAAAAAGqOW8Na_BAGi6nfc5hb6lNYjrD8"
SITE_KEY = "6LfEhdgpAAAAAG901eNJnE7Dph8LLocypngjDR_s"

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # Verify Google reCAPTCHA
        recaptcha_response = request.form.get('g-recaptcha-response')
        if not verify_recaptcha(recaptcha_response):
            return "Ошибка проверки капчи", 400

        file = request.files['image']
        noise_level = float(request.form['noise'])

        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        image = Image.open(file_path)  # Open the image
        noisy_image = add_noise(image, noise_level)  # Add noise

        # Create histograms for the images
        original_hist = image.histogram()
        noisy_hist = noisy_image.histogram()

        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot(original_hist, color='b')
        plt.title('Гистограмма оригинального изображения')
        plt.xlabel('Интенсивность пикселей')
        plt.ylabel('Частота')
        plt.subplot(1, 2, 2)
        plt.plot(noisy_hist, color='r')
        plt.title('Гистограмма зашумленного изображения')
        plt.xlabel('Интенсивность пикселей')
        plt.ylabel('Частота')

        noisy_image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'noisy_image.png')
        histograms_path = os.path.join(app.config['UPLOAD_FOLDER'], 'histograms.png')
        plt.savefig(histograms_path)
        noisy_image.save(noisy_image_path)

        return render_template('index.html',
                               original_image=url_for('static', filename=file.filename),
                               original_image_name=file.filename,  # Передача имени оригинального изображения
                               noisy_image=url_for('static', filename='noisy_image.png'),
                               histograms=url_for('static', filename='histograms.png'),
                               site_key=SITE_KEY)

    return render_template('index.html', site_key=SITE_KEY)

def add_noise(image, noise_level):
    np_image = np.array(image)
    mean = 0
    var = noise_level * 255
    sigma = var ** 0.5
    gaussian = np.random.normal(mean, sigma, np_image.shape).astype('uint8')
    noisy_image = Image.fromarray(np.clip(np_image + gaussian, 0, 255).astype('uint8'))
    return noisy_image

def verify_recaptcha(recaptcha_response):
    payload = {
        'secret': SECRET_KEY,
        'response': recaptcha_response
    }
    response = requests.post("https://www.google.com/recaptcha/api/siteverify", data=payload)
    result = response.json()
    return result.get('success', False)

if __name__ == '__main__':
    app.run(debug=True)