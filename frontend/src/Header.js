import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";

function Header({ firstName, lastName }) {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/login");
  };

  return (
    <header style={styles.header}>
      <div style={styles.navLeft}>
        <Link to="/application" style={styles.link}>Application</Link>
        <Link to="/find-match" style={styles.link}>Find Match</Link>
        <Link to="/profile" style={styles.link}>Profile</Link>
      </div>
      <div style={styles.navRight}>
        <span onClick={() => setOpen(!open)} style={styles.dropdownToggle}>
          {firstName} {lastName} ▼
        </span>
        {open && (
          <div style={styles.dropdownMenu}>
            <button onClick={handleLogout} style={styles.dropdownItem}>Logout</button>
          </div>
        )}
      </div>
    </header>
  );
}

const styles = {
  header: { display: "flex", justifyContent: "space-between", alignItems: "center", padding: "10px 20px", background: "#eee" },
  navLeft: { display: "flex", gap: "20px" },
  link: { textDecoration: "none", color: "black", fontWeight: "bold" },
  navRight: { position: "relative" },
  dropdownToggle: { cursor: "pointer", fontWeight: "bold" },
  dropdownMenu: { position: "absolute", top: "100%", right: 0, background: "#fff", border: "1px solid #ccc", padding: "10px" },
  dropdownItem: { background: "none", border: "none", cursor: "pointer", fontSize: "14px" }
};

export default Header;