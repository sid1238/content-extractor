import React from "react";
import jobs from "../data/jobs";
import applications from "../data/applications";
import profile from "../data/profile";

const statusClass = {
  Applied: "status-applied",
  "Under review": "status-review",
  Interviewing: "status-interview",
  Offer: "status-offer",
  Rejected: "status-rejected",
};

const formatDate = (iso) =>
  new Date(iso + "T00:00:00").toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });

// Share of a job's required skills the user has, plus a bonus for roles they're interested in.
function matchScore(job) {
  const have = job.skills.filter((s) => profile.skills.includes(s)).length;
  const skillScore = (have / job.skills.length) * 80;
  const roleBonus = profile.interestedRoles.includes(job.role) ? 20 : 0;
  return Math.round(skillScore + roleBonus);
}

function Application() {
  const appliedIds = new Set(applications.map((a) => a.jobId));
  const applied = applications.map((a) => ({ ...a, job: jobs.find((j) => j.id === a.jobId) }));
  const matches = jobs
    .filter((job) => !appliedIds.has(job.id))
    .map((job) => ({ job, score: matchScore(job) }))
    .filter((m) => m.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, 6);

  return (
    <section>
      <div className="page-head">
        <h1>Application</h1>
        <p>Track the jobs you have applied to and discover roles that fit your profile</p>
      </div>

      <h2 className="section-title">Applied jobs <span className="count">{applied.length}</span></h2>
      <div className="card applied-list">
        {applied.map(({ job, appliedOn, status }) => (
          <div key={job.id} className="applied-row">
            <div className="avatar">{job.company[0]}</div>
            <div className="applied-main">
              <strong>{job.role}</strong>
              <span>{job.company} · {job.location}</span>
            </div>
            <span className="applied-date">Applied {formatDate(appliedOn)}</span>
            <span className={`status ${statusClass[status]}`}>{status}</span>
          </div>
        ))}
      </div>

      <h2 className="section-title">Jobs that match you <span className="count">{matches.length}</span></h2>
      <div className="card-grid">
        {matches.map(({ job, score }) => (
          <article key={job.id} className="card job-card">
            <div className="job-top">
              <div className="avatar">{job.company[0]}</div>
              <div className="job-top-text">
                <h3 className="job-role">{job.role}</h3>
                <p className="job-company">{job.company}</p>
              </div>
              <span className="match-badge">{score}% match</span>
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
                  <li key={skill} className={profile.skills.includes(skill) ? "chip chip-have" : "chip"}>
                    {skill}
                  </li>
                ))}
              </ul>
            </div>
          </article>
        ))}
      </div>
    </section>
  );
}

export default Application;
