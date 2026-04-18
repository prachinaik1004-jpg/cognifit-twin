from transformers import pipeline

# This will download the model the first time you run it (approx 200MB)
analyzer = pipeline("text-classification", 
                    model="cardiffnlp/twitter-roberta-base-sentiment-latest")

def get_stress_context(text: str):
    results = analyzer(text)
    emotion = results[0]['label']
    score = results[0]['score']
    
    # We flag stress if they sound fearful, angry, or sad
    is_stressed = emotion in ['fear', 'anger', 'sadness'] and score > 0.6
    
    return {"emotion": emotion, "stress_flag": is_stressed}