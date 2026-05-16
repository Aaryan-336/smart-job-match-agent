"""
UI template for the Smart Job Match Agent.
Minimal, professional design — no framework dependencies.
"""

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Smart Job Match Agent</title>
<meta name="description" content="AI-powered job matching using semantic search and LLM tool calling">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
<style>
*, *::before, *::after { margin: 0; padding: 0; box-sizing: border-box; }

:root {
  --bg: #fafaf9;
  --surface: #ffffff;
  --border: #e7e5e4;
  --border-light: #f5f5f4;
  --text-primary: #1c1917;
  --text-secondary: #57534e;
  --text-muted: #a8a29e;
  --accent: #292524;
  --accent-hover: #44403c;
  --accent-subtle: #f5f5f4;
  --green: #16a34a;
  --green-bg: #f0fdf4;
  --green-border: #bbf7d0;
  --blue: #2563eb;
  --blue-bg: #eff6ff;
  --blue-border: #bfdbfe;
  --amber: #d97706;
  --amber-bg: #fffbeb;
  --red: #dc2626;
  --red-bg: #fef2f2;
  --font-sans: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  --font-mono: 'JetBrains Mono', 'SF Mono', 'Consolas', monospace;
  --radius: 8px;
  --radius-sm: 5px;
  --shadow-sm: 0 1px 2px rgba(0,0,0,0.04);
  --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
  --transition: 150ms ease;
}

body {
  font-family: var(--font-sans);
  background: var(--bg);
  color: var(--text-primary);
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  min-height: 100vh;
}

/* Layout */
.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 24px;
}

/* Header */
.header {
  padding: 48px 0 40px;
  border-bottom: 1px solid var(--border);
}

.header h1 {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}

.header p {
  color: var(--text-secondary);
  font-size: 14px;
  max-width: 480px;
}

.header-meta {
  display: flex;
  gap: 16px;
  margin-top: 16px;
}

.meta-chip {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  background: var(--accent-subtle);
  padding: 3px 10px;
  border-radius: 20px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.meta-chip .dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--green);
  display: inline-block;
}

/* Sections */
.section {
  padding: 32px 0;
}

.section + .section {
  border-top: 1px solid var(--border-light);
}

.section-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: var(--text-muted);
  margin-bottom: 16px;
}

/* Input area */
.input-group {
  position: relative;
}

.input-group textarea {
  width: 100%;
  min-height: 160px;
  padding: 16px;
  font-family: var(--font-sans);
  font-size: 14px;
  line-height: 1.7;
  color: var(--text-primary);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  resize: vertical;
  transition: border-color var(--transition);
  outline: none;
}

.input-group textarea:focus {
  border-color: var(--accent);
}

.input-group textarea::placeholder {
  color: var(--text-muted);
}

.char-count {
  position: absolute;
  bottom: 12px;
  right: 14px;
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  pointer-events: none;
}

/* Buttons */
.actions {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 16px;
}

.btn {
  font-family: var(--font-sans);
  font-size: 13px;
  font-weight: 500;
  padding: 9px 20px;
  border-radius: var(--radius-sm);
  border: none;
  cursor: pointer;
  transition: all var(--transition);
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.btn-primary {
  background: var(--accent);
  color: #fff;
}

.btn-primary:hover { background: var(--accent-hover); }
.btn-primary:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.btn-ghost {
  background: transparent;
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.btn-ghost:hover { background: var(--accent-subtle); }

.btn .spinner {
  width: 14px;
  height: 14px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* Status */
.status-bar {
  margin-top: 12px;
  font-size: 13px;
  color: var(--text-secondary);
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 20px;
}

.status-bar.error { color: var(--red); }

.pipeline-steps {
  display: flex;
  gap: 6px;
  margin-top: 12px;
  flex-wrap: wrap;
}

.step-tag {
  font-size: 11px;
  font-family: var(--font-mono);
  padding: 3px 10px;
  border-radius: 20px;
  background: var(--accent-subtle);
  color: var(--text-muted);
  border: 1px solid var(--border-light);
  transition: all 0.3s ease;
}

.step-tag.active {
  background: var(--amber-bg);
  color: var(--amber);
  border-color: #fde68a;
}

.step-tag.done {
  background: var(--green-bg);
  color: var(--green);
  border-color: var(--green-border);
}

/* Candidate card */
.candidate-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 20px;
  margin-bottom: 24px;
}

.candidate-card h3 {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 12px;
  letter-spacing: -0.01em;
}

.candidate-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px 24px;
}

.candidate-field label {
  display: block;
  font-size: 11px;
  font-weight: 500;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-muted);
  margin-bottom: 3px;
}

.candidate-field span {
  font-size: 13px;
  color: var(--text-primary);
}

.skills-list {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 2px;
}

.skill-tag {
  font-size: 11px;
  font-family: var(--font-mono);
  padding: 2px 8px;
  background: var(--accent-subtle);
  border-radius: 3px;
  color: var(--text-secondary);
}

/* Job cards */
.job-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.job-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  transition: border-color var(--transition);
  cursor: default;
}

.job-card:hover {
  border-color: #d6d3d1;
}

.job-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.job-title {
  font-size: 14px;
  font-weight: 600;
  letter-spacing: -0.01em;
}

.job-company {
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.job-score {
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 20px;
  white-space: nowrap;
  flex-shrink: 0;
}

.score-high {
  background: var(--green-bg);
  color: var(--green);
}

.score-mid {
  background: var(--blue-bg);
  color: var(--blue);
}

.score-low {
  background: var(--amber-bg);
  color: var(--amber);
}

.job-meta {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}

.job-meta span {
  font-size: 12px;
  color: var(--text-muted);
}

.job-explanation {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
  padding: 10px 0;
  border-top: 1px solid var(--border-light);
  margin-top: 4px;
}

.job-analysis {
  background: var(--bg);
  border-radius: var(--radius-sm);
  padding: 12px;
  margin-top: 8px;
  border: 1px dashed var(--border);
}

.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.readiness-badge {
  font-size: 11px;
  font-weight: 600;
  padding: 2px 8px;
  border-radius: 4px;
}

.level-strong { background: var(--green-bg); color: var(--green); border: 1px solid var(--green-border); }
.level-moderate { background: var(--blue-bg); color: var(--blue); border: 1px solid var(--blue-border); }
.level-stretch { background: var(--amber-bg); color: var(--amber); border: 1px solid #fde68a; }

.score-container {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
  margin-right: 16px;
}

.score-bar-bg {
  height: 6px;
  background: var(--border-light);
  border-radius: 3px;
  flex: 1;
  overflow: hidden;
}

.score-bar-fill {
  height: 100%;
  background: var(--accent);
  border-radius: 3px;
  transition: width 1s ease-out;
}

.score-text {
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 600;
  min-width: 35px;
}

.analysis-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.analysis-col h5 {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  color: var(--text-muted);
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.analysis-list {
  list-style: none;
  font-size: 12px;
  color: var(--text-secondary);
}

.analysis-list li {
  margin-bottom: 4px;
  position: relative;
  padding-left: 12px;
}

.analysis-list li::before {
  content: '•';
  position: absolute;
  left: 0;
  color: var(--text-muted);
}

.job-skills {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-bottom: 10px;
}

/* Clarifying question */
.clarify-section {
  background: var(--blue-bg);
  border: 1px solid var(--blue-border);
  border-radius: var(--radius);
  padding: 20px;
  margin-top: 24px;
}

.clarify-section h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--blue);
  margin-bottom: 8px;
}

.clarify-section p {
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 14px;
}

.clarify-section .input-row {
  display: flex;
  gap: 8px;
}

.clarify-section input {
  flex: 1;
  font-family: var(--font-sans);
  font-size: 13px;
  padding: 8px 14px;
  border: 1px solid var(--blue-border);
  border-radius: var(--radius-sm);
  background: #fff;
  color: var(--text-primary);
  outline: none;
  transition: border-color var(--transition);
}

.clarify-section input:focus {
  border-color: var(--blue);
}

/* Reasoning block */
.reasoning-block {
  background: var(--green-bg);
  border: 1px solid var(--green-border);
  border-radius: var(--radius);
  padding: 16px 20px;
  margin-bottom: 24px;
}

.reasoning-block h4 {
  font-size: 13px;
  font-weight: 600;
  color: var(--green);
  margin-bottom: 6px;
}

.reasoning-block p {
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Results area */
#results-area {
  opacity: 0;
  transform: translateY(8px);
  transition: opacity 0.3s ease, transform 0.3s ease;
}

#results-area.visible {
  opacity: 1;
  transform: translateY(0);
}

/* Footer */
.footer {
  padding: 32px 0;
  border-top: 1px solid var(--border-light);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.footer span {
  font-size: 12px;
  color: var(--text-muted);
}

.footer a {
  font-size: 12px;
  color: var(--text-muted);
  text-decoration: none;
  transition: color var(--transition);
}

.footer a:hover { color: var(--text-secondary); }

/* JSON toggle */
.json-toggle {
  margin-top: 24px;
}

.json-toggle summary {
  font-size: 12px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  cursor: pointer;
  padding: 6px 0;
  list-style: none;
  display: flex;
  align-items: center;
  gap: 6px;
}

.json-toggle summary::-webkit-details-marker { display: none; }

.json-toggle summary::before {
  content: '▸';
  font-size: 10px;
  transition: transform var(--transition);
}

.json-toggle[open] summary::before {
  transform: rotate(90deg);
}

.json-block {
  background: #1c1917;
  color: #d6d3d1;
  font-family: var(--font-mono);
  font-size: 12px;
  padding: 16px;
  border-radius: var(--radius);
  overflow-x: auto;
  margin-top: 8px;
  line-height: 1.5;
  max-height: 400px;
  overflow-y: auto;
}

/* Responsive */
@media (max-width: 600px) {
  .container { padding: 0 16px; }
  .header { padding: 32px 0 28px; }
  .candidate-grid { grid-template-columns: 1fr; }
  .clarify-section .input-row { flex-direction: column; }
  .header-meta { flex-wrap: wrap; }
}
</style>
</head>
<body>

<div class="container">
  <header class="header">
    <h1>Smart Job Match Agent</h1>
    <p>Paste a resume below. The agent parses it, ranks 50 jobs by semantic similarity, and explains each match.</p>
    <div class="header-meta">
      <span class="meta-chip"><span class="dot"></span> JOBS_LOADED_COUNT jobs indexed</span>
      <span class="meta-chip">gpt-4o-mini</span>
      <span class="meta-chip">text-embedding-3-small</span>
    </div>
  </header>

  <!-- Input -->
  <div class="section">
    <div class="section-label">Resume</div>
    <div class="input-group">
      <textarea id="resume-input" placeholder="Paste the candidate's resume text here..."></textarea>
      <span class="char-count" id="char-count">0</span>
    </div>
    <div class="actions">
      <button class="btn btn-primary" id="submit-btn" onclick="submitResume()">Find matches</button>
      <button class="btn btn-ghost" id="clear-btn" onclick="clearAll()">Clear</button>
    </div>
    <div class="pipeline-steps" id="pipeline-steps" style="display:none;">
      <span class="step-tag" id="step-parse">parse_resume</span>
      <span class="step-tag" id="step-embed">embed + rank</span>
      <span class="step-tag" id="step-explain">explain_matches</span>
    </div>
    <div class="status-bar" id="status-bar"></div>
  </div>

  <!-- Results -->
  <div id="results-area">
    <!-- Candidate profile -->
    <div id="candidate-section" class="section" style="display:none;">
      <div class="section-label">Parsed candidate</div>
      <div class="candidate-card" id="candidate-card"></div>
    </div>

    <!-- Reasoning (for /refine) -->
    <div id="reasoning-section" style="display:none;"></div>

    <!-- Job matches -->
    <div id="jobs-section" class="section" style="display:none;">
      <div class="section-label">Top matches</div>
      <div class="job-list" id="job-list"></div>
    </div>

    <!-- Clarifying question -->
    <div id="clarify-section" style="display:none;"></div>

    <!-- Raw JSON -->
    <div id="json-section" style="display:none;">
      <details class="json-toggle">
        <summary>raw json response</summary>
        <pre class="json-block" id="json-output"></pre>
      </details>
    </div>
  </div>

  <footer class="footer">
    <span></span>
    <a href="/docs" target="_blank">API docs &rarr;</a>
  </footer>
</div>

<script>
const resumeInput = document.getElementById('resume-input');
const charCount = document.getElementById('char-count');
const submitBtn = document.getElementById('submit-btn');
const statusBar = document.getElementById('status-bar');
const pipelineSteps = document.getElementById('pipeline-steps');
const resultsArea = document.getElementById('results-area');

let lastResumeText = '';
let lastClarifyingQuestion = '';
let lastResponse = null;

resumeInput.addEventListener('input', () => {
  charCount.textContent = resumeInput.value.length;
});

function clearAll() {
  resumeInput.value = '';
  charCount.textContent = '0';
  statusBar.textContent = '';
  statusBar.className = 'status-bar';
  pipelineSteps.style.display = 'none';
  resultsArea.classList.remove('visible');
  document.getElementById('candidate-section').style.display = 'none';
  document.getElementById('jobs-section').style.display = 'none';
  document.getElementById('clarify-section').style.display = 'none';
  document.getElementById('reasoning-section').style.display = 'none';
  document.getElementById('json-section').style.display = 'none';
  lastResponse = null;
}

function setStep(step) {
  ['step-parse', 'step-embed', 'step-explain'].forEach(id => {
    document.getElementById(id).className = 'step-tag';
  });
  const steps = ['step-parse', 'step-embed', 'step-explain'];
  const idx = steps.indexOf(step);
  for (let i = 0; i < idx; i++) {
    document.getElementById(steps[i]).className = 'step-tag done';
  }
  if (idx >= 0) document.getElementById(step).className = 'step-tag active';
}

function allStepsDone() {
  ['step-parse', 'step-embed', 'step-explain'].forEach(id => {
    document.getElementById(id).className = 'step-tag done';
  });
}

function scoreClass(score) {
  if (score >= 0.45) return 'score-high';
  if (score >= 0.35) return 'score-mid';
  return 'score-low';
}

function renderCandidate(c) {
  const section = document.getElementById('candidate-section');
  const card = document.getElementById('candidate-card');
  const skills = (c.skills || []).map(s => `<span class="skill-tag">${esc(s)}</span>`).join('');
  const roles = (c.preferred_roles || []).join(', ');
  card.innerHTML = `
    <h3>${esc(c.name)}</h3>
    <div class="candidate-grid">
      <div class="candidate-field">
        <label>Experience</label>
        <span>${c.experience_years} years</span>
      </div>
      <div class="candidate-field">
        <label>Education</label>
        <span>${esc(c.education)}</span>
      </div>
      <div class="candidate-field">
        <label>Preferred roles</label>
        <span>${esc(roles) || '—'}</span>
      </div>
      <div class="candidate-field" style="grid-column: 1 / -1;">
        <label>Skills</label>
        <div class="skills-list">${skills}</div>
      </div>
    </div>
  `;
  section.style.display = 'block';
}

function renderJobs(jobs) {
  const section = document.getElementById('jobs-section');
  const list = document.getElementById('job-list');
  list.innerHTML = jobs.map((j, i) => {
    const skills = (j.skills || []).map(s => `<span class="skill-tag">${esc(s)}</span>`).join('');
    const remote = j.remote ? 'Remote' : 'On-site';
    const matchClass = (j.match_level || '').toLowerCase().includes('strong') ? 'level-strong' : 
                     (j.match_level || '').toLowerCase().includes('moderate') ? 'level-moderate' : 'level-stretch';
    
    return `
      <div class="job-card">
        <div class="job-header">
          <div>
            <div class="job-title">${esc(j.title)}</div>
            <div class="job-company">${esc(j.company)}</div>
          </div>
          <span class="job-score ${scoreClass(j.similarity_score)}">${j.similarity_score.toFixed(4)}</span>
        </div>
        <div class="job-meta">
          <span>${esc(j.location)} · ${remote}</span>
          <span>${esc(j.domain)}</span>
          <span>${j.required_experience_years}yr+ exp</span>
          <span>₹${j.salary_lpa} LPA</span>
        </div>
        <div class="job-skills">${skills}</div>
        <div class="job-explanation">${esc(j.explanation)}</div>
        
        <div class="job-analysis">
          <div class="analysis-header">
            <div class="score-container">
              <div class="score-bar-bg">
                <div class="score-bar-fill" style="width: ${j.interview_readiness_score}%"></div>
              </div>
              <div class="score-text">${j.interview_readiness_score}%</div>
            </div>
            <span class="readiness-badge ${matchClass}">
              ${esc(j.match_level)}
            </span>
          </div>
          
          <div class="analysis-grid">
            <div class="analysis-col">
              <h5><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg> Skill Gaps</h5>
              <ul class="analysis-list">
                ${(j.skill_gaps || []).length > 0 ? j.skill_gaps.map(s => `<li>${esc(s)}</li>`).join('') : '<li>No major gaps</li>'}
              </ul>
            </div>
            <div class="analysis-col">
              <h5><svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z"/><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z"/></svg> Suggested Prep</h5>
              <ul class="analysis-list">
                ${(j.suggested_preparation || []).map(s => `<li>${esc(s)}</li>`).join('')}
              </ul>
            </div>
          </div>
        </div>
      </div>
    `;
  }).join('');
  section.style.display = 'block';
}

function renderClarify(question) {
  const section = document.getElementById('clarify-section');
  lastClarifyingQuestion = question;
  section.innerHTML = `
    <div class="clarify-section">
      <h4>Clarifying question</h4>
      <p>${esc(question)}</p>
      <div class="input-row">
        <input type="text" id="clarify-input" placeholder="Type your answer to refine results..." />
        <button class="btn btn-primary" onclick="submitRefine()">Refine</button>
      </div>
    </div>
  `;
  section.style.display = 'block';
}

function renderReasoning(text) {
  const section = document.getElementById('reasoning-section');
  section.innerHTML = `
    <div class="reasoning-block">
      <h4>Why rankings changed</h4>
      <p>${esc(text)}</p>
    </div>
  `;
  section.style.display = 'block';
}

function renderJson(data) {
  document.getElementById('json-output').textContent = JSON.stringify(data, null, 2);
  document.getElementById('json-section').style.display = 'block';
}

function esc(str) {
  if (!str) return '';
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

async function submitResume() {
  const text = resumeInput.value.trim();
  if (!text) {
    statusBar.textContent = 'Paste a resume first.';
    statusBar.className = 'status-bar error';
    return;
  }
  lastResumeText = text;

  submitBtn.disabled = true;
  submitBtn.innerHTML = '<span class="spinner"></span>Matching...';
  statusBar.textContent = 'Running agent pipeline...';
  statusBar.className = 'status-bar';
  pipelineSteps.style.display = 'flex';
  document.getElementById('reasoning-section').style.display = 'none';
  setStep('step-parse');

  // Animate steps while waiting
  const stepTimer = setInterval(() => {
    const parseEl = document.getElementById('step-parse');
    const embedEl = document.getElementById('step-embed');
    if (parseEl.classList.contains('active')) {
      parseEl.className = 'step-tag done';
      embedEl.className = 'step-tag active';
    } else if (embedEl.classList.contains('active')) {
      embedEl.className = 'step-tag done';
      document.getElementById('step-explain').className = 'step-tag active';
    }
  }, 2800);

  try {
    const res = await fetch('/recommend', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resume_text: text }),
    });

    clearInterval(stepTimer);

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Request failed' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    lastResponse = data;

    allStepsDone();
    statusBar.textContent = `Done — ${data.ranked_jobs.length} matches found`;

    renderCandidate(data.candidate);
    renderJobs(data.ranked_jobs);
    if (data.clarifying_question) renderClarify(data.clarifying_question);
    renderJson(data);

    resultsArea.classList.add('visible');
  } catch (err) {
    clearInterval(stepTimer);
    statusBar.textContent = err.message;
    statusBar.className = 'status-bar error';
    pipelineSteps.style.display = 'none';
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = 'Find matches';
  }
}

async function submitRefine() {
  const answer = document.getElementById('clarify-input').value.trim();
  if (!answer) return;

  const refineBtn = document.querySelector('#clarify-section .btn-primary');
  refineBtn.disabled = true;
  refineBtn.innerHTML = '<span class="spinner"></span>Refining...';
  statusBar.textContent = 'Refining with your answer...';
  statusBar.className = 'status-bar';
  pipelineSteps.style.display = 'flex';
  setStep('step-parse');

  const stepTimer = setInterval(() => {
    const parseEl = document.getElementById('step-parse');
    const embedEl = document.getElementById('step-embed');
    if (parseEl.classList.contains('active')) {
      parseEl.className = 'step-tag done';
      embedEl.className = 'step-tag active';
    } else if (embedEl.classList.contains('active')) {
      embedEl.className = 'step-tag done';
      document.getElementById('step-explain').className = 'step-tag active';
    }
  }, 2800);

  try {
    const res = await fetch('/refine', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        resume_text: lastResumeText,
        clarifying_question: lastClarifyingQuestion,
        candidate_answer: answer,
      }),
    });

    clearInterval(stepTimer);

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: 'Refine failed' }));
      throw new Error(err.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();

    allStepsDone();
    statusBar.textContent = 'Refined — rankings updated';

    if (data.reasoning) renderReasoning(data.reasoning);
    renderJobs(data.ranked_jobs);
    document.getElementById('clarify-section').style.display = 'none';
    renderJson(data);

    resultsArea.classList.add('visible');
  } catch (err) {
    clearInterval(stepTimer);
    statusBar.textContent = err.message;
    statusBar.className = 'status-bar error';
  } finally {
    refineBtn.disabled = false;
    refineBtn.innerHTML = 'Refine';
  }
}
</script>

</body>
</html>"""
