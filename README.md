# 🔎 Research-to-Deck Agent

> **An AI-powered research automation system that transforms a topic into a research-backed, presentation-ready PowerPoint — with live web research, local LLM reasoning, native editable charts, and source citations on every slide.**

Research-to-Deck Agent automates the complete workflow of turning an open-ended research topic into a structured presentation.

Give it a topic such as:

```bash
python run.py "Generative AI Impact on Business"
```

The system automatically:

**Searches the web → Extracts research → Deduplicates sources → Structures findings with a local LLM → Generates a PowerPoint**

The result is a polished `.pptx` presentation containing structured insights, data-driven charts, editable PowerPoint elements, and source citations.

---

## 🚀 Why This Project?

Creating a research-backed presentation usually requires several manual steps:

* Searching multiple websites
* Reading and comparing articles
* Extracting relevant information
* Identifying useful statistics
* Structuring the findings into slides
* Creating charts
* Designing the presentation
* Adding references and citations

This project automates that entire workflow while keeping the research **traceable to its original sources**.

### The goal

> **Turn an unstructured research question into a structured, evidence-backed business presentation with minimal manual effort.**

---

# ✨ Key Features

### 🔎 Multi-Angle Web Research

Instead of relying on a single search query, the agent searches the topic from multiple perspectives, including:

* General overview
* Industry impact
* Statistics and market data
* Recent developments
* Business implications

Search results are deduplicated by URL before content extraction.

---

### 📄 Intelligent Content Extraction

The system uses `trafilatura` to extract clean article content while removing:

* Navigation
* Advertisements
* Unnecessary page elements
* Boilerplate content

When a website blocks automated access, the system gracefully falls back to available search snippets.

---

### 🧠 Local LLM-Powered Structuring

Raw research is passed to a locally running LLM through **Ollama**.

The model transforms the research into a structured presentation outline containing:

* Slide titles
* Key insights
* Bullet points
* Chart data
* Units
* Source references

The LLM is explicitly instructed to remain grounded in the retrieved research and avoid inventing unsupported statistics.

---

### 📊 Native PowerPoint Charts

Charts are generated as **native PowerPoint objects**, rather than static images.

This means users can:

* Edit chart values
* Change chart types
* Modify labels
* Resize charts
* Customize the presentation directly in PowerPoint

Supported visualizations include data-driven:

* Bar charts
* Pie charts
* Other PowerPoint-native chart formats supported by the generator

---

### 🔗 Source Citation on Every Slide

Every content slide includes source references connected to the research used to generate that slide.

This makes the final presentation:

**Research-backed → Traceable → Easier to verify**

---

### 🛠️ Resilient JSON Processing

Local LLMs can occasionally return malformed or incomplete JSON.

The pipeline handles this using multiple recovery layers:

```text
Valid JSON
    ↓
Direct parsing
    ↓
JSON repair
    ↓
Partial slide recovery
```

This prevents a single formatting issue from unnecessarily breaking the entire presentation-generation pipeline.

---

### 💻 Fully Local LLM Processing

The content-structuring stage runs locally using Ollama.

No cloud LLM API is required.

```text
Web Search
    ↓
Local Research Processing
    ↓
Local LLM
    ↓
PowerPoint Generation
```

This provides:

* No LLM API key
* No per-request LLM cost
* Greater control over research processing
* Local inference

> **Note:** Internet access is still required for live web research.

---

# 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │     Topic Input     │
                         │ "GenAI in Business" │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Web Research      │
                         │     search.py       │
                         │                     │
                         │ • Multi-query       │
                         │ • Source discovery  │
                         │ • Text extraction   │
                         │ • Deduplication     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Research Dataset   │
                         │                     │
                         │ • Article content   │
                         │ • URLs              │
                         │ • Source metadata   │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Content Structuring│
                         │    structure.py     │
                         │                     │
                         │   Local LLM         │
                         │      Ollama         │
                         │                     │
                         │ • Slide outline     │
                         │ • Bullet points     │
                         │ • Chart data        │
                         │ • Source mapping    │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │  Deck Generation    │
                         │      deck.py        │
                         │                     │
                         │ • Slide design      │
                         │ • Native charts     │
                         │ • Citations         │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Finished .pptx    │
                         │                     │
                         │  Editable & Ready   │
                         │    for Presentation │
                         └─────────────────────┘
```

---

# 🧩 How the Pipeline Works

## 1. Topic Input

The user provides a research topic:

```bash
python run.py "Generative AI Impact on Business"
```

The topic becomes the input to the complete research-to-deck pipeline.

---

## 2. Multi-Angle Web Search

The research module generates multiple search perspectives around the topic.

For example:

```text
Generative AI business impact
Generative AI business statistics
Generative AI productivity
Generative AI industry adoption
Generative AI recent developments
```

The results are then:

1. Collected
2. Deduplicated
3. Downloaded where possible
4. Converted into clean article text
5. Stored with source URLs

---

## 3. Research Structuring

The collected research is provided to the local LLM.

The model converts unstructured research into a structured presentation schema.

Conceptually:

```json
{
  "title": "Economic Impact of Generative AI",
  "bullets": [
    "Key finding...",
    "Business implication..."
  ],
  "chart": {
    "type": "bar",
    "labels": ["A", "B", "C"],
    "values": [10, 20, 30],
    "unit": "%"
  },
  "sources": [
    "https://example.com"
  ]
}
```

The important design principle is:

> **The model is instructed to use retrieved research as its knowledge boundary rather than freely generating unsupported statistics.**

---

## 4. PowerPoint Generation

The structured outline is passed to the deck-generation module.

The generator creates:

* Title slide
* Content slides
* Bullet points
* Native charts
* Source citations
* Closing slide

The final result is a standard `.pptx` file that can be opened and edited in Microsoft PowerPoint.

---

# 🛠️ Tech Stack

| Technology      | Purpose                 |
| --------------- | ----------------------- |
| **Python**      | Core application        |
| **DDGS**        | Web search              |
| **Trafilatura** | Article text extraction |
| **Ollama**      | Local LLM inference     |
| **Qwen 3.5 9B** | Content structuring     |
| **JSON Repair** | Malformed JSON recovery |
| **python-pptx** | PowerPoint generation   |

---

# 📁 Project Structure

```text
research-to-deck-agent/
│
├── research/
│   ├── search.py
│   ├── structure.py
│   └── deck.py
│
├── output/
│   ├── example_outline.json
│   └── example_deck.pptx
│
├── run.py
├── requirements.txt
└── README.md
```

### Module Responsibilities

| Module         | Responsibility                                          |
| -------------- | ------------------------------------------------------- |
| `search.py`    | Search, extraction, deduplication and source collection |
| `structure.py` | Convert research into a structured slide outline        |
| `deck.py`      | Generate the final PowerPoint                           |
| `run.py`       | Orchestrate the complete pipeline                       |

Each module can also be executed independently for testing and debugging.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/research-to-deck-agent.git

cd research-to-deck-agent
```

## 2. Install Dependencies

```bash
pip install -r requirements.txt
```

## 3. Install Ollama

Install Ollama and make sure it is running.

Then pull the required model:

```bash
ollama pull qwen3.5:9b
```

Verify that the model is available:

```bash
ollama list
```

---

# ▶️ Usage

## Run the Complete Pipeline

```bash
python run.py "Generative AI Impact on Business"
```

Or run without arguments:

```bash
python run.py
```

The application will prompt you for a topic.

### Pipeline

```text
Topic
  ↓
Web Search
  ↓
Article Extraction
  ↓
Source Deduplication
  ↓
Local LLM Structuring
  ↓
Slide + Chart Generation
  ↓
PowerPoint
```

---

# 🔬 Run Individual Modules

Each stage can also be executed separately.

### Research

```bash
python research/search.py
```

### Content Structuring

```bash
python research/structure.py output/research_<topic>.json
```

### Deck Generation

```bash
python research/deck.py output/outline_<topic>.json
```

This modular design makes it easier to debug, test, and improve individual components without running the entire pipeline.

---

# 📈 Verified Results

The pipeline was tested using:

> **"Generative AI Impact on Business"**

### Web Research

The system successfully collected:

**16 unique sources**

across **4 research angles** in under a minute during the test run.

The system also handled blocked sources gracefully by falling back to available search snippets.

---

### Content Structuring

The local LLM generated a structured:

**7-slide research outline**

containing source-backed statistics and chart-ready data.

Example findings included:

| Insight                  | Example                                                     |
| ------------------------ | ----------------------------------------------------------- |
| Economic value           | $2.6T–$4.4T projected annual value                          |
| Productivity vs. revenue | 66% productivity gains vs. 20% revenue gains                |
| AI investment            | $37B GenAI enterprise spend vs. $581.7B total AI investment |

> Statistics shown above were obtained from the project's test run and should be independently verified before external presentation.

---

### PowerPoint Generation

The final pipeline generated a:

**9-slide PowerPoint presentation**

consisting of:

* 1 title slide
* 7 content slides
* 1 closing slide

Charts were generated as native PowerPoint objects and remained editable after opening the `.pptx`.

---

# 🐛 Engineering Challenge: Local LLM Thinking Mode

During testing, an important failure mode was discovered.

The selected Qwen model could spend its available token budget on reasoning and return little or no usable final output.

### Problem

```text
Prompt
  ↓
LLM reasoning
  ↓
Token budget exhausted
  ↓
Empty / incomplete final response
```

### Solution

The Ollama call was configured to disable unnecessary thinking for this structured-generation task:

```python
think=False
```

A diagnostic check was also added to identify the failure condition if it occurs again.

This improved reliability for the JSON-based content-generation stage.

---

# ⚠️ Limitations

### 1. Search Quality Depends on the Topic

Search results vary depending on the topic and available web sources.

Some high-authority websites may block automated requests.

The system handles these cases by falling back to snippets, but this can result in less detailed research.

---

### 2. Local LLM Performance Depends on Hardware

Local inference is slower than many cloud APIs on consumer hardware.

The structuring stage may take several minutes depending on:

* CPU/GPU
* Available RAM/VRAM
* Model size
* Research volume

---

### 3. Source Grounding Is Not Fact Verification

The system attempts to ensure that generated claims are supported by retrieved source content.

However:

> **Source grounding does not guarantee that the original source is factually correct.**

Important statistics should therefore still be manually verified before being used in professional or academic presentations.

---

### 4. Presentation Quality Is Template-Based

The system generates a consistent professional layout, but it is not intended to completely replace a human presentation designer.

For high-stakes presentations, users may still want to refine:

* Slide emphasis
* Storytelling
* Visual hierarchy
* Branding
* Speaker notes

---

# 🔮 Future Improvements

Planned improvements include:

* [ ] Configuration file for search and model parameters
* [ ] User-defined target slide count
* [ ] Regenerate individual slides
* [ ] Additional chart types
* [ ] Better source credibility scoring
* [ ] Automatic source ranking
* [ ] Fact-consistency checks across multiple sources
* [ ] PDF report generation
* [ ] Custom PowerPoint themes
* [ ] Speaker notes generation
* [ ] Research export to Markdown/JSON
* [ ] Interactive research dashboard

---

# 💡 Potential Applications

The architecture can be adapted beyond presentations.

### Business Research

```text
Question → Web Research → Analysis → Executive Presentation
```

### Market Intelligence

```text
Market → Research → Competitor Insights → Management Deck
```

### Academic Research

```text
Topic → Literature Search → Synthesis → Presentation
```

### Consulting

```text
Business Problem → Evidence Collection → Insights → Client Deck
```

### Management Reporting

```text
Business Data → Analysis → Key Findings → Executive Summary
```

---

# 🎯 What This Project Demonstrates

This project goes beyond simply using an LLM.

It demonstrates practical implementation of:

* **Agentic workflow design**
* **Web research automation**
* **Retrieval and source grounding**
* **Local LLM integration**
* **Structured LLM output**
* **JSON validation and recovery**
* **Data extraction**
* **Automated document generation**
* **PowerPoint automation**
* **Native data visualization**
* **End-to-end AI pipeline engineering**

The core idea is to connect **AI reasoning with a real business deliverable**.

---

# 📌 Example

### Input

```text
Generative AI Impact on Business
```

### Processing

```text
              USER TOPIC
                   │
                   ▼
            MULTI-QUERY SEARCH
                   │
                   ▼
          SOURCE COLLECTION
                   │
                   ▼
         CONTENT EXTRACTION
                   │
                   ▼
         LOCAL LLM STRUCTURING
                   │
                   ▼
        SLIDES + CHART DATA
                   │
                   ▼
          POWERPOINT GENERATOR
                   │
                   ▼
             FINAL .PPTX
```

### Output

A presentation containing:

**Research-backed insights + editable charts + source citations**

---

# 📄 License

This project is licensed under the **MIT License**.

---

## 👨‍💻 Author

**Anuj Bhatt**

MBA — Artificial Intelligence & Data Science

Interested in:

**AI Engineering • Generative AI • Data Science • Machine Learning • Data Engineering**

---

⭐ If you find this project useful, consider giving the repository a star.
