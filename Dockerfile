# Image de déploiement de l'application Taipy « RL-in-GA » (Render, ou tout hôte Docker)
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    TZ=Indian/Antananarivo \
    OPENBLAS_NUM_THREADS=1 \
    HOST=0.0.0.0 \
    PORT=7860 \
    NO_BROWSER=1

# Utilisateur non privilégié (UID 1000)
RUN useradd -m -u 1000 user && mkdir -p /home/user/app && chown user:user /home/user/app
WORKDIR /home/user/app

COPY --chown=user requirements-app.txt .
RUN pip install --no-cache-dir -r requirements-app.txt

COPY --chown=user . .
USER user

EXPOSE 7860
CMD ["python", "app_taipy/main.py"]
