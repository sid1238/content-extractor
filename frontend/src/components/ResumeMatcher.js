import React, { useRef, useState } from "react";
import axios from "axios";
import AtsReport from "./AtsReport";

const API_BASE = process.env.REACT_APP_API_URL || "http://127.0.0.1:5000";
const ACCEPTED = [".pdf", ".docx"];
const MAX_FILE_BYTES = 2 * 1024 * 1024;

const isValidUrl = (value) => {
  try {
    const url = new URL(value);
    return url.protocol === "http:" || url.protocol === "https:";
  } catch {
    return false;
  }
};

const scoreTone = (pct) => (pct >= 75 ? "good" : pct >= 50 ? "fair" : "poor");

const formatYears = (y) => (y === null || y === undefined ? "Not found" : `${y} ${y === 1 ? "year" : "years"}`);

function ScoreRing({ value }) {
  const radius = 52;
  const circumference = 2 * Math.PI * radius;
  return (
    <div className={`score-ring tone-${scoreTone(value)}`}>
      <svg viewBox="0 0 120 120" aria-hidden="true">
        <circle className="ring-track" cx="60" cy="60" r={radius} />
        <circle
          className="ring-value"
          cx="60"
          cy="60"
          r={radius}
          strokeDasharray={circumference}
          strokeDashoffset={circumference * (1 - value / 100)}
        />
      </svg>
      <div className="score-ring-label">
        <strong>{value}%</strong>
        <span>match</span>
      </div>
    </div>
  );
}

function MatchResult({ result }) {
  const { skills, experience, job } = result;
  const expRequired = experience.required_years;

  return (
    <div className="match-result">
      <div className="match-summary">
        {result.match_percentage === null ? (
          <div className="score-ring-empty">No skills or experience requirements found in this posting.</div>
        ) : (
          <ScoreRing value={result.match_percentage} />
        )}
        <div className="match-summary-text">
          <h3>{job.title || "Job posting"}</h3>
          {job.company && <p className="job-company">{job.company}</p>}
          <a href={job.url} target="_blank" rel="noreferrer" className="match-link">View job posting ↗</a>
          <div className="match-breakdown">
            <span>Skills <strong>{skills.score === null ? "—" : `${skills.score}%`}</strong></span>
            <span>Experience <strong>{experience.score === null ? "—" : `${experience.score}%`}</strong></span>
          </div>
        </div>
      </div>

      <div className="match-columns">
        <div className="match-col">
          <h4 className="match-col-title good">✓ What matched</h4>
          {skills.matched.length > 0 ? (
            <ul className="chips">
              {skills.matched.map((s) => <li key={s} className="chip chip-have">{s}</li>)}
            </ul>
          ) : (
            <p className="muted">None of the required skills were found in your resume.</p>
          )}
          {experience.met && (
            <p className="exp-line good">
              Experience: you have {formatYears(experience.resume_years)}, the job asks for {expRequired}+.
            </p>
          )}
        </div>

        <div className="match-col">
          <h4 className="match-col-title poor">✕ What did not match</h4>
          {skills.missing.length > 0 ? (
            <ul className="chips">
              {skills.missing.map((s) => <li key={s} className="chip chip-missing">{s}</li>)}
            </ul>
          ) : (
            <p className="muted">{skills.required.length ? "You have every skill the job lists." : "The posting lists no recognisable skills."}</p>
          )}
          {experience.met === false && (
            <p className="exp-line poor">
              Experience: the job asks for {expRequired}+ years, your resume shows {formatYears(experience.resume_years)}.
            </p>
          )}
        </div>
      </div>

      <p className="match-footnote">
        {expRequired === null
          ? "The posting doesn't state a years-of-experience requirement, so the score is based on skills only."
          : `Your experience was ${experience.resume_years_source}.`}
        {result.extra_skills.length > 0 && ` Other skills on your resume: ${result.extra_skills.join(", ")}.`}
      </p>
    </div>
  );
}

function ResumeMatcher() {
  const [file, setFile] = useState(null);
  const [jobUrl, setJobUrl] = useState("");
  const [dragging, setDragging] = useState(false);
  const [loading, setLoading] = useState(false);
  const [scanning, setScanning] = useState(false);
  const [error, setError] = useState("");
  const [result, setResult] = useState(null);
  const [report, setReport] = useState(null);
  const inputRef = useRef(null);

  const urlOk = isValidUrl(jobUrl.trim());
  const busy = loading || scanning;
  const canStart = Boolean(file) && urlOk && !busy;
  const canScan = Boolean(file) && !busy;

  const pickFile = (picked) => {
    if (!picked) return;
    const ext = picked.name.slice(picked.name.lastIndexOf(".")).toLowerCase();
    if (ext === ".doc") {
      setError("Older .doc files aren't supported. In Word, use Save As to make a .docx copy.");
      return;
    }
    if (!ACCEPTED.includes(ext)) {
      setError("Upload your resume as a PDF or Word (.docx) file.");
      return;
    }
    if (picked.size > MAX_FILE_BYTES) {
      setError("Your resume is larger than the 2 MB limit.");
      return;
    }
    setError("");
    setResult(null);
    setReport(null);
    setFile(picked);
  };

  const startMatch = async () => {
    if (!canStart) return;
    setLoading(true);
    setError("");
    setResult(null);
    const form = new FormData();
    form.append("resume", file);
    form.append("job_url", jobUrl.trim());
    try {
      const { data } = await axios.post(`${API_BASE}/match`, form);
      setResult(data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not reach the matching server. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  const startScan = async () => {
    if (!canScan) return;
    setScanning(true);
    setError("");
    setReport(null);
    const form = new FormData();
    form.append("resume", file);
    try {
      const { data } = await axios.post(`${API_BASE}/ats-scan`, form);
      setReport(data);
    } catch (err) {
      setError(err.response?.data?.error || "Could not reach the server. Is the backend running?");
    } finally {
      setScanning(false);
    }
  };

  return (
    <div className="card matcher">
      <div className="matcher-head">
        <h2>Check your resume</h2>
        <p>Upload your resume to scan it for ATS red flags, or add a job link to see how well you fit the role.</p>
      </div>

      <div className="matcher-inputs">
        <div
          className={`dropzone${dragging ? " dragging" : ""}${file ? " has-file" : ""}`}
          onClick={() => inputRef.current.click()}
          onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(e) => { e.preventDefault(); setDragging(false); pickFile(e.dataTransfer.files[0]); }}
          role="button"
          tabIndex={0}
          onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current.click()}
        >
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED.join(",")}
            hidden
            onChange={(e) => { pickFile(e.target.files[0]); e.target.value = ""; }}
          />
          <span className="dropzone-icon">{file ? "📄" : "⬆"}</span>
          {file ? (
            <span className="dropzone-text">
              <strong>{file.name}</strong>
              <span>Click to replace</span>
            </span>
          ) : (
            <span className="dropzone-text">
              <strong>Upload resume</strong>
              <span>Drag a file here or click · PDF or Word (.docx), up to 2 MB</span>
            </span>
          )}
        </div>

        <label className="url-field">
          <span className="label">Job URL</span>
          <input
            type="url"
            placeholder="https://company.com/careers/job/123"
            value={jobUrl}
            onChange={(e) => { setJobUrl(e.target.value); setResult(null); }}
            onKeyDown={(e) => e.key === "Enter" && startMatch()}
          />
          {jobUrl && !urlOk && <span className="field-hint">Enter a full link starting with http:// or https://</span>}
        </label>

        <div className="matcher-actions">
          <button className="btn-primary" onClick={startMatch} disabled={!canStart}>
            {loading ? <><span className="spinner" /> Matching…</> : "Start match"}
          </button>
          <button className="btn-secondary" onClick={startScan} disabled={!canScan}>
            {scanning ? <><span className="spinner spinner-dark" /> Scanning…</> : "Scan for ATS issues"}
          </button>
        </div>
      </div>

      {scanning ? (
        <p className="matcher-hint">Checking your resume. The first scan takes longer while the spelling and grammar checker starts.</p>
      ) : !file ? (
        <p className="matcher-hint">Upload a resume to start. The match also needs a job URL.</p>
      ) : !urlOk ? (
        <p className="matcher-hint">You can scan your resume now. Enter a job URL to start a match.</p>
      ) : null}

      {error && <div className="matcher-error">{error}</div>}
      {result && <MatchResult result={result} />}
      {report && <AtsReport report={report} />}
    </div>
  );
}

export default ResumeMatcher;
