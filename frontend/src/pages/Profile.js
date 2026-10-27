import React from "react";
import profile from "../data/profile";

const initials = (name) => name.split(" ").map((n) => n[0]).join("");

function Profile() {
  return (
    <section className="profile">
      <div className="page-head">
        <h1>Profile</h1>
        <p>Your personal details</p>
      </div>

      <div className="card profile-card">
        <div className="profile-hero">
          <div className="profile-avatar">{initials(profile.name)}</div>
          <div>
            <h2>{profile.name}</h2>
            <p>{profile.currentTitle} · {profile.location}</p>
          </div>
        </div>

        <dl className="profile-grid">
          <div>
            <dt>Full name</dt>
            <dd>{profile.name}</dd>
          </div>
          <div>
            <dt>Email ID</dt>
            <dd>{profile.email}</dd>
          </div>
          <div>
            <dt>Phone</dt>
            <dd>{profile.phone}</dd>
          </div>
          <div>
            <dt>Years of experience</dt>
            <dd>{profile.yearsOfExperience} years</dd>
          </div>
        </dl>

        <div className="profile-section">
          <p className="label">Interested roles</p>
          <ul className="chips">
            {profile.interestedRoles.map((role) => (
              <li key={role} className="chip">{role}</li>
            ))}
          </ul>
        </div>

        <div className="profile-section">
          <p className="label">Skills</p>
          <ul className="chips">
            {profile.skills.map((skill) => (
              <li key={skill} className="chip chip-neutral">{skill}</li>
            ))}
          </ul>
        </div>
      </div>
    </section>
  );
}

export default Profile;
