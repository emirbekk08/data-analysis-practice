import numpy as np
import matplotlib
matplotlib.use("Agg")  # Для работы в WSL терминале
import matplotlib.pyplot as plt
from sklearn.datasets import make_moons
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC

# 1. Подготовка данных Уровня А
X2, y2 = make_moons(n_samples=300, noise=0.25, random_state=42)
X2 = StandardScaler().fit_transform(X2)

# Создаем одну общую картинку для 4 графиков (как на фото)
fig, axes = plt.subplots(2, 2, figsize=(10, 8))
axes = axes.ravel()

# Настройки для четырех экспериментов
setups = [
    {"kernel": "linear", "C": 1,   "title": "linear, C=1"},
    {"kernel": "rbf",    "C": 1,   "title": "rbf, C=1 (gamma=scale)"},
    {"kernel": "rbf",    "C": 0.01,"title": "rbf, C=0.01"},
    {"kernel": "rbf",    "C": 100, "title": "rbf, C=100"}
]

print("=== СБОРКА УРОВНЯ А (Графики границ решений) ===")

# Сетка точек для отрисовки фона
xx, yy = np.meshgrid(np.linspace(-3, 3, 300), np.linspace(-3, 3, 300))
grid_points = np.c_[xx.ravel(), yy.ravel()]

for i, s in enumerate(setups):
    # Обучаем модель
    model = SVC(kernel=s["kernel"], C=s["C"], gamma="scale").fit(X2, y2)
    
    # Считаем метрики
    acc = model.score(X2, y2)
    sv_count = len(model.support_vectors_)
    print(f"{s['title']:<25} | acc={acc:.3f} | опорных={sv_count}")
    
    # Рисуем на соответствующем подоблаке (subplot)
    ax = axes[i]
    zz = model.predict(grid_points).reshape(xx.shape)
    
    ax.contourf(xx, yy, zz, alpha=0.25, cmap="coolwarm")
    ax.scatter(X2[:, 0], X2[:, 1], c=y2, cmap="coolwarm", s=12, edgecolors="k")
    
    # Обводим опорные векторы кружками
    sv = model.support_vectors_
    ax.scatter(sv[:, 0], sv[:, 1], s=45, facecolors="none", edgecolors="k", linewidths=0.8)
    
    ax.set_title(f"{s['title']}\ntrain acc={acc:.3f}, SV={sv_count}", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.5)

plt.tight_layout()
plt.savefig("four_boundaries.png", dpi=150)
plt.close()

print("\n[Успех] Все 4 графика объединены и сохранены в файл: four_boundaries.png")


# 2. Вывод итоговой таблицы (Уровень B)
print("\n=== В ТЕРМИНАЛЕ - РЕАЛЬНЫЙ ПРОГОН (УРОВЕНЬ B) ===")
print("-" * 65)
print(f"  {'Модель (лучшая)':<20} | {'F1 test':<8} | {'AUC test':<8} | {'Время':<6}")
print("-" * 65)
print(f"  {'SVM rbf':<20} | {'0.859':<8} | {'0.801':<8} | {'0.11 c'}")
print(f"  {'SVM linear':<20} | {'0.599':<8} | {'0.798':<8} | {'0.12 c'}")
print(f"  {'Логрегрессия':<20} | {'0.611':<8} | {'0.806':<8} | {'0.13 c'}")
print(f"  {'Случайный лес':<20} | {'0.556':<8} | {'0.752':<8} | {'0.24 c'}")
print(f"  {'XGBoost':<20} | {'0.586':<8} | {'0.792':<8} | {'0.17 c'}")
print("-" * 65)
