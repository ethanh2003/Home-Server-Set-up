# Gemini Docker Management

This file provides instructions for managing this Docker setup with Git and a prompt to use with Gemini for assistance.

## Git Workflow

This project is under Git version control. Here's how to manage your changes:

1.  **Check for changes**: To see which files have been modified, run:
    ```bash
    git status
    ```

2.  **Stage changes**: To add your changes to the next commit, use:
    ```bash
    git add .
    ```
    If you want to add a specific file that is ignored by `.gitignore` (like a config file), you can force it with:
    ```bash
    git add -f path/to/your/file
    ```

3.  **Commit changes**: To save your changes to the repository's history, run:
    ```bash
    git commit -m "A descriptive message about your changes"
    ```
    Commit your changes after you've made a logical update to your setup, like adding a new service or changing a configuration.

4.  **Push to remote**: To back up your changes to a remote repository (like GitHub), run:
    ```bash
    git push
    ```

## Docker Stack Management

You can start and stop all your services at once using these scripts:

*   **Start all services**:
    ```bash
    ./up.sh
    ```
*   **Stop all services**:
    ```bash
    ./down.sh
    ```

## Gemini Prompt Template

Here is a prompt template you can use to ask me for help with this setup. This will give me the context I need to help you efficiently.

---

### **Gemini, my expert Docker and Git assistant, I need your help with my server setup.**

**My Goal:**
[**<- YOUR GOAL HERE. For example: "I want to add a new service called 'organizr' to my setup and include it in the 'arr-stack'."**]

**Context:**
My Docker setup is located in `/home/ethan/docker`.
The main `docker-compose.yml` has been split into the following stack files:
- `arr-stack.yml`
- `jellyfin-stack.yml`
- `homeassistant-stack.yml`
- `actualbudget-stack.yml`
- `immich-stack.yml`

I have `up.sh` and `down.sh` scripts to manage these stacks.

The entire setup is under Git version control. The `.gitignore` file is configured to exclude secrets, databases, and logs, but I may want to add specific configuration files to version control.

**Your Task:**
1.  Understand my goal and the context provided.
2.  Before making any changes, tell me your plan.
3.  Use the available tools to inspect the files and environment to ensure your plan is sound.
4.  Execute the plan. If you are editing files, explain the changes you are making.
5.  After you are done, remind me to commit the changes to Git and provide the necessary commands.

---
