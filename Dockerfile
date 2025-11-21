# Python 3.10-slim 이미지를 기반으로 합니다.
FROM python:3.9

# 작업 디렉토리를 /app으로 설정합니다.
WORKDIR /app

# 현재 디렉토리의 모든 파일을 /app으로 복사합니다.
COPY . /app

# requirements.txt에 명시된 패키지들을 설치합니다.
RUN pip install --no-cache-dir -r requirements.txt

# 8000번 포트를 외부에 노출합니다.
EXPOSE 8000

# 애플리케이션을 실행합니다.
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
