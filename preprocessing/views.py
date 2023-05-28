import re
import string
import pandas as pd
import numpy as np
import spacy
from django.http import JsonResponse
from preprocessing.models import UnprocessedData
from preprocessing.models import ProcessedData
from preprocessing.models import ClassifiedData
from preprocessing.serializers import PreProcessSerializer
from preprocessing.serializers import AdjustmentSerializer
from preprocessing.serializers import ClassifierSerializer
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

def save_preprocess(processedText):
	processed = ProcessedData(text=processedText)
	processed.save()

def sentiment_analyzer(data, name):
    nlp=spacy.load('en_core_web_sm')
    positive_sentiments=[]
    negative_sentiments=[]
    for tex in data[name].values:
        tex=nlp(tex)
        noun=[]
        verb=[]
        adj=[]
        adv=[]
        for i in tex :
            if i.pos_=='NOUN':
                noun.append(i)
            elif i.pos_ =='ADJ':
                adj.append(i)
            elif i.pos_ =='VERB':
                verb.append(i)
            elif i.pos_=='ADV':
                adv.append(i)
        neg_score=[]
        pos_score=[]
        for i in tex :
            try:
                if i in noun:
                    x=swn.senti_synset(str(i)+'.n.01')
                    neg_score.append(x.neg_score())
                    pos_score.append(x.pos_score())
                elif i in adj:
                    x=swn.senti_synset(str(i)+'.a.02')
                    neg_score.append(x.neg_score())
                    pos_score.append(x.pos_score())
                elif i in adv :
                    x=swn.senti_synset(str(i)+'.r.02')
                    neg_score.append(x.neg_score())
                    pos_score.append(x.pos_score())
                elif i in verb :
                    x=swn.senti_synset(str(i)+'.v.02')
                    neg_score.append(x.neg_score())
                    pos_score.append(x.pos_score())

            except:
                pass
        positive_sentiments.append(np.mean(pos_score))
        negative_sentiments.append(np.mean(neg_score))

    data['positive']=positive_sentiments
    data['negative']=negative_sentiments
    
def save_classified(text, nilai, label):
	classified = ClassifiedData(text=text, nilai=nilai, label=label)
	classified.save()
    
def graph_counter(label):
	return label

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
			del df['nama_akun']
			del df['tanggal']
			del df['id']
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
			del df['komentar']
			df['kata'].apply(save_preprocess)
			return JsonResponse({"data":df.to_dict('records')}, safe=False, status=200)
		elif query_params['step'] == "klasifikasi":
			data = ProcessedData.objects.count()
			if data == 0:
				return JsonResponse({"message": "preprocess before classify!"}, safe=False, status=422)
			
			data = ProcessedData.objects.all().values()
			serializer = AdjustmentSerializer(data, many=True)
			df = pd.DataFrame(serializer.data)
			sentiment_analyzer(df, 'text')
			overall=[]
			nilai=[]
			for i in range(len(data)):
				if df['positive'][i]>df['negative'][i]:
					tempNilai = df['positive'][i]
					nilai.append(df['positive'][i])
					overall.append('Positive')
				elif df['positive'][i]<df['negative'][i]:
					nilai.append(df['negative'][i])
					overall.append('Negative')
				else:
					nilai.append(df['negative'][i])
					overall.append('Neutral')
			df['label']=overall
			df['nilai']=nilai
			del df['negative']
			del df['positive']
			df.apply(lambda x: save_classified(x['text'], x['nilai'], x['label']), axis=1)
			return JsonResponse({"data": df.to_dict('records')}, safe=False, status=200)
		elif query_params['step'] == "grafik":
			data = ClassifiedData.objects.count()
			if data == 0:
				return JsonResponse({"message": "please classify data!"}, safe=False, status=422)
			
			data = ClassifiedData.objects.all().values()
			serializer = ClassifierSerializer(data, many=True)
			df = pd.DataFrame(serializer.data)
			positive = negative = neutral = 0
			for i in range(len(data)):
				if df['label'][i] == "Positive":
					positive+=1
				elif df['label'][i] == "Negative":
					negative+=1
				elif df['label'][i] == "Neutral":
					neutral+=1
			return JsonResponse({"data": {"positive": positive, "negative": negative, "neutral": neutral}}, safe=False, status=200)
		else:
			return JsonResponse({"message": "invalid query params"}, safe=False, status=422)
		