import React, { useState } from "react";
import axios from "axios";

function Signup() {
  const [form, setForm] = useState({});
  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const handleSubmit = async (e) => {
    e.preventDefault();
    await axios.post("http://localhost:5000/signup", form);
    alert("Signup successful!");
  };

  return (
    <form onSubmit={handleSubmit}>
      <h2>Signup</h2>
      <input name="first_name" placeholder="First Name" onChange={handleChange} required />
      <input name="last_name" placeholder="Last Name" onChange={handleChange} required />
      <input name="email" type="email" placeholder="Email" onChange={handleChange} required />
      <input name="password" type="password" placeholder="Password" onChange={handleChange} required />
      <input name="address" placeholder="Address" onChange={handleChange} />
      <input name="city" placeholder="City" onChange={handleChange} />
      <input name="state" placeholder="State" onChange={handleChange} />
      <input name="country" placeholder="Country" onChange={handleChange} />
      <input name="pincode" placeholder="Pincode" onChange={handleChange} />
      <input name="education" placeholder="Education" onChange={handleChange} />
      <input name="work_experience" placeholder="Work Experience" onChange={handleChange} />
      <select name="authorized_work" onChange={handleChange}>
        <option value="">Authorized to work?</option>
        <option value="1">Yes</option>
        <option value="0">No</option>
      </select>
      <select name="sponsorship_required" onChange={handleChange}>
        <option value="">Require sponsorship?</option>
        <option value="1">Yes</option>
        <option value="0">No</option>
      </select>
      <input name="gender" placeholder="Gender" onChange={handleChange} />
      <input name="community" placeholder="Community" onChange={handleChange} />
      <select name="protected_veteran" onChange={handleChange}>
        <option value="">Protected Veteran?</option>
        <option value="1">Yes</option>
        <option value="0">No</option>
      </select>
      <button type="submit">Signup</button>
    </form>
  );
}

export default Signup;