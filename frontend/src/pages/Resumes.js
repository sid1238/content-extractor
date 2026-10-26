import React, { useEffect, useState } from "react";
import resumes from "../data/resumes";

function ResumeDocument({ resume }) {
  return (
    <div className="resume-doc">
      <header className="resume-header">
        <h2>{resume.name}</h2>
        <p className="resume-title">{resume.title}</p>
        <p className="resume-contact">
          {resume.email} · {resume.phone} · {resume.location}
        </p>
      </header>

      <h3>Summary</h3>
      <p>{resume.summary}</p>

      <h3>Experience</h3>
      {resume.experience.map((job) => (
        <div key={job.company} className="resume-job">
          <div className="resume-job-head">
            <strong>{job.role} — {job.company}</strong>
            <span>{job.period}</span>
          </div>
          <ul>
            {job.bullets.map((b) => (
              <li key={b}>{b}</li>
            ))}
          </ul>
        </div>
      ))}

      <h3>Skills</h3>
      <p>{resume.skills.join(" · ")}</p>

      <h3>Education</h3>
      <p>{resume.education}</p>
    </div>
  );
}

function Resumes() {
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    if (!selected) return;
    const onKey = (e) => e.key === "Escape" && setSelected(null);
    document.addEventListener("keydown", onKey);
    document.body.style.overflow = "hidden";
    return () => {
      document.removeEventListener("keydown", onKey);
      document.body.style.overflow = "";
    };
  }, [selected]);

  return (
    <section>
      <div className="page-head">
        <h1>Resumes</h1>
        <p>{resumes.length} sample resumes · click one to view it full size</p>
      </div>
      <div className="card-grid">
        {resumes.map((resume) => (
          <button
            key={resume.id}
            className="card resume-card"
            onClick={() => setSelected(resume)}
          >
            <div className="resume-thumb">
              <div className="resume-thumb-inner">
                <ResumeDocument resume={resume} />
              </div>
            </div>
            <div className="resume-card-foot">
              <strong>{resume.name}</strong>
              <span>{resume.title} · {resume.years}+ yrs</span>
            </div>
          </button>
        ))}
      </div>

      {selected && (
        <div className="modal-backdrop" onClick={() => setSelected(null)}>
          <div
            className="modal"
            role="dialog"
            aria-modal="true"
            aria-label={`Resume of ${selected.name}`}
            onClick={(e) => e.stopPropagation()}
          >
            <button className="modal-close" onClick={() => setSelected(null)} aria-label="Close">
              ×
            </button>
            <ResumeDocument resume={selected} />
          </div>
        </div>
      )}
    </section>
  );
}

export default Resumes;
