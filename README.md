# toolz4biz-test

# SETUP

1. Run `pip install -r requirements.txt`, make sure your python environment's version is 3.9.12
2. Run the below command (https://github.com/myshell-ai/MeloTTS/blob/main/docs/install.md#linux-and-macos-install)

```
git clone https://github.com/myshell-ai/MeloTTS.git
cd MeloTTS
pip install -e .
python -m unidic download
```
3. install ffmpeg and ngrok in your system

# Telegram

1. prepare the file `telegram_api_token` with your telegram api token in it

2. run `python telegram-app.py`

3. Start the session by sending the bot `/special_command`

# Whatsapp

1. run `ngrok http 5000`

2. open `https://www.twilio.com/console/sms/whatsapp/sandbox` and navigate to `Send WhatsApp message` and then to `Sandbox settings`

3. Put the forwarding url to the configuration

4. run `python whatsapp-app.py`

5. Start the session by sending the bot `special_command`