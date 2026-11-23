# Architecture diagrams

Editable Mermaid sources. The README and docs/05 embed simplified versions of these diagrams as `mermaid` blocks, which GitHub renders natively. `screenshots/` holds the redacted AWS console screenshots.

| File | Diagram |
|---|---|
| `01-solution-architecture.mmd` | Solution architecture |
| `02-request-flow.mmd` | End-to-end request sequence |
| `03-deployment.mmd` | Build, ECR and AWS deployment |

To export PNG/SVG versions (for slides or LinkedIn), run this from this folder:

```bash
npx -y @mermaid-js/mermaid-cli -i 01-solution-architecture.mmd -o 01-solution-architecture.png -b white -w 1800 -s 2
```

Or paste a file into https://mermaid.live and export.
