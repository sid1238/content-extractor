import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Header from "./Header";
import Application from "./pages/Application";
import FindMatch from "./pages/FindMatch";
import Profile from "./pages/Profile";
import Resumes from "./pages/Resumes";
import "./App.css";

function App() {
  return (
    <Router>
      <Header />
      <main className="page">
        <Routes>
          <Route path="/application" element={<Application />} />
          <Route path="/find-match" element={<FindMatch />} />
          <Route path="/profile" element={<Profile />} />
          <Route path="/resumes" element={<Resumes />} />
          <Route path="*" element={<Navigate to="/find-match" replace />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
