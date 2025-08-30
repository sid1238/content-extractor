# content-extractor

1. Install node.js and npm latest version.

2. Create the react app
   npx create-react-app frontend
   cd frontend
   npm install axios

3. Start React app
   npm start

4. Create virtual environment
   python -m venv rag_env
   source rag_env/bin/activate

5. Inside the virtual environment
   Run the command pip install flask python-docx PyPDF2 sentence-transformers faiss-cpu transformers langchain llama-cpp-python flask-cors flask-bcrypt flask-mysql


# General information

1. generator.py is used for generating questions that will be asked based on the resume uploaded.
2. retriever.py is used for extracting the content from the file that is uploaded.


# Tasks

1. We first have to create an account. whatever fields we enter in the signup page will be stored in the database (we will use MariaDB).
2. We login into our account. In that page we create 2 buttons. One which fills the content into our fields based on the content that is stored in database. For the 2nd button we upload the file and based on what we uploaded the contents are filled in ProfileForm.js(use retrieve.py).
3. Once the file is uploaded we will want to generate questions for the resume that has been uploaded(integrate a simple trained model for the tasks). 
