import React, { useEffect } from "react";
import { useNavigate } from "react-router-dom";

function LogoutPage() {
  const navigate = useNavigate();

  useEffect(() => {
    // Clear user session (if you later add JWT/localStorage)
    localStorage.removeItem("user");
    navigate("/login");
  }, [navigate]);

  return <p>Logging out...</p>;
}

export default LogoutPage;