import React from "react";

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

function TextList({ title, note, items }) {
  if (items.length === 0) return null;
  return (
    <section className="ats-section">
      <div className="ats-section-head">
        <h4>{title}</h4>
        <span className="ats-section-state">{items.length}</span>
      </div>
      {note && <p className="ats-note">{note}</p>}
      <ul className="change-list">
        {items.map((item) => <li key={item} className="change-item"><p>{item}</p></li>)}
      </ul>
    </section>
  );
}

function TailorResult({ result }) {
  const { job, experience, changes, kept, removed, added_skills: added, missing_skills: missing, needs_metric: needsMetric } = result;
  const experienceShort = experience.met === false;

  return (
    <div className="ats-report">
      <div className="ats-report-head">
        <h3>Your tailored resume is ready</h3>
        <p className="ats-note">{job.title || "Job posting"}{job.company ? ` · ${job.company}` : ""}</p>
        <div className="tailor-summary">
          <span className="sev sev-clear">1 page</span>
          {result.match_before !== null && result.match_after !== null && (
            <span className="sev sev-info">Match {result.match_before}% → {result.match_after}%</span>
          )}
          <span className="sev sev-info">{plural(changes.length, "change")}</span>
        </div>
        <p className="ats-note">Check every change below before you send this. The AI can subtly change what a line means.</p>
      </div>

      <section className="ats-section">
        <div className="ats-section-head">
          <h4>What changed</h4>
          <span className="ats-section-state">{plural(changes.length, "change")}</span>
        </div>
        <ul className="change-list">
          {changes.map((change) => (
            <li key={change.before} className="change-item">
              <p className="change-before">{change.before}</p>
              <p className="change-after">{change.after}</p>
            </li>
          ))}
        </ul>
      </section>

      {kept.length > 0 && (
        <section className="ats-section">
          <div className="ats-section-head">
            <h4>Left as written</h4>
            <span className="ats-section-state">{kept.length}</span>
          </div>
          <p className="ats-note">The AI's versions of these lines failed the accuracy checks, so your original wording was kept.</p>
          <ul className="change-list">
            {kept.map((item) => (
              <li key={item.text} className="change-item">
                <p>{item.text}</p>
                <p className="change-reason">The AI's last attempt {item.reason}.</p>
              </li>
            ))}
          </ul>
        </section>
      )}

      <TextList
        title="Removed to fit one page"
        note="These were the lines least related to this job."
        items={removed}
      />
      <TextList
        title="Lines with no number yet"
        note="Numbers are never invented. If you can back up a result for any of these, add it under Real results and generate again."
        items={needsMetric}
      />
      <TextList
        title="Skills added"
        note="The job asks for these, and your resume or notes already show them elsewhere."
        items={added}
      />
      <TextList
        title="Job skills not added"
        note="The job asks for these, but nothing in your resume shows them. If you do have one, add it under Real results and generate again."
        items={missing}
      />

      {experienceShort && (
        <p className="ats-note">
          This job asks for {experience.required_years}+ years of experience, and your resume shows {experience.resume_years ?? "none"}. Your experience was not changed.
        </p>
      )}
    </div>
  );
}

export default TailorResult;
