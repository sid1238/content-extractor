import React, { useState } from "react";
import Header from "../src/Header";
function Application() {
  // fetch user details from localStorage (set at login/signup)
  const user = JSON.parse(localStorage.getItem("user")) || { first_name: "User", last_name: "" };
  const [firstName, setfirstName] = useState("");
  const [lastName, setlastName] = useState("");
  const [Email, setEmail] = useState("");
  const [workExp, setWorkExp] = useState("");
  const [education, setEducation] = useState("");


  return (
    <div>
      <Header firstName={user.first_name} lastName={user.last_name} />
      <h2>Application Page</h2>
      <p>All your application fields go here...</p>
      <form>
        <label>First Name</label><br />
        <textarea value={firstName} onChange={(e) => setfirstName(e.target.value)} /><br />
        <label>Last Name</label><br />
        <textarea value={lastName} onChange={(e) => setlastName(e.target.value)} /><br />
        <label>Email</label><br />
        <textarea value={Email} onChange={(e) => setEmail(e.target.value)} /><br />
        <label>Work Experience</label><br />
        <textarea value={workExp} onChange={(e) => setWorkExp(e.target.value)} /><br />
        <label>Education</label><br />
        <textarea value={education} onChange={(e) => setEducation(e.target.value)} /><br />
      </form>
    </div>
  );
}

export default Application;