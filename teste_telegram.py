import requests

telegram_bot_token = '6644963671:AAHgK96UoirMdoExb4EzPsbaJLmWQyi76gU'
telegram_chat_id = '-1001744400927'
mensagem = 'Se cair vou avisar'

url = f'https://api.telegram.org/bot{telegram_bot_token}/sendMessage'
payload = {
    'chat_id': telegram_chat_id,
    'text': mensagem
}

response = requests.post(url, data=payload)
print(response.json())