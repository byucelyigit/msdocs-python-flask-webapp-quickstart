import os
import config
from question import Answer


from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)

root_dir = "c:\\Users\\burak.yucelyigit\\OneDrive\\kisisel\Yazılım\\openai\\crawler\\SemanticCatalogSearch\\"
HOST = config.settings['host']
MASTER_KEY = config.settings['master_key']
DATABASE_ID = config.settings['database_id']
CONTAINER_ID = config.settings['container_id']

"""
test yaparken doğrudan lokal bilgisayarda python app.py demek mümkün.
işler yolundaysa sunucu çalışıyor. 127.0.0.1:5000 diyerek loak uygulamayı çalıştırmak mümkün.
sunucu tarafına göndermek için git pipeline kullanılıyor.
Burada aksionları  git websayfasındaki actions ile görmek mümkün. 

Uygulama tarafında azure üzerinde uygulamanın config sayfasına gidip env değişkenlerni
tanımlamak gerekiyor.

şu hali ile azure üzerinde çalışıyor sistem. ve 68 dönüyolr.

"""


@app.route('/')
def index():
   print('Request for index page received')
   return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
   name = request.form.get('name')
   if name:
       print('Request for hello page received with name=%s' % name)
       return render_template('hello.html', name = ReturnSomething(name))
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


def ReturnSomething(name):
    r = Answer(name)
    return r

if __name__ == '__main__':
   app.run()
