from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import azure.cognitiveservices.speech as speechsdk
import configparser
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os

MAX_FILE_SIZE = 1 * 1024 * 1024  # 1 MB

# Create a configuration parser instance
config = configparser.ConfigParser()

# Read the configuration file
config.read('config/config.ini')

api_key = config.get('azure', 'API_KEY')
api_region = config.get('azure', 'API_REGION')
api_language = config.get('azure', 'API_LANGUAGE')

app = Flask(__name__, static_folder='public_html')
limiter = Limiter(app=app, key_func=get_remote_address, default_limits=["100 per day", "40 per hour"],)



app.config['UPLOAD_EXTENSIONS'] = ['.wav']
app.config["LIMITER_HEADERS_ENABLED"] = True

CORS(app)


@app.route('/static/<path:filename>')
@limiter.exempt
def serve_files(filename):
    return send_from_directory('public_html/static', filename)


@app.route('/')
@limiter.exempt
def hello():
    return app.send_static_file('index.html')

@app.route('/speech', methods=['POST'])
def handle_recognize():
    
    # Get the audio filestorage object 
    input_file = request.files['audio']
    file_size = int(request.headers.get('Content-Length', 0))
    if file_size > MAX_FILE_SIZE:
        error_msg = f"File size exceeds the maximum limit of 1MB."
        return jsonify({'error': error_msg}), 413  # Return HTTP 413 Payload Too Large error
    
    input_data = input_file.read()
    input = recognize_from_input(input_data)
    
    return jsonify({"text": input})

def recognize_from_input(audio_in):
    
    speech_config = speechsdk.SpeechConfig(subscription=api_key, region=api_region)
    speech_config.speech_recognition_language=api_language
    
    # this example uses audio streams so there is no need to save the wav files in storage 
    audio_stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=audio_stream)

    # write audio data and then close the stream
    # closing the stream is needed if the audio is less than 15 seconds
    audio_stream.write(audio_in)
    audio_stream.close()
    
    speech_recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)

    speech_recognition_result = speech_recognizer.recognize_once_async().get()

    if speech_recognition_result.reason == speechsdk.ResultReason.RecognizedSpeech:
        print("Recognized: {}".format(speech_recognition_result.text))
        return speech_recognition_result.text
    elif speech_recognition_result.reason == speechsdk.ResultReason.NoMatch:
        print("No speech could be recognized: {}".format(speech_recognition_result.no_match_details))
    elif speech_recognition_result.reason == speechsdk.ResultReason.Canceled:
        cancellation_details = speech_recognition_result.cancellation_details
        print("Speech Recognition canceled: {}".format(cancellation_details.reason))
        if cancellation_details.reason == speechsdk.CancellationReason.Error:
            print("Error details: {}".format(cancellation_details.error_details))
            print("Did you set the speech resource key and region values?")
    return ""


            
if __name__ == '__main__':
    # https secure conection required in order to send audio data
    # run  "openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365"
    # in order to create a new key and certificate
    context = ('config/cert.pem', 'config/key.pem')
    app.run(host='0.0.0.0', port=443, ssl_context=context)


    
    