import json
import os
import threading

import requests
from django.http.response import HttpResponse
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from bot.models import Game

# Create your views here.
zoom_verification_token = os.environ.get('VERIFICATION_TOKEN')
zoom_bot_jid = os.environ.get('BOT_JID')
zoom_client_id = os.environ.get('CLIENT_ID')
zoom_client_secret = os.environ.get('CLIENT_SECRET')


def exec_command(cmd: str, payload):
    split = cmd.split(' ')[0]
    if split == 'say':
        send_msg(cmd.removeprefix('say '), payload)

    elif split == 'list':
        msg = '*Games List (With Shrimp 🦐)*\n\n*Consider contributing! Send me or @✨Winning Lisa✨ a message and you will get credited with the game.*'

        for item in Game.objects.all():
            msg += f'\n\n{item.name}: {item.url}'

        send_msg(msg, payload)

    elif split == 'add':
        split = cmd.removeprefix('add ').split(';')
        try:
            game = Game(name=split[0], url=split[1])
            game.save()
            notify('Game added!', payload)
        except:
            notify('Syntax error!', payload)

    elif split == 'del':
        name = cmd.removeprefix('del ')
        try:
            Game.objects.get(name=name).delete()
            notify('Game removed!', payload)
        except Game.DoesNotExist:
            notify('This game does not exist!', payload)


def get_token():
    return requests.post('https://zoom.us/oauth/token?grant_type=client_credentials',
                         auth=(zoom_client_id, zoom_client_secret)).json()['access_token']


def notify(message, payload):
    message_id = send_msg(message, payload)["message_id"]

    timer = threading.Timer(2, delete_msg, [message_id, payload])
    timer.start()


def delete_msg(message_id, payload):
    token = get_token()

    requests.delete(f'https://api.zoom.us/v2/im/chat/messages/{message_id}', headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }, json={
        'robot_jid': zoom_bot_jid,
        'account_id': payload['accountId']
    })


def send_msg(message, payload):
    token = get_token()

    message = requests.post('https://api.zoom.us/v2/im/chat/messages', headers={
        'Content-Type': 'application/json',
        'Authorization': 'Bearer ' + token
    }, json={
        'robot_jid': zoom_bot_jid,
        'to_jid': payload['toJid'],
        'account_id': payload['accountId'],
        'content': {
            'head': {
                'text': message
            }
        },
        'is_markdown_support': True
    }).json()

    return message


@require_GET
def index(request):
    return HttpResponse('You found an easter egg!')


@require_GET
def authorize(request):
    return redirect(f'https://zoom.us/launch/chat?jid=robot_{zoom_bot_jid}')


@require_POST
@csrf_exempt
def shb(request):
    body = json.loads(request.body)
    payload = body['payload']
    exec_command(payload['cmd'], payload)
    return HttpResponse()
