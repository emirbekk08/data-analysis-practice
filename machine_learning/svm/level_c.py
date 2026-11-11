import time
import numpy as np
import matplotlib
matplotlib.use("Agg")  # Чтобы график сохранялся в файл без интерфейса
import matplotlib.pyplot as plt
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import SVC, LinearSVC
from sklearn.ensemble import RandomForestClassifier
from sklearn.datasets import make_classification

print("=== ЗАДАНИЕ УРОВНЯ C: ВЫСОКОРАЗМЕРНЫЕ ДАННЫЕ ===")

# 1. Текстовый датасет + TF-IDF
print("\n[1/4] Загрузка текстового датасета...")
categories = ['sci.space', 'comp.graphics']
data_train = fetch_20newsgroups(subset='train', categories=categories, remove=('headers', 'footers', 'quotes'))
X_texts, y = data_train.data, data_train.target

vectorizer = TfidfVectorizer(max_features=5000)
X_tfidf = vectorizer.fit_transform(X_texts)
print(f"Размерность после TF-IDF: объектов = {X_tfidf.shape[0]}, признаков = {X_tfidf.shape[1]}")

# 2. Сравнение моделей
print("\n[2/4] Обучение моделей на текстах...")
t0 = time.perf_counter()
svm_model = LinearSVC(random_state=42, max_iter=10000)
svm_model.fit(X_tfidf, y)
print(f"LinearSVC      | Время: {time.perf_counter() - t0:.4f} сек | Точность: {svm_model.score(X_tfidf, y):.3f}")

t0 = time.perf_counter()
rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
rf_model.fit(X_tfidf, y)
print(f"Random Forest  | Время: {time.perf_counter() - t0:.4f} сек | Точность: {rf_model.score(X_tfidf, y):.3f}")

# 3. Стресс-тест масштабируемости
print("\n[3/4] Замер зависимости времени от объема выборки...")
sizes = [2000, 4000, 8000, 16000]
rbf_times, linear_times = [], []

for n in sizes:
    X_scale, y_scale = make_classification(n_samples=n, n_features=100, random_state=42)
    
    t0 = time.perf_counter()
    SVC(kernel="rbf").fit(X_scale, y_scale)
    rbf_times.append(time.perf_counter() - t0)
    
    t0 = time.perf_counter()
    LinearSVC(max_iter=10000, random_state=42).fit(X_scale, y_scale)
    linear_times.append(time.perf_counter() - t0)
    
    print(f"Выборка N = {n:<5} | rbf SVC: {rbf_times[-1]:.3f} с | LinearSVC: {linear_times[-1]:.3f} с")

# 4. Построение и сохранение графика
print("\n[4/4] Отрисовка графика...")
plt.figure(figsize=(9, 5))
plt.plot(sizes, rbf_times, 'o-', color='crimson', label='Ядерный SVM (rbf)')
plt.plot(sizes, linear_times, 's-', color='royalblue', label='Линейный SVM (LinearSVC)')
plt.title("Уровень C: Зависимость времени обучения SVM от объема выборки")
plt.xlabel("Количество объектов в выборке (N)")
plt.ylabel("Время обучения (секунды)")
plt.grid(True, linestyle="--", alpha=0.5)
plt.legend()
plt.tight_layout()
plt.savefig("svm_level_c_scalability.png", dpi=150)
print("[Успех] График сохранен в файл: svm_level_c_scalability.png")

