from transformers import pipeline

# Модель для определения намерения (intent)
intent_model = None

# Модель для извлечения параметров (жанр, год и т.д.)
ner_model = None