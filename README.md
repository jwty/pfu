# pseudocode-file-uploader
Python file uploader using Flask

## Requirements
`flask` and `werkzeug`

## Usage
Clone and run `setup.py` to set up a sqlite3 database, config file and uploads directory (make sure script has write permissions).

Run `server.py` for [developement server](http://flask.pocoo.org/docs/1.0/server/) or use [one of deployement options](http://flask.pocoo.org/docs/0.12/deploying/#deployment),
for example `gunicorn`:
```
$ gunicorn --bind 0.0.0.0:8000 server:app
```

Use a web interface (`localhost:5000` if using dev server) or send POST request manually:
```
$ curl -X POST http://localhost:5000/upload -F 'file_up=@example.txt' -F 'secret=secret'
```
Or for JSON response:
```
$ curl -X POST http://localhost:5000/upload?json -F 'file_up=@example.txt' -F 'secret=secret'

{
  "file": "example.txt", 
  "response": "ok", 
  "url": "http://localhost:5000/9q6w3z6d.txt"
}
```
