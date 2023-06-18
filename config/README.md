Rename config-template.ini to config.ini and write the necessary keys.

Run "openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365" for the certificate and key files in order to run the app on a secure connection https.
