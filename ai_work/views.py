from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.conf import settings
import openai
from openai import OpenAI
import os
import requests
import uuid


def work(request):
    return render(request, 'work.html')

def gen_res(request):
    if request.method == 'GET':
        return JsonResponse({'error': 'invalid request'})

    type = request.POST['type']
    prompt = request.POST['prompt']
    response = {'status': False}
    res, error = generate_response(prompt, type)
    if error:
        response['error'] = res
        return JsonResponse(response)
    response['status'] = True
    response['content'] = res
    if type:
        response['img_name'] = res.replace('media/', '')
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
        response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": prompt},
                    ]
                    )
        data = response.choices[0].message.content
        return data, False

    except openai.BadRequestError as err:
        if err.response:
            err_dt = err.response.json()
            err_msg = err_dt['error']['message']
            return err_msg, True
    except Exception as err:
        return None, True

def download_image(url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img_data = response.content
            base_dir = settings.BASE_DIR
            img_name = f'{uuid.uuid1()}.jpg'
            img_path = os.path.join(base_dir, f'media/{img_name}')
            with open(img_path, 'wb') as f:
                f.write(img_data)
            img_path = f'media/{img_name}'
            return img_path
    except Exception as err:
        return None

def download_img(request, img_name):
    img_name = img_name.replace('/', '\\')
    img_path = os.path.join(settings.BASE_DIR, f'media\{img_name}')
    if os.path.exists(img_path):
        with open(img_path, 'rb') as img:
            response = HttpResponse(img.read(), content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="{img_name}"'
            return response
    else:
        return JsonResponse({'error': 'file not found'})