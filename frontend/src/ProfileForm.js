import React, { useState } from "react";
import axios from "axios";

function ProfileForm() {
  const [form, setForm] = useState({});
  const email = localStorage.getItem("userEmail");

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const autoFill = async () => {
    const res = await axios.get(`http://localhost:5000/profile/${email}`);
    setForm(res.data);
  };

  return (
    <div>
      <h2>Profile Form</h2>
      <button onClick={autoFill}>Fill Automatically</button>
      <form>
        <input name="first_name" placeholder="First Name" value={form.first_name || ""} onChange={handleChange} />
        <input name="last_name" placeholder="Last Name" value={form.last_name || ""} onChange={handleChange} />
        <input name="email" placeholder="Email" value={form.email || ""} onChange={handleChange} />
        <input name="address" placeholder="Address" value={form.address || ""} onChange={handleChange} />
        <input name="city" placeholder="City" value={form.city || ""} onChange={handleChange} />
        <input name="state" placeholder="State" value={form.state || ""} onChange={handleChange} />
        <input name="country" placeholder="Country" value={form.country || ""} onChange={handleChange} />
        <input name="pincode" placeholder="Pincode" value={form.pincode || ""} onChange={handleChange} />
        <input name="education" placeholder="Education" value={form.education || ""} onChange={handleChange} />
        <input name="work_experience" placeholder="Work Experience" value={form.work_experience || ""} onChange={handleChange} />
        {/* add other fields here similarly */}
      </form>
    </div>
  );
}

export default ProfileForm;