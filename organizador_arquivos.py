import os
from google.cloud import vision
from dotenv import load_dotenv
import io
from pdf2image import convert_from_path

# Carrega variáveis do .env
load_dotenv()

# Autenticação
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

client = vision.ImageAnnotatorClient()

POPPLER_PATH = r"C:\Users\User\Downloads\poppler-22.04.0\Library\bin"
pdf_path = "DCTF 05-2024.pdf" 

def conversor_imagem_pdf(pdf_path):
    try:
        images = convert_from_path(pdf_path, dpi=300, poppler_path=POPPLER_PATH)
        return images
    except Exception as e:
        print(f"Erro ao converter PDF em imagens: {e}")
        return []

images = conversor_imagem_pdf(pdf_path)

for i, image in enumerate(images):
    # Salva temporariamente como JPEG em memória
    img_byte_arr = io.BytesIO()
    image.save(img_byte_arr, format='JPEG')
    content = img_byte_arr.getvalue()

    vision_image = vision.Image(content=content)
    try:
        response = client.text_detection(image=vision_image)
        texts = response.text_annotations

        print(f"\nPágina {i + 1}:")
        if texts:
            print(texts[0].description)
        else:
            print("Nenhum texto encontrado.")
    except Exception as e:
        print(f"Erro ao processar OCR na página {i + 1}: {e}")

vision_image = vision.Image(content=content)

def organizar_arquivos():
    pass

