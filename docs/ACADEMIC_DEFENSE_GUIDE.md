# Academic Defense & Viva Evaluation Guide
## Final Year Project (FYP) — Bachelor of Science in Computer Science

---

## 1. Problem Statement & Motivation
Traditional streaming analytics projects often limit scope to exploratory data analysis (EDA) on static datasets. This project elevates the problem space by implementing a **production-grade, multi-tier data platform and intelligent recommendation system** that addresses three fundamental industry challenges:
1. **Semantic Gap in Search:** Keyword-based search fails when users describe moods, concepts, or tropes rather than exact titles.
2. **Cold Start Asymmetry:** New users with no telemetry history and newly added catalog titles lack collaborative filtering signals.
3. **Storage & Serving Co-location:** Decoupling vector search into separate external vector stores often introduces distributed network overhead, transactional inconsistency, and operational complexity.

---

## 2. Mathematical Modeling & Algorithmic Formulation

### A. Semantic Content Embedding
Given a catalog item $x_i$ with text representation $T_i = (\text{Title}, \text{Genres}, \text{Director}, \text{Cast}, \text{Overview})$, a dense sentence transformer $\mathcal{M}$ maps $T_i$ to a 384-dimensional latent embedding $\vec{v}_i \in \mathbb{R}^{384}$:

$$\vec{v}_i = \frac{\mathcal{M}(T_i)}{\|\mathcal{M}(T_i)\|_2}$$

By constraining $\|\vec{v}_i\|_2 = 1.0$, the cosine similarity between a natural language query vector $\vec{q}$ and item vector $\vec{v}_i$ reduces to the Euclidean dot product:

$$S_{\text{cos}}(\vec{q}, \vec{v}_i) = \vec{q} \cdot \vec{v}_i$$

### B. User Profile Latent Vector Aggregation
A user's dynamic preference vector $\vec{u}$ is formulated as a recency- and engagement-weighted linear combination of consumed item embeddings:

$$\vec{u} = \frac{\sum_{j \in \mathcal{H}_u} w_j \cdot \vec{v}_j}{\left\|\sum_{j \in \mathcal{H}_u} w_j \cdot \vec{v}_j\right\|_2}$$

Where the interaction weight $w_j$ incorporates interaction type and completion percentage:

$$w_j = \alpha_{\text{type}} \times \left(0.5 + 0.5 \times \frac{\text{completion\_pct}_j}{100}\right) \times e^{-\lambda (t_{\text{now}} - t_j)}$$

with $\alpha_{\text{like}} = 2.5, \alpha_{\text{save}} = 2.0, \alpha_{\text{watch}} = 1.0, \alpha_{\text{skip}} = 0.1$, and $\lambda$ representing temporal decay.

### C. Hybrid Multi-Signal Scoring Function
For a candidate title $c$, the final recommendation score $F(u, c)$ fuses semantic similarity with metadata affinity:

$$F(u, c) = w_{\text{sem}} S_{\text{cos}}(\vec{u}, \vec{v}_c) + w_{\text{genre}} J(\mathcal{G}_u, \mathcal{G}_c) + w_{\text{dir}} \mathbb{I}(D_c \in \mathcal{D}_u) + w_{\text{cast}} J(\mathcal{C}_u, \mathcal{C}_c)$$

Where $J(A, B) = \frac{|A \cap B|}{|A \cup B|}$ is the Jaccard similarity coefficient, and $\mathbb{I}$ is the indicator function. Default hyperparameters:
$$w_{\text{sem}} = 0.40, \quad w_{\text{genre}} = 0.30, \quad w_{\text{dir}} = 0.15, \quad w_{\text{cast}} = 0.15$$

---

## 3. Algorithmic Complexity Analysis

| Operation | Brute-Force Baseline | Our Implementation (pgvector + HNSW) | Complexity Justification |
| :--- | :--- | :--- | :--- |
| **Semantic Query (Top-K)** | $O(N \cdot d)$ | $O(\log N \cdot d)$ | HNSW constructs multi-layer proximity graphs for logarithmic nearest neighbor traversal. |
| **User Vector Aggregation** | $O(|\mathcal{H}_u| \cdot d)$ | $O(|\mathcal{H}_u| \cdot d)$ | Direct linear combination over user history bounded to $|\mathcal{H}_u| \le 50$. |
| **Metadata Fusion Scoring** | $O(C \cdot (|G| + |C|))$ | $O(C)$ | Set hashing enables $O(1)$ intersection checks across candidate set $C$. |
| **Telemetry Ingestion** | $O(1)$ | $O(1)$ | B-Tree indexed append-only insert with background batch write. |

*(Where $N$ = catalog size, $d = 384$ vector dimensions, $C$ = candidate pool size, $|\mathcal{H}_u|$ = user history size).*

---

## 4. Key Architectural Trade-offs & Justifications

### Q1: Why use PostgreSQL with pgvector rather than a dedicated vector database (e.g., Pinecone, Milvus, Chroma)?
* **Defense Response:** Co-locating relational data and vector embeddings within PostgreSQL eliminated the *dual-write anomaly* and cross-network latency. It allows relational metadata filtering (`WHERE type = 'Movie' AND release_year >= 2020`) and vector cosine ordering (`ORDER BY embedding <=> qvec`) to execute inside a single SQL query execution plan using the query optimizer, avoiding multi-system two-phase commits.

### Q2: How does the platform resolve the Cold Start Problem?
* **Defense Response:** 
  1. **New User (0 interactions):** The platform transitions from collaborative preference modeling to an explicit *Popularity + Diversity* fallback. It ranks items using historical engagement completion rates while enforcing genre diversity to avoid pigeonholing the user.
  2. **New Item (0 watches):** Unlike collaborative filtering models (e.g., Matrix Factorization / ALS) that require interaction matrices, our system leverages the item's pre-computed dense semantic embedding and metadata attributes to match against user preference vectors immediately upon ingestion.

### Q3: What ensures the system's operational resilience?
* **Defense Response:** The platform includes graceful fallbacks across all tiers:
  - Database layer falls back to local embedded SQLite if PostgreSQL is unavailable.
  - Sentence embedder falls back to a deterministic 384-dimensional unit-norm projection if heavy model weights are offline.
  - The API incorporates automated database table health checks and asynchronous non-blocking connection pooling.

---

## 5. Potential FYP Defense Questions & Model Answers

### Panelist Question: "How would you scale this architecture to 100 million active streaming users?"
> **Model Answer:**
> "At 100M users, three architectural transitions would be implemented:
> 1. **Streaming Ingestion:** Replace direct HTTP batch ingestion with a distributed event log (Apache Kafka) paired with a stream processing engine (Apache Flink) for real-time rolling user vector computation.
> 2. **Caching & Retrieval Tier:** Introduce Redis for sub-millisecond retrieval of pre-computed user vectors and two-stage recommendation architecture (Candidate Generation via HNSW ANN $\to$ Heavy Ranking via Deep Learning model like DLRM).
> 3. **Database Sharding:** Shard PostgreSQL telemetry tables horizontally by `user_id` hash range while maintaining read-replicas for catalog embeddings."
