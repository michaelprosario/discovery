# How to Obtain FIREBASE_SERVICE_ACCOUNT_JSON

This guide explains how to generate a Firebase Service Account private key JSON file and configure it for your application.

## Steps to Generate the Service Account Key

1.  **Go to the Firebase Console**:
    Navigate to [https://console.firebase.google.com/](https://console.firebase.google.com/) and log in with your Google account.

2.  **Select Your Project**:
    Click on the Firebase project you want to use.

3.  **Open Project Settings**:
    Click the **Gear icon** (⚙️) next to "Project Overview" in the left sidebar and select **Project settings**.

4.  **Navigate to Service Accounts**:
    Click on the **Service accounts** tab in the top navigation bar.

5.  **Generate New Private Key**:
    *   Ensure "Firebase Admin SDK" is selected.
    *   Scroll down to the bottom of the page.
    *   Click the **Generate new private key** button.

6.  **Confirm Generation**:
    A warning dialog will appear. Click **Generate key** to confirm.

7.  **Download the JSON File**:
    The JSON file containing your service account credentials will automatically download to your computer. Keep this file secure!

## Configuring the Environment Variable

The `FIREBASE_SERVICE_ACCOUNT_JSON` environment variable expects the content of this JSON file.

1.  **Open the downloaded JSON file** in a text editor.
2.  **Copy the entire content**.
3.  **Format for `.env`**:
    *   The content must be a single line string if you are pasting it directly into a `.env` file, or you can wrap it in single quotes `'`.
    *   **Example**:
        ```dotenv
        FIREBASE_SERVICE_ACCOUNT_JSON='{"type": "service_account", "project_id": "your-project-id", ...}'
        ```

> **Note:** Ensure you do not commit your actual service account keys to version control. Add `.env` to your `.gitignore` file.
