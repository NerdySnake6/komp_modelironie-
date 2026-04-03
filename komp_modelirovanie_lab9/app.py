from flask import Flask, render_template, request, redirect, url_for, flash
import boto3
from botocore.client import Config
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = 'supersecretkey'

# Настройка S3 клиента для Yandex Cloud
s3_client = boto3.client(
    's3',
    endpoint_url=os.getenv('S3_ENDPOINT_URL'),
    region_name=os.getenv('S3_REGION'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    config=Config(signature_version='s3v4')
)

BUCKET = os.getenv('S3_BUCKET_NAME')


@app.route('/')
def index():
    try:
        response = s3_client.list_objects_v2(Bucket=BUCKET)
        files = response.get('Contents', [])
    except Exception as e:
        flash(f"Ошибка при получении списка файлов: {e}", "error")
        files = []

    return render_template('index.html', files=files)


@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        flash("Файл не выбран", "error")
        return redirect(url_for('index'))

    file = request.files['file']
    if file.filename == '':
        flash("Файл не выбран", "error")
        return redirect(url_for('index'))

    try:
        s3_client.upload_fileobj(file, BUCKET, file.filename)
        flash(f"Файл '{file.filename}' успешно загружен", "success")
    except Exception as e:
        flash(f"Ошибка при загрузке: {e}", "error")

    return redirect(url_for('index'))


@app.route('/delete/<path:filename>')
def delete_file(filename):
    try:
        s3_client.delete_object(Bucket=BUCKET, Key=filename)
        flash(f"Файл '{filename}' удалён", "success")
    except Exception as e:
        flash(f"Ошибка при удалении: {e}", "error")
    return redirect(url_for('index'))


@app.route('/presign/<path:filename>')
def presign_file(filename):
    try:
        url = s3_client.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET, 'Key': filename},
            ExpiresIn=3600  # 1 час
        )
        return redirect(url)
    except Exception as e:
        flash(f"Ошибка при генерации ссылки: {e}", "error")
        return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8000)