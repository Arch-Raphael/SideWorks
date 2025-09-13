# SideWorks #1
<h1 align="center">🔬 Hospital Patient Data Processor</h1>
<p align="center">
  <img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExYzY1YmRmYmU5ZGI1ZjdiNjBmN2M4NjAxMDViOTAyZTc1YjgyOTRhOCZjdD1n/qgQUggAC3Pfv687qPC/giphy.gif" width="220" alt="AI Research GIF"/>
</p>

<p align="center">
  <b>A Researcher-Themed AI Tool for Cleaning Patient Records, Assigning Unique IDs, and Detecting Duplicates Across Hospitals</b>
</p>
<p align="center"><i>Made by <b>Elbin George</b></i></p>

---

<h2>✨ Features</h2>
<ul>
  <li>📂 Upload an Excel file with <b>multiple hospital sheets</b>.</li>
  <li>🆔 Assigns <b>sequential numeric unique IDs</b> to each patient.</li>
  <li>🔍 Detects <b>duplicate patients</b> across hospitals using:
    <ul>
      <li>✔ Name similarity (fuzzy match ≥65%)</li>
      <li>✔ Same DOB</li>
      <li>✔ Same Gender</li>
    </ul>
  </li>
  <li>📊 Provides a <b>researcher dashboard</b> with summaries.</li>
  <li>⚡ Outputs two clean Excel files:
    <ul>
      <li><code>Processed_Patients.xlsx</code></li>
      <li><code>Duplicates_For_Review.xlsx</code></li>
    </ul>
  </li>
  <li>🎨 Professional <b>researcher-friendly UI</b> with progress indicators, metric cards, and tabs.</li>
</ul>

---

<h2>🚀 Demo Workflow</h2>
<p align="center"><i>Upload → Analyze → Detect Duplicates → Download Results</i></p>

---

<h2>🛠️ Installation</h2>

```bash
# Clone the repo
git clone https://github.com/yourusername/hospital-patient-processor.git
cd hospital-patient-processor

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate   # (Linux/Mac)
venv\Scripts\activate      # (Windows)

# Install dependencies
pip install -r requirements.txt

