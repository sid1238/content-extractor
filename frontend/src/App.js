import React from 'react';
import UploadForm from './UploadForm';
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import Signup from "./Signup";
import Login from "./Login";
import ProfileForm from "./ProfileForm";

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Login />} />
        <Route path="/signup" element={<Signup />} />
        <Route path="/profile" element={<ProfileForm />} />
        <Route path="/upload" element={<UploadForm />} />
      </Routes>
    </Router>
  );
}

export default App;