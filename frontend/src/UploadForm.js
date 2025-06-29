import React, { useState } from 'react';
import axios from 'axios';

function UploadForm() {
  const [file, setFile] = useState(null);
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setFile(e.target.files[0]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await axios.post("http://localhost:5000/upload", formData);
      setQuestions(response.data.questions || []);
    } catch (err) {
      alert("Upload failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="container">
      <h2>Upload File</h2>
      <form onSubmit={handleSubmit}>
        <input type="file" accept=".pdf,.docx,.txt" onChange={handleChange} />
        <button type="submit">Upload</button>
      </form>

      {loading && <p>Generating questions...</p>}

      {questions.length > 0 && (
        <div>
          <h3>Generated Questions:</h3>
          <ul>
            {questions.map((q, idx) => <li key={idx}>{q}</li>)}
          </ul>
        </div>
      )}
    </div>
  );
}

export default UploadForm;