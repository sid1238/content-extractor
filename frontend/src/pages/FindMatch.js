import React from "react";
import jobs from "../data/jobs";

function FindMatch() {
  return (
    <section>
      <div className="page-head">
        <h1>Find Match</h1>
        <p>{jobs.length} open roles</p>
      </div>
      <div className="card-grid">
        {jobs.map((job) => (
          <article key={job.id} className="card job-card">
            <div className="job-top">
              <div className="avatar">{job.company[0]}</div>
              <div>
                <h2 className="job-role">{job.role}</h2>
                <p className="job-company">{job.company}</p>
              </div>
            </div>
            <dl className="job-meta">
              <div>
                <dt>Experience</dt>
                <dd>{job.experience}</dd>
              </div>
              <div>
                <dt>Location</dt>
                <dd>{job.location}</dd>
              </div>
            </dl>
            <div>
              <p className="label">Skills required</p>
              <ul className="chips">
                {job.skills.map((skill) => (
                  <li key={skill} className="chip">{skill}</li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default FindMatch;
