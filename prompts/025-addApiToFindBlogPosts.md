- Follow this spec: /workspaces/discovery/specs/clean_architecture.md
- Write api to get blog links that answer a key search phrase or question.
- API should return a JSON array of documents and their links
- At the infrastructure level, the API should use Gemini Flash 2.5 with Google search enabled
- The following prompt can be helpful

**Key Question to Answer:** [Insert the specific, detailed question here, e.g., "What are the most effective, evidence-based methods for improving deep sleep quality without medication?"]

**Goal:** Find 5 to 10 high-quality, in-depth blog posts, articles, or guides that provide a comprehensive, robust, and well-cited answer to the Key Question. Prioritize articles that go beyond a surface-level list.

**Quality Filters (Implicit Search Intent):**
1.  **Depth:** Must provide detailed explanations, 'how-to' steps, or scientific rationale.
2.  **Robustness:** Should appear authoritative (e.g., from reputable blogs, journals, or experts).
3.  **Format:** Must be a blog post, article, or online guide (exclude forums, simple news snippets, videos, or bare product pages).

**Output Requirement:** Return ONLY a single JSON array named `robust_articles`. Each object in the array must contain only two keys: `title` (the article's title) and `link` (the full URL).

**Example of Desired Output Format:**
```json
{
  "robust_articles": [
    {
      "title": "A Comprehensive Guide to Optimizing Sleep Hygiene for Deep Rest",
      "link": "[https://example.com/sleep-guide-1](https://example.com/sleep-guide-1)"
    },
    {
      "title": "Beyond Melatonin: 7 Non-Pharmacological Interventions for Insomnia",
      "link": "[https://anothersite.org/deep-sleep-interventions](https://anothersite.org/deep-sleep-interventions)"
    }
    // ... up to 10 articles
  ]
}