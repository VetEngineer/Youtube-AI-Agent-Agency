# Council & Deployment Roles

This project is developed and managed by a "Council" of AI Agents, each with a specific role and responsibility.

## 🏛️ The Council

### 1. Codex (Project Manager)
*   **Role:** Project Manager & Lead Reviewer
*   **Responsibility:**
    *   **No Direct Coding:** Codex does not write code directly.
    *   **Project Oversight:** First to grasp the entire project context and roadmap.
    *   **Task Management:** Creates `issues` in Git to distribute work.
    *   **Strict Review:** Reviews all pushed code rigorously and strictly.
    *   **Feedback:** Opens follow-up issues based on code reviews.

### 2. Claude-code (Developer)
*   **Role:** Lead Developer (Implementation)
*   **Responsibility:**
    *   **Implementation:** Writes the actual code and implements features.
    *   **Workflow:** Checks assigned `issues`, writes code, and pushes deliverables.
    *   **Review Request:** MUST request review from **Codex** after completing a task.

### 3. Gemini (Frontend Designer)
*   **Role:** Frontend & UI/UX Designer
*   **Responsibility:**
    *   **Design:** Creating UI/UX optimized designs.
    *   **Frontend Impl:** Implementing frontend components that ensure high usability and aesthetics.
    *   **Focus:** Bridging the gap between backend logic and user experience.

---

## 🔄 Development Process

1.  **Issue Creation:** Codex identifies requirements and creates Git issues.
2.  **Development:** Claude-code (or Gemini for UI) picks up the issue and implements the solution.
3.  **Code Push:** Developer pushes code to the repository.
4.  **Review:** Codex reviews the changes.
    *   *Pass:* Issue closed.
    *   *Fail:* Codex creates a new issue with feedback.
