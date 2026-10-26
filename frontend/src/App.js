import React from "react";
import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Header from "./Header";
import Jobs from "./pages/Jobs";
import Resumes from "./pages/Resumes";
import "./App.css";

function App() {
  return (
    <Router>
      <Header />
      <main className="page">
        <Routes>
          <Route path="/jobs" element={<Jobs />} />
          <Route path="/resumes" element={<Resumes />} />
          <Route path="*" element={<Navigate to="/jobs" replace />} />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
