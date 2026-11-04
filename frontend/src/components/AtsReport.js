import React from "react";

const SEVERITY_LABELS = { critical: "Critical", warning: "Warning", info: "Suggestion" };

const plural = (count, word) => `${count} ${word}${count === 1 ? "" : "s"}`;

function SectionState({ section }) {
  if (section.status === "ok") return <span className="ats-section-state ok">✓ No issues found</span>;
  if (section.status === "unavailable") return <span className="ats-section-state">Not checked</span>;
  if (section.status === "skipped") return <span className="ats-section-state">Not checked</span>;
  return <span className="ats-section-state">{plural(section.findings.length, "issue")}</span>;
}

function ExperienceBalance({ jobs }) {
  return (
    <ul className="balance-list">
      {jobs.map((job) => (
        <li key={`${job.title}-${job.company}-${job.dates}`}>
          <div className="balance-top">
            <span>
              <strong>{job.title || job.company || "Job"}</strong>
              {job.title && job.company ? ` · ${job.company}` : ""}
              {job.is_latest && <span className="balance-tag">{job.is_current ? "Current" : "Most recent"}</span>}
              {job.related === false && <span className="balance-tag unrelated">Looks unrelated</span>}
            </span>
            <span className="balance-meta">{job.dates} · {job.share}% of experience ({plural(job.words, "word")})</span>
          </div>
          <div className="balance-track">
            <div className={`balance-fill${job.related === false ? " unrelated" : ""}`} style={{ width: `${job.share}%` }} />
          </div>
        </li>
      ))}
    </ul>
  );
}

function AtsReport({ report }) {
  const { summary, sections, experience_breakdown: jobs } = report;
  const total = summary.critical + summary.warning + summary.info;
  const allChecked = sections.every((s) => s.status === "ok" || s.status === "issues");

  return (
    <div className="ats-report">
      <div className="ats-report-head">
        <h3>ATS scan results</h3>
        <div className="ats-summary">
          {total === 0 && (
            <span className="sev sev-clear">{allChecked ? "No red flags found" : "No red flags in the checks that ran"}</span>
          )}
          {summary.critical > 0 && <span className="sev sev-critical">{summary.critical} critical</span>}
          {summary.warning > 0 && <span className="sev sev-warning">{plural(summary.warning, "warning")}</span>}
          {summary.info > 0 && <span className="sev sev-info">{plural(summary.info, "suggestion")}</span>}
        </div>
      </div>

      {sections.map((section) => (
        <section key={section.id} className="ats-section">
          <div className="ats-section-head">
            <h4>{section.title}</h4>
            <SectionState section={section} />
          </div>
          {section.note && <p className="ats-note">{section.note}</p>}
          {section.findings.length > 0 && (
            <ul className="ats-findings">
              {section.findings.map((finding, i) => (
                <li key={`${finding.message}-${i}`} className="ats-finding">
                  <span className={`sev sev-${finding.severity}`}>{SEVERITY_LABELS[finding.severity]}</span>
                  <div className="ats-finding-body">
                    <p>{finding.message}</p>
                    {finding.suggestion && <p className="ats-suggestion">{finding.suggestion}</p>}
                    {finding.snippet && <p className="ats-snippet">{finding.snippet}</p>}
                  </div>
                </li>
              ))}
            </ul>
          )}
          {section.id === "balance" && jobs.length > 0 && <ExperienceBalance jobs={jobs} />}
        </section>
      ))}

      <p className="match-footnote">
        These are automated checks. They can miss mistakes or flag correct wording, and each ATS reads resumes differently, so review each item yourself.
      </p>
    </div>
  );
}

export default AtsReport;
