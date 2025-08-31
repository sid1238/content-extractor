import React, { useState } from "react";
import Header from "../src/Header";

function FindMatch() {
  const user = JSON.parse(localStorage.getItem("user")) || { first_name: "User", last_name: "" };
  const [jobUrl, setJobUrl] = useState("");
  const [resume, setResume] = useState(null);

  const handleUpload = (e) => setResume(e.target.files[0]);

  return (
    <div>
      <Header firstName={user.first_name} lastName={user.last_name} />
      <h2>Find Match</h2>
      <form>
        <input
          type="text"
          placeholder="Enter Job ID URL"
          value={jobUrl}
          onChange={(e) => setJobUrl(e.target.value)}
        />
        <br />
        <input type="file" accept=".pdf,.docx" onChange={handleUpload} />
      </form>
    </div>
  );
}

export default FindMatch;