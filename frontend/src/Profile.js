import React, { useState } from "react";
import Header from "../src/Header";

function Profile() {
  const user = JSON.parse(localStorage.getItem("user")) || { first_name: "User", last_name: "" };
  const [workExp, setWorkExp] = useState("");
  const [education, setEducation] = useState("");

  return (
    <div>
      <Header firstName={user.first_name} lastName={user.last_name} />
      <h2>Profile</h2>
      <form>
        <label>Work Experience</label><br />
        <textarea value={workExp} onChange={(e) => setWorkExp(e.target.value)} /><br />
        <label>Education</label><br />
        <textarea value={education} onChange={(e) => setEducation(e.target.value)} />
      </form>
    </div>
  );
}

export default Profile;