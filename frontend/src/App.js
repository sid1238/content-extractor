import React from 'react';
import UploadForm from './UploadForm';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Signup from "./Signup";
import Login from "./Login";
import Application from "./Application";
import FindMatch from "./FindMatch";
import Profile from "./Profile";
import LogoutPage from "./LogoutPage";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/login" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/application" element={<Application />} />
        <Route path="/find-match" element={<FindMatch />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/upload" element={<UploadForm />} />
        <Route path="/logout" element={<LogoutPage />} />
      </Routes>
    </Router>
  );
}

export default App;