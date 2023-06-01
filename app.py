import os
import openai
from openai.embeddings_utils import distances_from_embeddings

from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)


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
       return render_template('hello.html', name = ReturnSomething())
   else:
       print('Request for hello page received with no name or blank name -- redirecting')
       return redirect(url_for('index'))


def SortedList(question, top):
    df_embeddings = pd.read_csv(root_dir + 'embeddings_eng.csv')    
    q_embeddings = openai.Embedding.create(input=question, engine='text-embedding-ada-002')['data'][0]['embedding']

    # code takes the 'embedding' column in df (which contains strings representing arrays of numbers) and converts each string to a NumPy array, which is then stored in a new column called 'embedding_values'.
    df_embeddings['embedding_values'] = df_embeddings.embedding.apply(eval).apply(np.array)
    # Get the distances from the embeddings
    df_embeddings['distances'] = distances_from_embeddings(q_embeddings, df_embeddings['embedding_values'].values, distance_metric='cosine')    

    # sort values ascending. smallest distance is at top
    df_sorted = df_embeddings.sort_values('distances')
    # top n value from df_sorted
    df_top_n = df_sorted.iloc[0:top]
    # first_row_sorted = df_sorted.iloc[0]
    return df_top_n

def ReturnSomething():
    return "result"

if __name__ == '__main__':
   app.run()
