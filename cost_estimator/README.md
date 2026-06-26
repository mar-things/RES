# RES AI Cost Estimator

MVP scope:

- Accept a smartphone/photo file and copy it into managed photo storage.
- Optionally call OpenAI Vision when `OPENAI_API_KEY` is configured.
- Fall back to deterministic local severity classification when offline.
- Convert severity to an estimated cost range.
- Write the selected estimate back to the main RES database as a `Finding`.

The local YOLOv8/IP-camera path is represented by the same classifier
interface and can be added later without changing the RES database contract.
