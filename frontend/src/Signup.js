import React, { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import axios from "axios";

function SignupPage() {
  const [form, setForm] = useState({
    first_name: "", last_name: "", email: "", password: "", confirm_password: "",
    address: "", city: "", state: "", country: "", pincode: "",
    education: "", work_experience: "",
    authorized: "", sponsorship: "", gender: "", community: "", veteran: ""
  });

  const navigate = useNavigate();

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (form.password !== form.confirm_password) {
      alert("Passwords do not match!");
      return;
    }
    try {
      await axios.post("http://127.0.0.1:5000/signup", form);
      alert("Signup successful!");
      navigate("/login");
    } catch (err) {
      alert("Signup failed.");
    }
  };

  return (
    <div>
      <h2>Sign Up</h2>
      <form onSubmit={handleSubmit}>
        <input type="text" name="first_name" placeholder="First Name" onChange={handleChange} />
        <input type="text" name="last_name" placeholder="Last Name" onChange={handleChange} />
        <input type="email" name="email" placeholder="Email" onChange={handleChange} />
        <input type="password" name="password" placeholder="Password" onChange={handleChange} />
        <input type="password" name="confirm_password" placeholder="Confirm Password" onChange={handleChange} />
        <input type="text" name="address" placeholder="Address" onChange={handleChange} />
        <input type="text" name="city" placeholder="City" onChange={handleChange} />
        <input type="text" name="state" placeholder="State" onChange={handleChange} />
        <input type="text" name="country" placeholder="Country" onChange={handleChange} />
        <input type="text" name="pincode" placeholder="Pincode" onChange={handleChange} />
        <input type="text" name="education" placeholder="Education" onChange={handleChange} />
        <input type="text" name="work_experience" placeholder="Work Experience" onChange={handleChange} />
        <input type="text" name="authorized" placeholder="Legally authorized to work?" onChange={handleChange} />
        <input type="text" name="sponsorship" placeholder="Require sponsorship?" onChange={handleChange} />
        <input type="text" name="gender" placeholder="Gender" onChange={handleChange} />
        <input type="text" name="community" placeholder="Community" onChange={handleChange} />
        <input type="text" name="veteran" placeholder="Protected veteran?" onChange={handleChange} />
        <button type="submit">Sign Up</button>
      </form>
      <p>
        Already have an account? <Link to="/login">Login here</Link>
      </p>
    </div>
  );
}

export default SignupPage;
