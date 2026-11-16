"""Machine learning component: auto-categorize an expense from its description.

This is real ML: a TF-IDF + Naive Bayes text classifier trained on a labeled
sample dataset (data/sample_expenses.csv). Replace or extend the CSV with your
own data to improve it.
"""
import csv
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.pipeline import Pipeline

DEFAULT_DATASET = Path(__file__).parent / "data" / "sample_expenses.csv"
FALLBACK_CATEGORY = "Other"


class ExpenseCategorizer:
    def __init__(self, dataset_path=DEFAULT_DATASET, min_confidence=0.2):
        self._dataset_path = Path(dataset_path)
        self._min_confidence = min_confidence
        self._pipeline = Pipeline(
            [
                # Character n-grams tolerate typos and word forms ("jeep" vs "jeepney").
                ("tfidf", TfidfVectorizer(lowercase=True, analyzer="char_wb", ngram_range=(2, 4))),
                ("clf", MultinomialNB(alpha=0.3)),
            ]
        )
        self._trained = False

    def _load(self):
        texts, labels = [], []
        with open(self._dataset_path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                texts.append(row["description"])
                labels.append(row["category"])
        return texts, labels

    def train(self) -> "ExpenseCategorizer":
        texts, labels = self._load()
        self._pipeline.fit(texts, labels)
        self._trained = True
        return self

    @property
    def is_trained(self) -> bool:
        return self._trained

    def predict(self, description):
        """Return (category, confidence). Low confidence falls back to 'Other'."""
        if not self._trained:
            raise RuntimeError("Call train() before predict().")
        text = (description or "").strip()
        if not text:
            return FALLBACK_CATEGORY, 0.0
        probabilities = self._pipeline.predict_proba([text])[0]
        best = probabilities.argmax()
        confidence = float(probabilities[best])
        if confidence < self._min_confidence:
            return FALLBACK_CATEGORY, confidence
        return str(self._pipeline.classes_[best]), confidence
