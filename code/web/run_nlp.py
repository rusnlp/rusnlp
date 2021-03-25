from flask import Flask, url_for, send_from_directory
from lang_converter import LangConverter
from nlp import *
from api import api_bp
from flasgger import Swagger

config = configparser.RawConfigParser()
config.read('rusnlp.cfg')
url = config.get('Other', 'url')

app_rusnlp = Flask(__name__, static_url_path='/C:/Users/79850/Desktop/rusnlp/code/web/data/')
swagger = Swagger(app_rusnlp)


@app_rusnlp.route('/data/<path:query>/')
def send(query):
    if 'rus_nlp.db.gz' in query:
        return redirect('https://rusvectores.org/static/rusnlp/rus_nlp.db.gz')
    else:
        return send_from_directory('data/', query)


app_rusnlp.url_map.converters['lang'] = LangConverter
app_rusnlp.register_blueprint(nlpsearch)
app_rusnlp.register_blueprint(api_bp)


@app_rusnlp.context_processor
def set_globals():
    return dict(lang=g.lang, strings=g.strings)


def url_for_other_page(page):
    args = request.view_args.copy()
    args['page'] = page
    return url_for(request.endpoint, **args)


app_rusnlp.jinja_env.globals['url_for_other_page'] = url_for_other_page

if __name__ == '__main__':
    app_rusnlp.run()
