from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import openai
from openai import OpenAI
import os
import requests
import uuid
from nltk.sentiment import SentimentIntensityAnalyzer


base_dir = settings.BASE_DIR

def work(request):
    return render(request, 'work.html')

def gen_res(request):
    if request.method == 'GET':
        return JsonResponse({'error': 'invalid request'})

    type = request.POST['type']
    if request.FILES:
        audio_file = request.FILES['prompt']
        prompt = os.path.join(base_dir, f'media/audio/{audio_file.name}')
        with open(prompt, 'wb') as f:
            for chunk in audio_file.chunks():
                f.write(chunk)
    else:
        prompt = request.POST['prompt']
    response = {'status': False}
    res, error = generate_response(prompt, type)
    if error:
        response['error'] = res
        return JsonResponse(response)
    response['status'] = True
    response['content'] = res
    if type == 'img':
        response['img_name'] = res.replace('media/images', '')
    if type == 'audio':
        response['audio_name'] = res.replace('media/audio', '')
    return JsonResponse(response)

def generate_response(prompt, type):
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        OpenAI.api_key = api_key
        client = OpenAI()
        if type == 'img':
            response = client.images.generate(
                        model='dall-e-2',
                        prompt=prompt,
                        size="1024x1024",
                        quality="standard",
                        n=1,
                        )
            img_url = response.data[0].url
            img = download_image(img_url)
            if not img:
                return None, True
            return img, False

        if type == 'text':
            response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[
                            {"role": "system", "content": prompt},
                        ]
                        )
            data = response.choices[0].message.content
            return data, False

        if type == 'audio':
            response = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=prompt
            )
            file_name = f'{uuid.uuid1()}.mp3'
            file_path = os.path.join(base_dir, f'media/audio/{file_name}')
            response.stream_to_file(file_path)
            file_path = f'media/audio/{file_name}'
            return file_path, False

        if type == 'a2t':
            audio_file =  open(prompt, 'rb')
            response = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
            os.remove(prompt)
            return response.text, False

        if type == 'sa':
            sia = SentimentIntensityAnalyzer()
            sentiment_scores = sia.polarity_scores(prompt)
            if sentiment_scores['compound'] > 0:
                analyzed = 'Positive'
            elif sentiment_scores['compound'] < 0:
                analyzed = 'Negative'
            else:
                analyzed = 'Neutral'
            return analyzed, False

        return 'invalid request', True

    except openai.BadRequestError as err:
        if err.response:
            err_dt = err.response.json()
            err_msg = err_dt['error']['message']
            return err_msg, True
    except Exception as err:
        print('Error?>>', err)
        return None, True

def download_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img_data = response.content
            img_name = f'{uuid.uuid1()}.jpg'
            img_path = os.path.join(base_dir, f'media/images/{img_name}')
            with open(img_path, 'wb') as f:
                f.write(img_data)
            img_path = f'media/images/{img_name}'
            return img_path
    except Exception as err:
        return None

def download_img(request, img_name):
    img_name = img_name.replace('/', '\\')
    img_path = os.path.join(settings.BASE_DIR, f'media/images/{img_name}')
    if os.path.exists(img_path):
        with open(img_path, 'rb') as img:
            response = HttpResponse(img.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{img_name}"'
            return response
    else:
        return JsonResponse({'error': 'file not found'})