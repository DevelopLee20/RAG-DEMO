# RAG-DEMO

FastAPI와 React를 사용하는 간단한 RAG(Retrieval-Augmented Generation) 데모입니다.

## 실행 방법

### 백엔드 (FastAPI)

1.  **프로젝트 루트 디렉토리로 이동합니다:**
    ```bash
    cd RAG-DEMO
    ```

2.  **Pipenv를 사용하여 의존성을 설치합니다:**
    ```bash
    pipenv install
    ```

3.  **가상 환경을 활성화합니다:**
    ```bash
    pipenv shell
    ```

4.  **백엔드 서버를 실행합니다:**
    서버가 `http://127.0.0.1:8000`에서 시작됩니다.
    ```bash
    uvicorn main:app --reload
    ```

### 프론트엔드 (React)

1.  **프론트엔드 디렉토리로 이동합니다:**
    ```bash
    cd frontend
    ```

2.  **의존성을 설치합니다:**
    ```bash
    npm install
    ```

3.  **프론트엔드 개발 서버를 실행합니다:**
    React 앱이 `http://localhost:3000`에서 시작됩니다.
    ```bash
    npm start
    ```