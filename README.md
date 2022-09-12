# pfu file uploader
Python file uploader using Flask. Readme currently outdated and in process of being rewritten.

## Requirements
`flask` and `werkzeug`

## Installation & usage
### Setup
Clone and run `setup.py` to set up a sqlite3 database, config file and uploads directory (make sure script has write permissions).

Run `server.py` for [developement server](http://flask.pocoo.org/docs/1.0/server/) or use [one of deployement options](http://flask.pocoo.org/docs/0.12/deploying/#deployment),
for example `gunicorn`:
```
$ gunicorn --bind 0.0.0.0:8000 server:app
```

### Form fields
* `file_up` - file to upload
* `secret` (string) - secret key (as set in by `setup.py`)
* `expire` (bool) - to set file expiry date (as for now does nothing but useful nonetheless)
* `expire_date` (string) - file expiry date in YYYY-MM-DD format (cause html)
* `expire_time` (string) - file expiry time in HH:MM time (cause html)
* `keep` (bool) - whether to keep original file name or not (original file name is kept as first segment of newly generated file name, for example `test-wgownpqy.jpg`)

### Usage
Use a web interface (`localhost:5000` if using dev server) or send POST request manually:
```
$ curl -X POST http://localhost:5000/upload -F 'file_up=@example.txt' -F 'secret=secret'
```
Or for JSON response:
```
$ curl -X POST http://localhost:5000/upload?json -F 'file_up=@example.txt' -F 'secret=secret'

{
  "data": {
    "file": "test.jpg", 
    "url": "http://127.0.0.1:5000/TUMFEhE.jpg"
  }, 
  "status": "success"
}
```

Using `requests` library:
```
import requests
url = "http://127.0.0.1:5000/upload?json"

data = {
        'secret' : 'secret',
        'expire' : True,
        'expire_date' : '2019-10-10',
        'expire_time' : '16:20',
        'keep' : True,
}
files = { 'file_up' : open('test.jpg', 'rb') }

r = requests.post(url, data=data, files=files)
```
### Deleting a file
Delete file through web interface (`localhost:5000/delete/filename.txt`), or send POST request. In both cases you need to provide the secret key.
```
curl -X POST "http://localhost:5000/delete/3HzK8ic.jpg?json" -F "secret=secret"

{
  "data": {
    "message": "file deleted"
  }, 
  "status": "success"
}
```
Script validates if file is allowed to be deleted by checking against database (instead for example checking if file exists in `uploads/`) to make sure only valid files are deleted.
