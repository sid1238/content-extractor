import React from "react";
import { NavLink } from "react-router-dom";

function Header() {
  return (
    <header className="topbar">
      <div className="topbar-inner">
        <NavLink to="/find-match" className="brand">
          <span className="brand-mark">CE</span>
          Content Extractor
        </NavLink>
        <nav className="topbar-nav">
          <NavLink to="/application" className="nav-link">Application</NavLink>
          <NavLink to="/find-match" className="nav-link">Find Match</NavLink>
          <NavLink to="/profile" className="nav-link">Profile</NavLink>
          <NavLink to="/resumes" className="nav-link">Resumes</NavLink>
        </nav>
      </div>
    </header>
  );
}

export default Header;
