import React from "react";
import Header from "../src/Header";

function Application() {
  // fetch user details from localStorage (set at login/signup)
  const user = JSON.parse(localStorage.getItem("user")) || { first_name: "User", last_name: "" };

  return (
    <div>
      <Header firstName={user.first_name} lastName={user.last_name} />
      <h2>Application Page</h2>
      <p>All your application fields go here...</p>
    </div>
  );
}

export default Application;