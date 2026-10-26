import React from "react";
import { NavLink } from "react-router-dom";

function Header() {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <NavLink to="/jobs" className="brand">
          <span className="brand-mark">CE</span>
          Content Extractor
        </NavLink>
        <nav className="topbar-nav">
          <NavLink to="/jobs" className="nav-link">Jobs</NavLink>
          <NavLink to="/resumes" className="nav-link">Resumes</NavLink>
        </nav>
      </div>
    </header>
  );
}

export default Header;
