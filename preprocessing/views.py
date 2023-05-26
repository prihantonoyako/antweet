import re
import string
import pandas as pd
from django.http import JsonResponse
from preprocessing.models import UnprocessedData
from preprocessing.serializers import PreProcessSerializer
from nltk.corpus import stopwords
from nltk.corpus import sentiwordnet as swn
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from deep_translator import GoogleTranslator

def deEmojify(text):
	regrex_pattern = re.compile(pattern = "["
		u"\U0001F600-\U0001F64F"  # emoticons
		u"\U0001F300-\U0001F5FF"  # symbols & pictographs
		u"\U0001F680-\U0001F6FF"  # transport & map symbols
		u"\U0001F1E0-\U0001F1FF"  # flags (iOS)
						   "]+", flags = re.UNICODE)
	return regrex_pattern.sub(r' ',text)

def textFiltrator(text):
	number_pattern = re.compile(pattern = "[0-9]+")
	punctuation_pattern = re.compile(pattern = "["
			+ string.punctuation +
	"]\S+")
	
	proc_text = re.sub(r"(?:\@|http?|https?|www?|\#|rp)\S+", "", text)
	proc_text = ' '.join(word.strip(string.punctuation) for word in proc_text.split())
	proc_text = number_pattern.sub(r' ', proc_text)
	proc_text = punctuation_pattern.sub(r' ', proc_text)
	proc_text = ' '.join( [w for w in proc_text.split() if len(w)>1] )
	return proc_text

def asciiTransformer(text):
	return text.encode('ascii', 'ignore').decode('ascii')

def textTranslator(text):
	return GoogleTranslator(source='auto', target='en').translate(text)

def stopWordRemover(text):
	stop_words = set(stopwords.words('english'))
 
	word_tokens = word_tokenize(str(text))

	filtered_sentence = [w for w in word_tokens if not w.lower() in stop_words]

	filtered_sentence = []
	
	for w in word_tokens:
		if w not in stop_words:
			filtered_sentence.append(w)
	
	return filtered_sentence

def lemmatize_words(text):
	# words = text.split()
	lemmatizer = WordNetLemmatizer()
	words = text
	words = [lemmatizer.lemmatize(word,pos='v') for word in words]
	return ' '.join(words)

def pre_process(request):
	if request.method == 'GET':
		query_params = request.GET
		if query_params['step'] == "prapemrosesan":
			data = UnprocessedData.objects.all()
			serializer = PreProcessSerializer(data, many=True)
			return JsonResponse({"data":serializer.data}, safe=False, status=200)
		elif query_params['step'] == "penyesuaian":
			data = UnprocessedData.objects.all().values()
			serializer = PreProcessSerializer(data, many=True)
			df = pd.DataFrame(serializer.data)
			df['komentar'] = df['komentar'].str.lower()
			df['komentar'] = df['komentar'].apply(deEmojify)
			df['komentar'] = df['komentar'].apply(textFiltrator)
			df['komentar'] = df['komentar'].apply(asciiTransformer)

			# Translate to english
			df['alih_bahasa'] = df['komentar'].apply(textTranslator)
			df['alih_bahasa'] = df['alih_bahasa'].apply(textFiltrator)
			df['alih_bahasa'] = df['alih_bahasa'].apply(asciiTransformer)

			# Stop words
			df['kata'] = df['alih_bahasa'].apply(stopWordRemover)
			df['kata'] = df['kata'].apply(lemmatize_words)
			df['tokenization'] = df['kata'].apply(word_tokenize)
			return JsonResponse(df.to_dict('records'), safe=False, status=200)
		